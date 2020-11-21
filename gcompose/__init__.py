from typing import Callable


class AppMixin(object):
    _app = None

    @property
    def app(self):
        if self._app is None:
            self._app = self.get_toplevel().get_application()
        return self._app


class StateMixin(object):
    _app = None

    @property
    def app(self):
        if self._app is None:
            self._app = self.get_toplevel().get_application()
        return self._app

    def dispatch(self, signal: str, *args, **kwargs):
        if '.' in signal:
            app_attr, sig = signal.split('.', 1)
            getattr(self.app, app_attr).emit(sig, *args, **kwargs)
        else:
            self.app.emit(signal, *args, **kwargs)

    def mapProp(self, prop: str, clb: Callable):
        if '.' in prop:
            app_attr, prp = prop.split('.', 1)
            getattr(self.app, app_attr).connect('notify::' + prp.replace('_', '-'), clb)
        else:
            self.app.connect('notify::' + prop.replace('_', '-'), clb)

    def mapProps(self, props_map: dict):
        for prop, clb in props_map.items():
            if callable(clb):
                self.mapProp(prop, clb)
            else:
                if type(clb) is list or type(clb) is tuple or type(clb) is set:
                    for cb in clb:
                        if callable(cb):
                            self.mapProp(prop, cb)
