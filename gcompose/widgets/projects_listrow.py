from pathlib import Path
from gi.repository import Gtk
from gcompose.models.projects import Project


@Gtk.Template.from_file(str(Path(__file__).parents[0] / 'projects_listrow.glade'))
class ProjectsListRow(Gtk.Box):
    __gtype_name__ = 'ProjectsListRow'

    project: Project

    project_name = Gtk.Template.Child()
    project_path = Gtk.Template.Child()
    run_image = Gtk.Template.Child()

    def __init__(self, project: Project, **kwargs):
        super().__init__(**kwargs)
        self.project = project
        self.project_name.set_text(project.name)
        self.project_path.set_text(str(project.path.parent))

    def get_project_name(self) -> str:
        return self.project.name
