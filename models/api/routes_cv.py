from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Annotated
import logging

from models.api.schemas import CVtextInput, CVtextOutput, CVscoreInput, CVscoreOutput

from models.services.cv_parser import CVParserService
from models.api.dependencies import get_cv_parser_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["cv Processing"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def parse_cv():
    return {"message": "CV parsing endpoint"}
    