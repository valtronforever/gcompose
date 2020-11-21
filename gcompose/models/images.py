from pydantic import BaseModel


class Image(BaseModel):
    project_name: str
    container: str
    repository: str
    tag: str
    image_id: str
    size: str
