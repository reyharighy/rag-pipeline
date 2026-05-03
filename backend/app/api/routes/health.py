from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def check_health():
    return {"message": "Hello from backend!"}
