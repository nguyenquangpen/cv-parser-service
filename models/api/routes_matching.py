from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Tuple, Set, Dict, Any, Union
import asyncio
import logging
import time
from config import settings

from models.schemas.processing_payload import (
    ProcessingPayload,
    MatchingResult,
    OverallProcessingResponse
)

from models.services import matchingProcess

logger = logging.getLogger(__name__)

matching_router = APIRouter(
    tags=["CV-JD Matching"],
    responses={404: {"description": "Not found"}},
)
sem = asyncio.Semaphore(settings.MATCH_CONCURRENCY)

# this function ensures unique pairs of resume and job description IDs
async def _run_one(
    resume_id: str, 
    jd_id: str,
) -> MatchingResult:
    async with sem:
        try:
            coro = matchingProcess.process_caculate(
                resume_id=resume_id,
                job_description_id=jd_id,
                resume_table_name=settings.RESUME_TABLE_NAME,
                jd_table_name=settings.JD_TABLE_NAME,
            )

            result_dict = await asyncio.wait_for(coro, timeout=settings.PER_TASK_TIMEOUT)
            
            return MatchingResult(**result_dict)
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout processing resume_id={resume_id}, jd_id={jd_id} after {settings.PER_TASK_TIMEOUT} seconds"
            )
            return MatchingResult(
                resume_id=resume_id,
                job_description_id=jd_id,
                score=0.0,
                status="timeout",
                message=f"Processing timed out after {settings.PER_TASK_TIMEOUT} seconds",
            )
        except Exception as e:
            logger.exception(
                "Error processing",
                extra={"resume_id": resume_id, "job_description_id": jd_id},
            )
            return MatchingResult(
                resume_id=resume_id,
                job_description_id=jd_id,
                score=0.0,
                status="error",
                message=str(e),
            )

@matching_router.post("/process-with-ai")
async def caculate_matching(payload: ProcessingPayload) -> OverallProcessingResponse:
    start_time = time.time()

    resume_ids = payload.resume_ids
    job_ids = payload.job_ids

    if not resume_ids or not job_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both resume_ids and job_ids must be provided and non-empty."
        )
    
    single_jd_id = job_ids[0]
    
    if len(resume_ids) > settings.MATCH_MAX_PAIRS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many resumes to process with one JD. Max allowed is {settings.MATCH_MAX_PAIRS}."
        )

    tasks = [
        _run_one(r_id, single_jd_id) 
        for r_id in resume_ids
    ]

    all_results: List[MatchingResult] = await asyncio.gather(*tasks)

    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    processed_pairs_count = len(all_results)

    msg = f"Processed {processed_pairs_count} CV-JD pairs in {elapsed_time}s (1 JD vs {len(resume_ids)} CVs)."


    return OverallProcessingResponse(
        message=msg,
        matching_results=all_results,
        status_code=status.HTTP_200_OK,
    )