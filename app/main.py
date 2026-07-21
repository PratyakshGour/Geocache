from fastapi import FastAPI, HTTPException
from app.schemas.data import DataCreate
from app.repositories.data_repository import DataRepository
from app.services.data_service import DataService

app = FastAPI()
data_repository = DataRepository()
data_service = DataService(data_repository)



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

    try:

        return data_service.get_data(data_id)

    except ValueError:

        raise HTTPException(
            status_code=404,
            detail="Data not found"
        )

@app.post("/data")
def create_data(data: DataCreate):

    return data_service.create_data(
        title=data.title,
        content=data.content
    )