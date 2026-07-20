class DataRepository:

    def __init__(self):

        self.data_store = {
            1: {
                "title": "India Data",
                "content": "This data belongs to the India region"
            },
            2: {
                "title": "Singapore Data",
                "content": "This data belongs to the Singapore region"
            },
            3: {
                "title": "Europe Data",
                "content": "This data belongs to the Europe region"
            }
        }

        self.next_id = 4

    def get_by_id(self, data_id: int):

        return self.data_store.get(data_id)
    

    def create(self, title: str, content: str):
        
        data_id = self.next_id

        self.data_store[data_id] = {
        "title": title,
        "content": content
    }

        self.next_id += 1

        return {
        "data_id": data_id,
        "data": self.data_store[data_id]
    }