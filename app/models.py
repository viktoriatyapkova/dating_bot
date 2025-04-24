from pydantic import BaseModel

class UserProfile(BaseModel):
    user_id: int
    name: str
    age: int
    gender: str
    about: str
    city: str
    photo_file_id: str
