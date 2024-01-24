from aqt import mw
from aqt.utils import qconnect
from aqt.qt import QAction

from .ui import SonaveebNoteDialog

def open_sonaveeb_dialog():
    global win
    if win is None:
        win = SonaveebNoteDialog()
    win.show()

win = None
action = QAction("Add notes from Sõnaveeb", mw)
qconnect(action.triggered, open_sonaveeb_dialog)
mw.form.menuTools.addAction(action)
