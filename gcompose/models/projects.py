from pathlib import Path
from pydantic import BaseModel


class Project(BaseModel):
    name: str
    path: Path
    use_sudo: bool = True
    selected: bool = False
