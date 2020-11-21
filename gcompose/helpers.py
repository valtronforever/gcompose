from gi.repository import Gtk, Vte
import logging


def password_prompt_dialog(parent, message, title=''):
    dialogWindow = Gtk.MessageDialog(
        parent.get_toplevel(),
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.QUESTION,
        Gtk.ButtonsType.OK_CANCEL,
        message
    )

    dialogWindow.set_title(title)

    dialogBox = dialogWindow.get_content_area()
    userEntry = Gtk.Entry()
    userEntry.set_visibility(False)
    userEntry.set_invisible_char("*")
    userEntry.set_size_request(250, 0)
    dialogBox.pack_end(userEntry, False, False, 0)

    dialogWindow.show_all()
    response = dialogWindow.run()
    text = userEntry.get_text()
    dialogWindow.destroy()
    if (response == Gtk.ResponseType.OK) and (text != ''):
        return text
    else:
        return None


def check_prompt(terminal: Vte.Terminal, prompt: str) -> bool:
    text, attrs = terminal.get_text()
    lines = [line for line in text.splitlines() if line]
    last_lines = ''.join(lines[-1:])
    if prompt in last_lines:
        return True
    else:
        return False
