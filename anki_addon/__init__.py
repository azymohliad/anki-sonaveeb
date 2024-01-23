from aqt import mw
from aqt.utils import qconnect
from aqt.qt import QAction

from .ui import SonaveebNoteDialog


win = SonaveebNoteDialog()
action = QAction("Add notes from Sõnaveeb", mw)
qconnect(action.triggered, win.show)
mw.form.menuTools.addAction(action)
