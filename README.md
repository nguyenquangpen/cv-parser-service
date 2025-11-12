cv_ai_server/
├── api/
│   ├── __init__.py
│   ├── dependencies.py # Quản lý session database
│   ├── routes.py       # Lễ tân: Nhận request và gọi service
│   └── schemas.py      # Hợp đồng: Định nghĩa cấu trúc dữ liệu
├── database/
│   ├── __init__.py
│   ├── database.py     # Thiết lập kết nối database
│   └── models.py       # Kho: Định nghĩa các bảng dữ liệu
├── services/
│   ├── __init__.py
│   └── storage_service.py # Phòng làm việc: Chứa logic nghiệp vụ
├── main.py             # Cửa chính của ứng dụng
└── requirements.txt    # Danh sách các thư viện cần thiết