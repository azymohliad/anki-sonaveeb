from aqt import mw, gui_hooks
from aqt.utils import qconnect
from aqt.qt import QAction

from .ui import SonaveebDialog, check_templates_updates
from .sonaveeb import Sonaveeb

def open_sonaveeb_dialog():
    global sonaveeb
    global win
    if win is None:
        win = SonaveebDialog(sonaveeb)
    win.show()

def destroy_sonaveeb_dialog():
    global win
    win = None

win = None
sonaveeb = Sonaveeb()
action = QAction("Sõnaveeb Deck Builder", mw)
qconnect(action.triggered, open_sonaveeb_dialog)
mw.form.menuTools.addAction(action)

gui_hooks.profile_will_close.append(destroy_sonaveeb_dialog)
gui_hooks.profile_did_open.append(check_templates_updates)
