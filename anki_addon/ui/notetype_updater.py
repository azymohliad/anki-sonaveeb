from aqt import mw
from aqt.qt import QMessageBox

from ..notetypes import NoteTypeManager


def check_notetype_updates(ntmanager: NoteTypeManager):
    # Get a list of supported note types
    notetypes = ntmanager.get_intended_notetypes()
    # Check note types updates
    updates = [ntmanager.get_pending_update(n) for n in notetypes]
    required = any([u.is_required() for u in updates])
    can_or_need = 'need to' if required else 'can'
    if any([u.is_consequential() for u in updates]):
        # If there are consequential note type updates, ask user to confirm
        # If all note type updates are purely additive or cosmetic,
        # update without bothering a user
        message = (
            f'Sõnaveeb note types {can_or_need} be updated, but some of the '
            'changes are consequential and require your confirmation.'
        )
        message += '<ol>'
        for notetype, update in zip(notetypes, updates):
            if update.is_empty():
                continue
            message += f'<li>{notetype["name"]}:<ul>'
            if update.fields_to_add:
                message += f'<li>Add fields: {", ".join(update.fields_to_add)}</li>'
            if update.fields_to_remove:
                message += f'<li>Remove fields: {", ".join(update.fields_to_remove)}</li>'
            if update.templates_to_add:
                message += f'<li>Add card templates: {", ".join(update.templates_to_add)}</li>'
            if update.templates_to_remove:
                message += f'<li>Remove card templates: {", ".join(update.templates_to_remove)}</li>'
            if update.templates_to_update:
                message += f'<li>Update card templates: {", ".join(update.templates_to_update)}</li>'
            if update.style:
                message += '<li>Change style</li>'
            if update.fields_order:
                message += '<li>Change fields order</li>'
            message += '</ul></li>'
        message += '</ol>'
        message += (
            '<br>'
            'These changes may affect your collection, so it is recommended '
            'to create a backup before applying the updates (File -> Create Backup).'
            '<br><br>'
            'Would you like to apply these updates now?'
        )
        answer = QMessageBox.question(
            mw,
            'Update note types?',
            message,
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No
        )
        if answer == QMessageBox.StandardButton.No:
            if required:
                return None
            else:
                return notetypes
    # Apply updates
    for notetype, update in zip(notetypes, updates):
        if not update.is_empty():
            ntmanager.update_notetype(notetype)

