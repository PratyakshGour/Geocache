from fastapi import FastAPI, HTTPException
from app.schemas.data import DataCreate
from app.repositories.data_repository import DataRepository


app = FastAPI()
data_repository = DataRepository()



@app.get("/")
def home():
    return {
        
    "project": "GeoCache",
    "status": "running",
    "region": "local",
    "server": "local-server"
}



@app.get("/data/{data_id}")
def get_data(data_id: int):

    data = data_repository.get_by_id(data_id)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Data not found"
        )

    return {
        "data_id": data_id,
        "data": data
    }


@app.post("/data")
def create_data(data: DataCreate):

    return data_repository.create(
        title=data.title,
        content=data.content
    )