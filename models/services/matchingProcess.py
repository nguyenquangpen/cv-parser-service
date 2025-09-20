import os
import logging
import re
import numpy as np
from numpy.linalg import norm 

from gensim.models.doc2vec import Doc2Vec
import psycopg2
from psycopg2 import sql
import asyncio
from config import settings

logger = logging.getLogger(__name__)

_doc2vec_model: Doc2Vec | None = None

def load_doc2vec_model() -> Doc2Vec:
    global _doc2vec_model
    if _doc2vec_model is None:
        doc2vecModel = settings.MODEL_PATH + "/cv_job_maching.model"
        logger.info("Loading Doc2Vec model from %s ...", doc2vecModel)
        try:
            if not os.path.exists(doc2vecModel):
                raise FileNotFoundError(f"Doc2Vec model file not found at {doc2vecModel}")
            _doc2vec_model = Doc2Vec.load(doc2vecModel)
            logger.info("Doc2Vec model loaded.")
        except Exception as e:
            logger.exception("Error loading Doc2Vec model: %s", e)
            raise
    return _doc2vec_model

def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub('[^a-z]', ' ', text)
    text = re.sub(r'\d+', '', text)
    text = ' '.join(text.split())
    return text

def _get_db_connection():
    return psycopg2.connect(**settings.DB_CONFIG)

def _fetch_fileContent_from_db_sync(item_id: str | int, table_name: str) -> str:
    conn = None
    try:
        conn = _get_db_connection()
        with conn.cursor() as cur:
            query = sql.SQL("SELECT file_content FROM {} WHERE id = %s").format(
                sql.Identifier(table_name)
            )
            cur.execute(query, (item_id, ))
            row = cur.fetchone()

        if not row or row[0] is None:
            logger.warning(f"No content found for {table_name}(id={item_id}) or content is NULL.")
            return ""
        content = row[0]
        
        if isinstance(content, (bytes, bytearray)):
            try:
                return content.decode("utf-8", errors="ignore")
            except Exception:
                return ""
        return str(content)

    except psycopg2.Error as db_err:
        logger.exception(f"DB error when fetching {table_name}(id={item_id}): {db_err}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error when fetching {table_name}(id={item_id}): {e}")
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as close_err:
                logger.warning(f"Error closing DB connection for {table_name}(id={item_id}): {close_err}")
                pass

async def get_preprocessed_fileContent_from_db(item_id: str | int, table_name: str) -> str:
    raw_content = await asyncio.to_thread(lambda: _fetch_fileContent_from_db_sync(item_id, table_name))
    return preprocess_text(raw_content)


async def calculate_similarity(resume_text: str, job_description: str) -> float:
    if not resume_text or not job_description:
        return 0.0
    
    model = load_doc2vec_model()

    v1 = model.infer_vector(resume_text.split())
    v2 = model.infer_vector(job_description.split())

    dn1 = norm(v1)
    dn2 = norm(v2)
    if dn1 == 0.0 or dn2 == 0.0:
        return 0.0

    sim = 100.0 * float(np.dot(v1, v2)) / float(dn1 * dn2)
    return round(sim, 2)

async def process_caculate(
    resume_id: str,
    job_description_id: str,
    resume_table_name: str,
    jd_table_name: str,
) -> dict:
    try:
        resume_pre = await get_preprocessed_fileContent_from_db(resume_id, resume_table_name)
        jd_pre = await get_preprocessed_fileContent_from_db(job_description_id, jd_table_name)

        if not resume_pre or not jd_pre:
            return ValueError("Empty content after preprocessing")
        
        score = await calculate_similarity(resume_pre, jd_pre)

        return {
            "resume_id": resume_id,
            "job_description_id": job_description_id,
            "score": score,
            "status": "completed",
            "message": "successful",
        }
    except Exception as e:
        logger.exception(
            "Processing failed",
            extra={"resume_id": resume_id, "job_description_id": job_description_id},
        )
        return {
            "resume_id": resume_id,
            "job_description_id": job_description_id,
            "score": 0.0,
            "status": "failed",
            "message": str(e),
        }

