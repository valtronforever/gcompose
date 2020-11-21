from pathlib import Path
from typing import Dict
from gi.repository import Gtk
from gcompose.models.projects import Project
from gcompose import StateMixin
from gcompose.state.projects import ProjectsState
from gcompose.widgets.projects_listrow import ProjectsListRow
from gcompose.widgets.workspace_notebook import WorkspaceNotebook


def create_workspace(project: Project) -> WorkspaceNotebook:
    return WorkspaceNotebook(
        name=project.name,
        path=project.path,
        use_sudo=project.use_sudo,
    )


@Gtk.Template.from_file(str(Path(__file__).parents[0] / 'appwindow.glade'))
class AppWindow(Gtk.ApplicationWindow, StateMixin):
    __gtype_name__ = 'AppWindow'

    # sourceview = Gtk.Template.Child()
    # lanchterminal = Gtk.Template.Child()

    workspaces: Dict[str, WorkspaceNotebook] = {}

    projects_stack = Gtk.Template.Child()
    projects_list = Gtk.Template.Child()
    projects_empty_list = Gtk.Template.Child()
    projects_config_error = Gtk.Template.Child()

    new_project_popover = Gtk.Template.Child()
    new_project_name_entry = Gtk.Template.Child()
    new_project_path_entry = Gtk.Template.Child()
    new_project_sudo_switch = Gtk.Template.Child()
    new_project_popover_add_button = Gtk.Template.Child()

    create_project_popover = Gtk.Template.Child()
    create_project_name_entry = Gtk.Template.Child()
    create_project_path_entry = Gtk.Template.Child()
    create_project_sudo_switch = Gtk.Template.Child()
    create_project_popover_create_button = Gtk.Template.Child()

    workspace_stack = Gtk.Template.Child()
    no_selected_workspace_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mapProps({
            'projects.projects': (
                self.render_projects_stack,
                self.render_project_list,
                self.render_workspace_stack,
            ),
            'projects.config_read_error': self.render_projects_stack,
        })
        self.render_project_list(self.app.projects)
        self.render_projects_stack(self.app.projects)

    def render_project_list(self, state: ProjectsState, *args):
        exists = []
        for el in self.projects_list.get_children():
            name = el.get_child().get_project_name()
            if state.has(name):
                exists.append(name)
            else:
                self.projects_list.remove(el)
                self.workspace_stack.remove(
                    self.workspace_stack.get_child_by_name(name)
                )

        for project in state.projects:
            if project.name not in exists:
                self.workspace_stack.add_named(
                    create_workspace(project),
                    project.name
                )
                self.projects_list.add(ProjectsListRow(project))

    def render_projects_stack(self, state: ProjectsState, *args):
        if state.config_read_error:
            self.projects_stack.set_visible_child(self.projects_config_error)
        elif state.is_empty:
            self.projects_stack.set_visible_child(self.projects_empty_list)
        else:
            self.projects_stack.set_visible_child(self.projects_list)

    def render_workspace_stack(self, state: ProjectsState, *args):
        if state.select_project:
            try:
                self.workspace_stack.set_visible_child_name(state.selected_project.name)
            except AttributeError:
                pass
        else:
            self.workspace_stack.set_visible_child(self.no_selected_workspace_box)

    @Gtk.Template.Callback(name='on_projects_list_row_selected')
    def on_projects_list_row_selected(self, list_box, row):
        if row:
            self.dispatch('projects.select_project', row.get_child().get_project_name())
        else:
            self.dispatch('projects.clear_project_selection')

    @Gtk.Template.Callback(name='on_remove_project_button_clicked')
    def on_remove_project_button_clicked(self, *args, **kwargs):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Remove {self.app.projects.selected_project.name}",
        )
        dialog.format_secondary_text(
            "Do you really want to remove this project?\nAll project data will not be lost."
        )
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            self.dispatch('projects.remove_project', self.app.projects.selected_project.name)

        dialog.destroy()

    @Gtk.Template.Callback(name='on_add_project_button_clicked')
    def on_add_project_button_clicked(self, *args, **kwargs):
        self.new_project_popover.popup()

    @Gtk.Template.Callback(name='on_new_project_popover_show')
    def on_new_project_popover_show(self, *args, **kwargs):
        self.new_project_name_entry.set_text('')
        self.new_project_path_entry.set_text('')

    @Gtk.Template.Callback(name='on_new_project_path_dialog_clicked')
    def on_new_project_path_dialog_clicked(self, *args, **kwargs):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        filter_yaml = Gtk.FileFilter()
        filter_yaml.set_name("Docker-compose yaml files")
        filter_yaml.add_mime_type("application/x-yaml")
        dialog.add_filter(filter_yaml)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.new_project_path_entry.set_text(dialog.get_filename())

        dialog.destroy()

    @Gtk.Template.Callback(name='on_new_project_entry_changed')
    def on_on_new_project_entry_changed(self, *args, **kwargs):
        if self.new_project_name_entry.get_text() and self.new_project_path_entry.get_text():
            self.new_project_popover_add_button.set_sensitive(True)
        else:
            self.new_project_popover_add_button.set_sensitive(False)

    @Gtk.Template.Callback(name='on_new_project_popover_close_button_clicked')
    def on_new_project_popover_close_button_clicked(self, *args, **kwargs):
        self.new_project_popover.popdown()

    @Gtk.Template.Callback(name='on_new_project_popover_add_button_clicked')
    def on_new_project_popover_add_button_clicked(self, *args, **kwargs):
        self.dispatch('projects.add_project', Project(
            name=self.new_project_name_entry.get_text(),
            path=Path(self.new_project_path_entry.get_text()),
            use_sudo=self.new_project_sudo_switch.get_active(),
        ))
        self.new_project_popover.popdown()

    @Gtk.Template.Callback(name='on_create_project_button_clicked')
    def on_create_project_button_clicked(self, *args, **kwargs):
        self.create_project_popover.popup()

    @Gtk.Template.Callback(name='on_create_project_popover_show')
    def on_create_project_popover_show(self, *args, **kwargs):
        self.create_project_name_entry.set_text('')
        self.create_project_path_entry.set_text('')

    @Gtk.Template.Callback(name='on_create_project_path_dialog_clicked')
    def on_create_project_path_dialog_clicked(self, *args, **kwargs):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self, action=Gtk.FileChooserAction.SAVE
        )
        dialog.set_create_folders(True)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name('docker-compose.yml')
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE,
            Gtk.ResponseType.OK,
        )

        filter_yaml = Gtk.FileFilter()
        filter_yaml.set_name("Docker-compose yaml files")
        filter_yaml.add_mime_type("application/x-yaml")
        dialog.add_filter(filter_yaml)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.create_project_path_entry.set_text(dialog.get_filename())

        dialog.destroy()

    @Gtk.Template.Callback(name='on_create_project_entry_changed')
    def on_create_project_entry_changed(self, *args, **kwargs):
        if self.create_project_name_entry.get_text() and self.create_project_path_entry.get_text():
            self.create_project_popover_create_button.set_sensitive(True)
        else:
            self.create_project_popover_create_button.set_sensitive(False)

    @Gtk.Template.Callback(name='on_create_project_popover_create_button_clicked')
    def on_create_project_popover_create_button_clicked(self, *args, **kwargs):
        project_path = Path(self.create_project_path_entry.get_text())
        project_path.touch()
        self.dispatch('projects.add_project', Project(
            name=self.create_project_name_entry.get_text(),
            path=project_path,
            use_sudo=self.create_project_sudo_switch.get_active(),
        ))
        self.create_project_popover.popdown()

    @Gtk.Template.Callback(name='on_create_project_popover_close_button_clicked')
    def on_create_project_popover_close_button_clicked(self, *args, **kwargs):
        self.create_project_popover.popdown()
