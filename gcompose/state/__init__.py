from gcompose.application import Application
from gcompose.state.projects import ProjectsState
from gcompose.state.images import ImagesState


class StatefullApplication(Application):
    def __init__(self):
        super(StatefullApplication, self).__init__()
        self.projects = ProjectsState(self)
        self.images = ImagesState(self)
