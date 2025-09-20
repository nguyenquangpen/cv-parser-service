from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Tuple, Set, Dict, Any, Union
import asyncio
import logging
import time

from models.schemas.processing_payload import (
    ProcessingPayload,
    MatchingResult,
    OverallProcessingResponse
)
from models.services import matching # Đảm bảo đã import service matching

# FastAPI tự cấu hình logging cơ bản, nhưng bạn có thể custom.
# logger = logging.getLogger(__name__)
# Để sử dụng logger của FastAPI, bạn có thể truy cập logger gốc hoặc cấu hình riêng.
# ví dụ: from logging import getLogger; logger = getLogger("uvicorn.error")

# Sử dụng logger cơ bản nếu chưa cấu hình chi tiết, hoặc dùng logger của Uvicorn
logger = logging.getLogger("uvicorn.access") # Hoặc "uvicorn.error" nếu muốn log lỗi chi tiết hơn


router = APIRouter(
    tags=["CV-JD Matching"],
    responses={404: {"description": "Not found"}},
)

def _unique_pairs(resume_ids: List[str], jd_ids: List[str]) -> List[Tuple[str, str]]: # Thay int thành str
    # Sử dụng set để loại bỏ các ID trùng lặp
    r_set: Set[str] = set(resume_ids or [])
    j_set: Set[str] = set(jd_ids or [])
    
    # Tạo các cặp duy nhất và sắp xếp chúng (tùy chọn nhưng tốt cho tính nhất quán)
    # Lưu ý: Sắp xếp các chuỗi ID
    return [(r, j) for j in sorted(list(j_set)) for r in sorted(list(r_set))]

async def _run_one(
    sem: asyncio.Semaphore,
    resume_id: str, # Thay int thành str
    jd_id: str,     # Thay int thành str
    settings: Settings,
    per_task_timeout: float,
) -> MatchingResult: # Hàm trả về MatchingResult hoặc một dict báo lỗi
    async with sem:
        try:
            # Hàm process_matching trong models.services.matching cần nhận str cho ID
            coro = matching.process_matching(
                resume_id=resume_id,
                job_description_id=jd_id,
                resume_table_name=settings.resume_table_name,
                jd_table_name=settings.jd_table_name,
            )
            # await asyncio.wait_for sẽ ném TimeoutError nếu timeout
            result_dict = await asyncio.wait_for(coro, timeout=per_task_timeout)
            
            # Đảm bảo kết quả là một MatchingResult hợp lệ
            return MatchingResult(**result_dict) 
            
        except asyncio.TimeoutError:
            logger.warning(
                "Matching timeout",
                extra={"resume_id": resume_id, "jd_id": jd_id, "timeout_sec": per_task_timeout},
            )
            return MatchingResult(
                resume_id=resume_id,
                job_description_id=jd_id,
                score=0.0,
                status="failed",
                message=f"Processing timed out after {per_task_timeout} seconds."
            )
        except Exception as e:
            logger.exception(
                "Matching failed",
                extra={"resume_id": resume_id, "job_description_id": jd_id},
            )
            return MatchingResult(
                resume_id=resume_id,
                job_description_id=jd_id,
                score=0.0,
                status="failed",
                message=f"Processing failed: {str(e)}"
            )

@router.post(
    "/process/",
    response_model=OverallProcessingResponse,
    status_code=status.HTTP_200_OK,
)
async def process_selection_overall(
    payload: ProcessingPayload,
    concurrency_limit: int = Query(None, ge=1, le=256, description="Số task chạy song song"),
    timeout_sec: float = Query(None, gt=0, le=600, description="Timeout mỗi cặp (giây)"),
    settings: Settings = Depends(get_settings),
):
    t0 = time.perf_counter()

    if not payload.job_description_ids or not payload.resume_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần cung cấp cả danh sách resume_ids và job_description_ids.",
        )

    pairs = _unique_pairs(payload.resume_ids, payload.job_description_ids)
    total_pairs = len(pairs)
    if total_pairs == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không tạo được cặp nào từ IDs (có thể do trùng/empty).",
        )
    if total_pairs > settings.max_pairs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Số cặp ({total_pairs}) vượt giới hạn {settings.max_pairs}. Vui lòng chọn ít lại.",
        )

    concurrency = concurrency_limit or settings.default_concurrency
    per_task_timeout = timeout_sec or settings.default_timeout_sec
    sem = asyncio.Semaphore(concurrency)

    logger.info(
        "Starting matching",
        extra={
            "resumes": len(set(payload.resume_ids)),
            "job_descriptions": len(set(payload.job_description_ids)),
            "pairs": total_pairs,
            "concurrency": concurrency,
            "timeout_sec": per_task_timeout,
            "resume_table": settings.resume_table_name,
            "jd_table": settings.jd_table_name,
        },
    )

    # Chạy các tác vụ và thu thập kết quả (đã là MatchingResult do _run_one trả về)
    tasks = [
        _run_one(sem, r_id, j_id, settings, per_task_timeout)
        for (r_id, j_id) in pairs
    ]
    all_results: List[MatchingResult] = await asyncio.gather(*tasks, return_exceptions=False)
    # return_exceptions=False vì _run_one đã xử lý exception và trả về MatchingResult báo lỗi

    # Chỉ cần lọc các kết quả "failed" để đếm
    failed_count = sum(1 for res in all_results if res.status == "failed")
    ok_results_list = [res for res in all_results if res.status != "failed"]


    dt = time.perf_counter() - t0
    msg = f"Processed {total_pairs} pairs in {dt:.2f}s: successful={len(ok_results_list)}, failed={failed_count}."

    logger.info("Matching finished", extra={"summary": msg})

    return OverallProcessingResponse(
        message=msg,
        matching_results=ok_results_list,
        status_code=status.HTTP_200_OK,
    )