from fastapi import FastAPI
from models.api import routes_cv

app = FastAPI(title="CV Parser Service")

app.include_router(routes_cv.router, prefix="/cv", tags=["CV"])