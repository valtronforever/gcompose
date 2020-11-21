from gi.repository import GObject
from typing import List, Optional
from pathlib import Path
import configparser
from gcompose.models.projects import Project


config_path = Path.home() / '.config' / 'gcompose' / 'projects.cfg'


def escape_project_name(name: str) -> str:
    return name.replace('[', '').replace(']', '').replace('#', '').replace(';', '')


def read_projects() -> List[Project]:
    conf = configparser.ConfigParser()
    conf.read(config_path)
    projects = []
    for section in conf.sections():
        projects.append(Project(
            name=section,
            path=conf[section]['path'],
            use_sudo=conf[section].getboolean('use_sudo', fallback=True),
            selected=conf[section].getboolean('selected', fallback=False),
        ))
    return projects


def write_projects(projects: List[Project]):
    conf = configparser.ConfigParser()
    for project in projects:
        conf[escape_project_name(project.name)] = {
            'path': project.path,
            'use_sudo': 'yes' if project.use_sudo else 'no',
            'selected': 'yes' if project.selected else 'no',
        }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.touch(exist_ok=True)
    with open(config_path, 'w+') as configfile:
        conf.write(configfile)


class ProjectsState(GObject.GObject):
    app = None

    projects: List[Project] = GObject.Property(type=object)
    config_read_error: bool = GObject.Property(type=bool, default=False)

    @GObject.Property(type=object)
    def selected_project(self) -> Optional[Project]:
        return next(filter(lambda project: project.selected, self.projects), None)

    @GObject.Property(type=bool, default=True)
    def is_empty(self) -> bool:
        return len(self.projects) == 0

    def has(self, name: str) -> bool:
        return bool(next(filter(lambda project: project.name == name, self.projects), None))

    @GObject.Signal(arg_types=(object,))
    def add_project(self, project: Project):
        self.projects = self.projects + [project]
        write_projects(self.projects)

    @GObject.Signal
    def remove_project(self, project_name: str):
        self.projects = [
            p for p in self.projects if p.name != project_name
        ]
        write_projects(self.projects)

    @GObject.Signal
    def read_projects(self):
        try:
            self.projects = read_projects()
            self.config_read_error = False
        except Exception:
            self.config_read_error = True

    @GObject.Signal
    def select_project(self, name: str):
        self.projects = [Project(
            selected=True if project.name == name else False,
            **project.dict(exclude={'selected'})
        ) for project in self.projects]

    @GObject.Signal
    def clear_project_selection(self):
        self.projects = [Project(
            **project.dict(exclude={'selected'})
        ) for project in self.projects]

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.read_projects()
