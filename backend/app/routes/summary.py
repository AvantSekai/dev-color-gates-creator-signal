from fastapi import APIRouter

from app.data import compute_promising_pool, get_dataset_meta

router = APIRouter()


@router.get("/api/summary")
def get_summary() -> dict:
    return {
        "meta": get_dataset_meta(),
        "creators": compute_promising_pool(),
    }
