from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def parse_cv():
    return {"message": "CV parsing endpoint"}
