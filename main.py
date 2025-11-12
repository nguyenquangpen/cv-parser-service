from fastapi import FastAPI
from api import routes
from database import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="CV Parser AI Server")

app.include_router(routes.router, prefix="/api")

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the CV Parser AI Server!"}