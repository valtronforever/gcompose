from pathlib import Path
from gi.repository import Gtk, GObject
from gcompose import AppMixin
from gcompose.models.projects import Project
from gcompose.models.images import Image
import shutil


@Gtk.Template.from_file(str(Path(__file__).parents[0] / 'image_tab.glade'))
class ImageTab(Gtk.Box, AppMixin):
    __gtype_name__ = 'ImageTab'

    project: Project
    image: Image

    shell_spawned = GObject.Property(type=bool, default=False)

    shell_button = Gtk.Template.Child()
    logsterminal = Gtk.Template.Child()
    shellterminal = Gtk.Template.Child()

    def __init__(self, project: Project, image: Image, **kwargs):
        super().__init__(**kwargs)
        self.project = project
        self.image = image
        self.connect('parent-set', self.on_parent_set)

    def get_container(self) -> str:
        return self.image.container

    def on_parent_set(self, *args, **kwargs):
        logs_command = f"{shutil.which('docker')} logs -f {self.image.container}"
        self.app.launch_in_terminal(
            terminal=self.logsterminal,
            command=logs_command,
            working_dir=self.project.path.parent,
            use_sudo=self.project.use_sudo,
        )

    @Gtk.Template.Callback(name='on_shell_button_toggled')
    def on_shell_button_toggled(self, *args, **kwargs):
        if self.shell_button.get_active():
            if not self.shell_spawned:
                shell_command = f"{shutil.which('docker')} exec -it {self.image.container} /bin/sh"
                self.app.launch_in_terminal(
                    terminal=self.shellterminal,
                    command=shell_command,
                    working_dir=self.project.path.parent,
                    use_sudo=self.project.use_sudo,
                )
                self.shell_spawned = True
            self.shellterminal.set_visible(True)
        else:
            self.shellterminal.set_visible(False)
