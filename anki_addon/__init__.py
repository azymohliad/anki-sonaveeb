from aqt import mw, gui_hooks
from aqt.utils import qconnect
from aqt.qt import QAction

from .ui import SonaveebDialog, check_notetype_updates
from .sonaveeb import Sonaveeb
from .notetypes import NoteTypeManager


def open_sonaveeb_dialog():
    global window
    if window is None:
        ntmanager.create_missing_defaults()
        check_notetype_updates(ntmanager)
        notetypes = ntmanager.get_valid_notetypes()
        if not notetypes:
            # Do nothing if there's no valid note types available
            # (e.g. if the required note types update was rejected by the user)
            return
        window = SonaveebDialog(notetypes, sonaveeb)
    window.show()


def destroy_sonaveeb_dialog():
    global window
    window = None


window = None
sonaveeb = Sonaveeb()
ntmanager = NoteTypeManager()

action = QAction("Sõnaveeb Deck Builder", mw)
qconnect(action.triggered, open_sonaveeb_dialog)
mw.form.menuTools.addAction(action)
gui_hooks.profile_will_close.append(destroy_sonaveeb_dialog)
