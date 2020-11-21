import sys
import gi
import logging

gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '4')
gi.require_version('Vte', '2.91')

from gcompose.state import StatefullApplication

VERSION = '1.0'
logging.basicConfig(level=logging.DEBUG)


def main(version=None):
    if version is None:
        version = VERSION
    app = StatefullApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main(VERSION))
