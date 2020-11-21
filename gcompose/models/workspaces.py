from enum import Enum
from pydantic import BaseModel
from gcompose.models.projects import Project


class WorkspaceStatusEnum(str, Enum):
    running = 'running'
    down = 'stopped'


class Workspace(BaseModel):
    project: Project
    status: WorkspaceStatusEnum = WorkspaceStatusEnum.stopped
