from aqt import mw
from aqt.utils import qconnect
from aqt.qt import QAction

from .ui import SonaveebNoteDialog
from .sonaveeb import Sonaveeb

def open_sonaveeb_dialog():
    global sonaveeb
    global win
    if win is None:
        win = SonaveebNoteDialog(sonaveeb)
    win.show()

win = None
sonaveeb = Sonaveeb()
action = QAction("Add notes from Sõnaveeb", mw)
qconnect(action.triggered, open_sonaveeb_dialog)
mw.form.menuTools.addAction(action)
