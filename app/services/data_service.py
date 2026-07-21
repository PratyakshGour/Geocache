from app.repositories.data_repository import DataRepository

class DataService:

    def __init__(self, repository: DataRepository):

        self.repository = repository


    def get_data(self, data_id: int):
        
        data = self.repository.get_by_id(data_id)
        if data is None:
            raise ValueError("Data not found")

        return {
           "data_id": data_id,
           "data": data
        }
    
    def create_data(self, title: str, content: str):
        return self.repository.create(
            title=title,
            content=content
    )