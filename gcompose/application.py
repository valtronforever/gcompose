from typing import Optional, Tuple, Callable
import os
import logging
from pathlib import Path
import shlex
import shutil
from gi.repository import GObject, Gtk, Gio, GLib, GtkSource, Vte
from gcompose.widgets.yamlsourceview import YamlSourceView
from gcompose.windows.appwindow import AppWindow
from gcompose.helpers import password_prompt_dialog, check_prompt


SUDO_PROMPT_TEXT = "Running with sudo"


class Application(Gtk.Application):
    sudo_pwd: Optional[str] = None

    def __init__(self):
        GObject.type_register(GtkSource.View)
        GObject.type_register(Vte.Terminal)
        GObject.type_register(YamlSourceView)

        super().__init__(application_id='org.valtronforever.gcompose',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = AppWindow(application=self)
        win.present()

    def set_sudo_pwd(self, pwd: str):
        self.sudo_pwd = pwd

    def get_sudo_pwd(self) -> str:
        return self.sudo_pwd

    def spawn(self, command: str, working_dir: Path, stdout_cb: Callable, use_sudo: True) -> bool:
        if use_sudo:
            command = f"{shutil.which('sudo')} -p '{SUDO_PROMPT_TEXT}' -S " + command
        (success, pid, stdin, stdout, stderr) = GLib.spawn_async_with_pipes(
            str(working_dir),
            shlex.split(command),
            [k + '=' + v for k, v in os.environ.items()],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None
        )
        if success:
            if use_sudo:
                sudo_pwd = self.get_sudo_pwd()
                if sudo_pwd is None:
                    sudo_pwd = password_prompt_dialog(
                        self.props.active_window,
                        'Please enter sudo password',
                        'Sudo password'
                    )
                    if sudo_pwd is not None:
                        self.set_sudo_pwd(sudo_pwd)

                if sudo_pwd is None:
                    sudo_pwd = ''
                os.write(stdin, f"{sudo_pwd}\r".encode('utf-8'))
                os.close(stdin)

            def callback(*args, **kwargs):
                cmd_out = None
                with os.fdopen(stdout) as out:
                    cmd_out = out.read()

                stdout_cb(cmd_out)

            GLib.child_watch_add(
                GLib.PRIORITY_DEFAULT_IDLE,
                pid,
                callback
            )
        return success

    def launch_in_terminal(self, terminal: Vte.Terminal, command: str, working_dir: Path, use_sudo: bool = True):
        def put_pwd_to_stdin(*args, **kwargs):
            sudo_pwd = self.get_sudo_pwd()
            if sudo_pwd is None:
                sudo_pwd = password_prompt_dialog(
                    terminal.get_toplevel(),
                    'Please enter sudo password',
                    'Sudo password'
                )
                if sudo_pwd is not None:
                    self.set_sudo_pwd(sudo_pwd)

            if sudo_pwd is None:
                sudo_pwd = ''

            feed_attempts_left = 10

            def feed_command(attempts_left, *args, **kwargs):
                if attempts_left <= 0:
                    return

                attempts_left -= 1
                if check_prompt(terminal, SUDO_PROMPT_TEXT):
                    terminal.feed_child(f"{sudo_pwd}\r".encode('utf-8'))
                else:
                    GLib.timeout_add(500, feed_command, attempts_left)
            feed_command(feed_attempts_left)

        if use_sudo:
            command = f"{shutil.which('sudo')} -p '{SUDO_PROMPT_TEXT}' -S " + command

        terminal_args = [
            Vte.PtyFlags.DEFAULT,
            str(working_dir),
            shlex.split(command),
            [k + '=' + v for k, v in os.environ.items()],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
            GObject.G_MAXINT,
            None
        ]

        if use_sudo:
            terminal_args.append(put_pwd_to_stdin)
        else:
            terminal_args.append(None)

        terminal.spawn_async(*terminal_args)
