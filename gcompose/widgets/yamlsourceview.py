from pathlib import Path
from gi.repository import GObject, Gtk, GtkSource, Gdk


@Gtk.Template.from_file(str(Path(__file__).parents[0] / 'yamlsourceview.glade'))
class YamlSourceView(GtkSource.View):
    __gtype_name__ = 'YamlSourceView'

    # sourceview = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        buffer = self.get_buffer()
        lm = GtkSource.LanguageManager()
        lang = lm.get_language('yaml')
        buffer.set_language(lang)
        manager = GtkSource.StyleSchemeManager().get_default()
        scheme = manager.get_scheme("oblivion")
        buffer.set_style_scheme(scheme)

    @GObject.Signal
    def save_key_pressed(self):
        pass

    @Gtk.Template.Callback(name='on_key_press_event')
    def on_key_press_event(self, widget, event: Gdk.EventKey, *args, **kwargs):
        if event.keyval == Gdk.KEY_s and (event.state & Gdk.ModifierType.CONTROL_MASK):
            self.emit('save_key_pressed')
