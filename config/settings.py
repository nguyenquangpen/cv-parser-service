import os
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = "models/output"

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "host": os.environ.get("DB_HOST"),
    "port": int(os.environ.get("DB_PORT")),
}

RESUME_TABLE_NAME = "overview_resume"
JD_TABLE_NAME = "overview_jobdescription"

# matching Processing settings
MATCH_CONCURRENCY = 10        # số task chạy song song
MATCH_TIMEOUT_SEC = 30.0      # timeout tổng cho toàn bộ quá trình (giây)
MATCH_MAX_PAIRS = 2000        # số cặp Resume–JD tối đa xử lý trong 1 lần
PER_TASK_TIMEOUT = 30.0       # timeout cho mỗi task con (giây)

