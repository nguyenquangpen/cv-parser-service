from typing import Annotated
from fastapi import Depends
import logging

logger = logging.getLogger(__name__)



# dependencies.py = nơi định nghĩa các dependency functions dùng chung cho nhiều API.
# Dùng để:
# Kết nối DB (get_db).
# Xác thực (get_current_user).
# Load config.
# Logging, rate limiting,…
# Giúp code modular, DRY, dễ test. 