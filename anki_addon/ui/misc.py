from aqt import mw
from aqt.qt import QMessageBox

from .. import note_type as nt


POPUP_TITLE = 'Update Sõnaveeb Card Templates?'
POPUP_TEXT = f'''\
Card templates update for "{nt.MODEL_NAME_DEFAULT}" note type is available.

If you modified the templates manually and would prefer to keep using them \
without receiving updates, rename "{nt.MODEL_NAME_DEFAULT}" note type into \
"{nt.MODEL_NAME_USER}".

Update card templates?
'''


def check_templates_updates():
    ntype = mw.col.models.by_name(nt.MODEL_NAME_DEFAULT)
    if ntype is not None:
        if not nt.templates_match(ntype):
            answer = QMessageBox.question(
                mw,
                POPUP_TITLE,
                POPUP_TEXT,
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.No
            )
            if answer == QMessageBox.StandardButton.Yes:
                try:
                    nt.update_templates(ntype)
                except nt.NoteTypeError as exp:
                    QMessageBox.warning(mw, 'Cannot Update Card Templates', str(exp))
