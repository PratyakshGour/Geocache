from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/data/{data_id}")
def get_data(data_id: int):
    # existing code
    ...


@router.post("/data")
def create_data(data: DataCreate):
    # existing code
    ...