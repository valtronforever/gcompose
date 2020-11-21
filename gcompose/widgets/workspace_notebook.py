from pathlib import Path
from enum import Enum
import shutil
import logging
from gi.repository import GObject, Gtk, GtkSource, Vte, Gio
from gcompose import StateMixin
from gcompose.models.projects import Project
from gcompose.widgets.yamlsourceview import YamlSourceView
from gcompose.widgets.image_tab import ImageTab


class SpawnedCommandEnum(str, Enum):
    up = 'up'
    down = 'down'


@Gtk.Template.from_file(str(Path(__file__).parents[0] / 'workspace_notebook.glade'))
class WorkspaceNotebook(Gtk.Notebook, StateMixin):
    __gtype_name__ = 'WorkspaceNotebook'

    project_name: str = GObject.Property(type=str)
    project_path: Path = GObject.Property(type=object)
    project_use_sudo: bool = GObject.Property(type=bool, default=True)
    child_process_running: bool = GObject.Property(type=bool, default=False)
    spawned_command: str = GObject.Property(type=str)

    filename_label: Gtk.Label = Gtk.Template.Child()
    sourceview: YamlSourceView = Gtk.Template.Child()
    source_buffer: GtkSource.Buffer
    lanchterminal: Vte.Terminal = Gtk.Template.Child()

    up_button: Gtk.Button = Gtk.Template.Child()
    down_button: Gtk.Button = Gtk.Template.Child()
    save_button: Gtk.Button = Gtk.Template.Child()
    undo_button: Gtk.Button = Gtk.Template.Child()
    redo_button: Gtk.Button = Gtk.Template.Child()
    refresh_images_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, name: str, path: Path, use_sudo: bool, **kwargs):
        super().__init__(**kwargs)
        self.project_name = name
        self.project_path = path
        self.project_use_sudo = use_sudo

        self.source_buffer = self.sourceview.get_buffer()
        self.source_buffer.connect('notify::can-undo', self.render_edit_buttons)
        self.source_buffer.connect('notify::can-redo', self.render_edit_buttons)
        self.connect('notify::child-process-running', self.render_run_buttons)
        self.source_buffer.connect('modified-changed', self.render_save)
        self.lanchterminal.connect('child-exited', self.render_child_exit)
        self.connect('parent-set', self.on_parent_set)

        with open(self.project_path) as f:
            self.source_buffer.begin_not_undoable_action()
            self.source_buffer.set_text(f.read())
            self.source_buffer.set_modified(False)
            self.source_buffer.end_not_undoable_action()

        self.sourceview.connect('save_key_pressed', self.on_save_button_clicked)

        self.render_edit_buttons()
        self.render_run_buttons()
        self.render_save()

    def on_parent_set(self, *args, **kwargs):
        self.app.images.connect('update_project_images', self.render_images)

    def render_edit_buttons(self, *args, **kwargs):
        self.undo_button.set_sensitive(
            self.source_buffer.can_undo()
        )
        self.redo_button.set_sensitive(
            self.source_buffer.can_redo()
        )

    def render_save(self, *args, **kwargs):
        self.save_button.set_sensitive(
            self.source_buffer.get_modified()
        )
        if self.source_buffer.get_modified():
            self.filename_label.set_text('*' + self.project_path.name)
        else:
            self.filename_label.set_text(self.project_path.name)

    def render_run_buttons(self, *args, **kwargs):
        self.up_button.set_sensitive(not self.child_process_running)
        self.down_button.set_sensitive(not self.child_process_running)

    def render_child_exit(self, *args, **kwargs):
        self.lanchterminal.feed("--- Done ---\r\n".encode('utf-8'))
        self.child_process_running = False
        if self.spawned_command == SpawnedCommandEnum.up:
            self.on_up_complete()
        elif self.spawned_command == SpawnedCommandEnum.down:
            self.on_down_complete()
        self.spawned_command = None

    def render_images(self, state, project, images):
        if project.name != self.project_name:
            return

        current_images = []
        page_nums_to_remove = []
        for page_num in range(1, self.get_n_pages()):
            page: ImageTab = self.get_nth_page(page_num)
            container = page.get_container()
            if container not in [image.container for image in images]:
                page_nums_to_remove.append(page_num)
            else:
                current_images.append(container)

        for page_num in page_nums_to_remove:
            self.remove_page(page_num)

        for image in images:
            if image.container not in current_images:
                self.append_page(
                    ImageTab(Project(
                        name=self.project_name,
                        path=self.project_path,
                        use_sudo=self.project_use_sudo,
                    ), image),
                    Gtk.Label(label=image.container),
                )
        self.refresh_images_button.set_sensitive(True)

    def on_up_complete(self):
        logging.debug("Up complete")
        self.refresh_images_button.set_sensitive(False)
        self.dispatch("images.request_images_for_project", Project(
            name=self.project_name,
            path=self.project_path,
            use_sudo=self.project_use_sudo,
        ))

    def on_down_complete(self):
        logging.debug("Down complete")

    @Gtk.Template.Callback(name='on_undo_button_clicked')
    def on_undo_button_clicked(self, *args, **kwargs):
        self.source_buffer.undo()

    @Gtk.Template.Callback(name='on_redo_button_clicked')
    def on_redo_button_clicked(self, *args, **kwargs):
        self.source_buffer.redo()

    @Gtk.Template.Callback(name='on_save_button_clicked')
    def on_save_button_clicked(self, *args, **kwargs):
        with open(self.project_path, 'w') as f:
            self.source_buffer.begin_not_undoable_action()
            f.write(self.source_buffer.get_text(
                *self.source_buffer.get_bounds(),
                include_hidden_chars=True
            ))
            self.source_buffer.set_modified(False)
            self.source_buffer.end_not_undoable_action()

    @Gtk.Template.Callback(name='on_refresh_images_button_clicked')
    def on_refresh_images_button_clicked(self, *args, **kwargs):
        self.refresh_images_button.set_sensitive(False)
        self.dispatch("images.request_images_for_project", Project(
            name=self.project_name,
            path=self.project_path,
            use_sudo=self.project_use_sudo,
        ))

    @Gtk.Template.Callback(name='on_up_button_clicked')
    def on_up_button_clicked(self, *args, **kwargs):
        docker_compose_path = shutil.which('docker-compose')
        logging.debug(f'Docker-compose path: {docker_compose_path}')
        if not docker_compose_path:
            docker_compose_path = '/usr/local/bin/docker-compose'
            logging.debug(f'Docker-compose path to: {docker_compose_path}')

        up_command = f"{docker_compose_path} -f {str(self.project_path)} up -d"
        self.child_process_running = True
        self.spawned_command = SpawnedCommandEnum.up
        self.app.launch_in_terminal(
            terminal=self.lanchterminal,
            command=up_command,
            working_dir=self.project_path.parent,
            use_sudo=self.project_use_sudo,
        )

    @Gtk.Template.Callback(name='on_down_button_clicked')
    def on_down_button_clicked(self, *args, **kwargs):
        docker_compose_path = shutil.which('docker-compose')
        logging.debug(f'Docker-compose path: {docker_compose_path}')
        if not docker_compose_path:
            docker_compose_path = '/usr/local/bin/docker-compose'
            logging.debug(f'Docker-compose path to: {docker_compose_path}')

        down_command = f"{docker_compose_path} -f {str(self.project_path)} down --remove-orphans"
        self.child_process_running = True
        self.spawned_command = SpawnedCommandEnum.down
        self.app.launch_in_terminal(
            terminal=self.lanchterminal,
            command=down_command,
            working_dir=self.project_path.parent,
            use_sudo=self.project_use_sudo,
        )
