from aqt import mw, gui_hooks
from aqt.utils import qconnect
from aqt.qt import QAction

from .ui import SonaveebDialog
from .sonaveeb import Sonaveeb
from .notetypes import NoteTypeManager


def open_sonaveeb_dialog():
    global window
    if window is None:
        window = SonaveebDialog(notetype_manager, sonaveeb)
    window.show()


def destroy_sonaveeb_dialog():
    global window
    window = None


window = None
sonaveeb = Sonaveeb()
notetype_manager = NoteTypeManager()

action = QAction("Sõnaveeb Deck Builder", mw)
qconnect(action.triggered, open_sonaveeb_dialog)
mw.form.menuTools.addAction(action)
gui_hooks.profile_will_close.append(destroy_sonaveeb_dialog)
