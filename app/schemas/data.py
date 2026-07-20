from pydantic import BaseModel

class DataCreate(BaseModel):
    title: str
    content: str