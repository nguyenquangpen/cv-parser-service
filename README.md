# cv-parser-service

## structure
cv_ai_server/
├── models/
│   ├── output/
│   │   └── result.pkl
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py # Để xử lý các dependencies (ví dụ: tải model, db session)
│   │   ├── routes.py       # <--- Chỉ chứa định nghĩa các API endpoints
│   │   └── schemas.py      # Chứa các Pydantic models (Input/Output)
│   └── services/           # <--- Thư mục mới cho Business Logic / Helper Functions
│       ├── __init__.py
│       └── cv_parser.py    # Chứa logic trích xuất text, gọi model
├── main.py
├── requirements.txt
└── Dockerfile