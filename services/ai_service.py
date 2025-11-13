import spacy
import PyPDF2
import docx
import numpy as np
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import re
import os
from numpy.linalg import norm
from dotenv import load_dotenv

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import logging

logger = logging.getLogger(__name__)

load_dotenv()

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

class AIService:
    _instance = None # Singleton pattern để đảm bảo chỉ có một instance LLM
    _gemini_model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            cls._instance._initialize_llm()
        return cls._instance

    def _initialize_llm(self):
        """Khởi tạo và cấu hình mô hình Gemini."""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables.")
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        genai.configure(api_key=google_api_key)
        try:
            self._gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Google Gemini model 'gemini-2.5-flash' initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini model: {e}", exc_info=True)
            raise RuntimeError(f"Could not initialize Google Gemini model: {e}")

    def generate_job_description(self, prompt_content: str) -> str:
        if not self._gemini_model:
            raise RuntimeError("Gemini model is not initialized.")

        llm_prompt = f"""
        Bạn là một chuyên gia tuyển dụng tài năng và có kinh nghiệm. Nhiệm vụ của bạn là tạo một mô tả công việc (Job Description)
        chuyên nghiệp, chi tiết và hấp dẫn.

        **Quy tắc và Hướng dẫn:**
        1.  **Phân tích và Mở rộng:** Đọc kỹ "Nội dung ban đầu" do người dùng cung cấp. Nội dung này có thể là các từ khóa, gạch đầu dòng, hoặc một đoạn văn ngắn. Nhiệm vụ của bạn là mở rộng những thông tin này thành một JD đầy đủ và mạch lạc.
        2.  **Chỉ tạo nội dung liên quan:** CHỈ tạo ra các phần thông tin TRỰC TIẾP liên quan đến mô tả công việc. Không bao gồm các thông tin cá nhân, ý kiến chủ quan, hay dữ liệu không liên quan đến yêu cầu tuyển dụng.
        3.  **Định dạng Text Thuần (Plain Text):** Tạo JD dưới dạng văn bản thuần túy. KHÔNG sử dụng bất kỳ thẻ HTML, Markdown (như ##, **, *) hay định dạng đặc biệt nào. Chỉ sử dụng xuống dòng để phân tách các đoạn và gạch đầu dòng bằng dấu gạch ngang (-) hoặc dấu hoa thị (*) cho các danh sách.
        4.  **Các phần bắt buộc:** JD phải bao gồm các phần sau, ngay cả khi "Nội dung ban đầu" không cung cấp đầy đủ, hãy suy luận một cách hợp lý:
            *   **Tên vị trí (Job Title):** Rõ ràng, chuyên nghiệp.
            *   **Tóm tắt công việc (Job Summary):** Một đoạn văn ngắn gọn mô tả vai trò tổng thể và đóng góp.
            *   **Trách nhiệm chính (Key Responsibilities):** Danh sách các nhiệm vụ cụ thể.
            *   **Yêu cầu (Qualifications):** Các kỹ năng, kinh nghiệm, bằng cấp bắt buộc.
            *   **Điểm cộng (Nice-to-Have/Bonus Points):** Các kỹ năng, kinh nghiệm không bắt buộc nhưng là lợi thế.
        5.  **Ngôn ngữ:** Tạo JD bằng tiếng Việt.
        6.  **Không thêm ghi chú:** Không thêm bất kỳ ghi chú nào của bạn về cách bạn tạo JD hoặc hướng dẫn này vào đầu ra cuối cùng.

        ---

        **Nội dung ban đầu:**
        {prompt_content}

        ---

        **Đầu ra JD định dạng Text Thuần:**
        """

        logger.info(f"Sending prompt to Gemini: {llm_prompt[:200]}...")

        try:
            response = self._gemini_model.generate_content(
                llm_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=1.0,
                    top_k=40,
                    candidate_count=1,
                    max_output_tokens=2048, 
                ),
                safety_settings=[
                    {
                        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                ],
                request_options={"timeout": 30.0}
            )
            if not response.candidates:
                logger.warning("Gemini returned no candidates for the prompt.")
                return ""

            generated_text = response.text
            if not generated_text.strip():
                logger.warning("Gemini returned empty text content.")
                return ""

            logger.info(f"Gemini generated content: {generated_text[:200]}...")
            return generated_text

        except genai.types.BlockedPromptException as bpe:
            logger.warning(f"Prompt blocked by Gemini safety settings: {bpe}")
            raise ValueError(f"Prompt bị chặn bởi cài đặt an toàn của Gemini: {bpe.response.prompt_feedback}")
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            raise RuntimeError(f"Lỗi khi gọi API Gemini: {e}")
        
ai_service_instance  = AIService()