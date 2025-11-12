import spacy
import PyPDF2
import docx
import numpy as np
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import re
from numpy.linalg import norm

try:
    SKILL_EXTRACTION_MODEL = spacy.load('NER_HardSoftSkill_Extract_model')
    CANDIDATE_INFO_MODEL = spacy.load('NER_Candidate_IE_model')
    MATCH_MODEL = Doc2Vec.load('cv_job_maching.model')
except Exception as e:
    print(f"Error loading models: {e}")
    SKILL_EXTRACTION_MODEL = None
    CANDIDATE_INFO_MODEL = None

def extract_text_from_content(content: bytes, filename: str) -> str:
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif filename.lower().endswith('.docx'):
            document = docx.Document(io.BytesIO(content))
            for para in document.paragraphs:
                text += para.text + '\n'
        elif filename.lower().endswith('.txt'):
            text = content.decode('utf-8')
    except Exception as e:
        return f"error when extract info from {filename}: {e}"
    return text

def clean_text(text):
    cleaned = re.sub(r'[\n\*\-\|/]+', ' ', text)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = cleaned.strip()
    return cleaned

def extract_skills_from_text(text: str):
    if not SKILL_EXTRACTION_MODEL:
        raise ValueError("Skill extraction model is not loaded.")
    
    doc = SKILL_EXTRACTION_MODEL(text)

    skills = set()

    for ent in doc.ents:
        if ent.label_.lower() in ['hard_skills', 'soft_skills']:
            skills.add((ent.text, ent.label_))

    unique_skills = sorted(list(skills))
    return {"skills": unique_skills}

def extract_candidate_info(text: str):
    if not CANDIDATE_INFO_MODEL:
        raise ValueError("Candidate info extraction model is not loaded.")
    
    doc = CANDIDATE_INFO_MODEL(text)

    info = {
        "name": None,
        "designations": [],
        "degrees": [],
        # thêm trường khác nếu model extract được
    }

    for ent in doc.ents:
        label = ent.label_.lower()
        value = ent.text.strip().replace('\n', ' ')

        if "name" in label:
            info["name"] = value
        elif "designation" in label:
            info["designations"].append(value)
        elif "degree" in label:
            info["degrees"].append(value)

    info["designations"] = sorted(list(set(info["designations"])))
    info["degrees"] = sorted(list(set(info["degrees"])))

    return info

def caculate_match_score(jd, resume):
    input_JD = clean_text(jd)
    input_CV = clean_text(resume)
    v1 = MATCH_MODEL.infer_vector(input_CV.split())
    v2 = MATCH_MODEL.infer_vector(input_JD.split())
    similarity = (np.dot(np.array(v1), np.array(v2))) / (norm(np.array(v1)) * norm(np.array(v2)))*100
    return round(similarity, 2)

    
