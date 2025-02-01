import typing as tp
import dataclasses as dc
from os import path
from aqt import mw
from anki.models import NoteType

Fields = tp.List[str]
Templates = tp.Dict[str, tp.Tuple[str, str]]


def add_notetype(name: str, fields: Fields, sort_idx: int, templates: Templates, style: str, metadata: dict):
    '''Create new note type.
    '''
    models = mw.col.models
    notetype = models.new(name)
    for field in fields:
        models.add_field(notetype, models.new_field(field))
    models.set_sort_index(notetype, sort_idx)
    for name, (front, back) in templates.items():
        forward_template = models.new_template(name)
        forward_template['qfmt'] = front
        forward_template['afmt'] = back
        models.add_template(notetype, forward_template)
    notetype['css'] = style
    for k, v in metadata.items():
        notetype[k] = v
    models.add(notetype)
    return notetype


def update_fields(notetype, fields: Fields, sort_idx: int):
    '''Update note type to ensure it contains expected fields.
    '''
    updated = False
    models = mw.col.models
    existing_fields = [f['name'] for f in notetype['flds']]
    # Add missing fields
    for field in fields:
        if field not in existing_fields:
            models.add_field(notetype, models.new_field(field))
            updated = True
    # Remove unknown fields
    for field in notetype['flds']:
        if field['name'] not in fields:
            models.remove_field(notetype, field)
            updated = True
    # Update fields order
    for target_idx, field_name in enumerate(fields):
        current_idx = next(i for i, f in enumerate(notetype['flds']) if f['name'] == field_name)
        if current_idx != target_idx:
            models.reposition_field(notetype, notetype['flds'][current_idx], target_idx)
            updated = True
    # Update sort index
    if models.sort_idx(notetype) != sort_idx:
        models.set_sort_index(notetype, sort_idx)
        updated = True
    return updated


def update_card_templates(notetype, templates: Templates, style: str):
    '''Update note type to ensure it contains expected card templates and style.
    '''
    updated = False
    models = mw.col.models
    existing_templates = {t['name']: t for t in notetype['tmpls']}
    for name, (front, back) in templates.items():
        template = existing_templates.get(name)
        if template is not None:
            # Update existing templates
            if template['qfmt'] != front or template['afmt'] != back:
                template['qfmt'] = front
                template['afmt'] = back
                updated = True
        else:
            # Add missing templates
            template = models.new_template(name)
            template['qfmt'] = front
            template['afmt'] = back
            models.add_template(notetype, template)
            updated = True
    # Remove unknown templates
    for name, template in existing_templates.items():
        if name not in templates:
            models.remove_template(notetype, template)
            updated = True
    # Update style
    if notetype['css'] != style:
        notetype['css'] = style
        updated = True
    return updated


@dc.dataclass
class NoteTypeChanges:
    '''Descriptor of the changes to be applied to a note type.
    '''
    fields_to_add: list = dc.field(default_factory=list)
    fields_to_remove: list = dc.field(default_factory=list)
    fields_order: bool = False
    fields_sort_index: bool = False
    templates_to_add: list = dc.field(default_factory=list)
    templates_to_remove: list = dc.field(default_factory=list)
    templates_to_update: list = dc.field(default_factory=list)
    style: bool = False

    @classmethod
    def compute(cls, notetype, fields: Fields = None, sort_idx: int = 0, templates: Templates = None, style: str = None):
        '''Derive the changes to be applied to a note type in order for it to contain the expected data.
        '''
        diff = cls()
        # Fields
        if fields is not None:
            existing_fields = [f['name'] for f in notetype['flds']]
            diff.fields_order = fields != existing_fields
            diff.fields_to_add = [f for f in fields if f not in existing_fields]
            diff.fields_to_remove = [f for f in existing_fields if f not in fields]
            diff.fields_sort_index = sort_idx != notetype['sortf']
        # Card templates
        if templates is not None:
            existing_templates = {t['name']: t for t in notetype['tmpls']}
            existing_template_names = set(existing_templates.keys())
            target_template_names = set(templates.keys())
            diff.templates_to_add = list(target_template_names - existing_template_names)
            diff.templates_to_remove = list(existing_template_names - target_template_names)
            for name, (front, back) in templates.items():
                template = existing_templates.get(name)
                if template is not None:
                    if template['qfmt'] != front or template['afmt'] != back:
                        diff.templates_to_update.append(name)
        # Style
        if style is not None:
            diff.style = notetype['css'] != style
        return diff

    def is_required(self):
        '''Check if the note type update is required to make it valid.
        '''
        return self.fields_to_add or self.fields_to_remove or self.fields_order

    def is_consequential(self):
        '''Check if these changes require user confirmation.
        '''
        return (
            self.fields_to_remove           # Causes full DB reupload, removes data
            or self.fields_to_add           # Causes full DB reupload
            or self.fields_order            # Causes full DB reupload
            or self.templates_to_remove     # Removes cards
            or self.templates_to_add        # Adds cards
        )

    def is_visual(self):
        '''Check if these changes affect how cards look.
        '''
        return self.templates_to_update or self.style

    def is_empty(self):
        '''Check if no changes are present.
        '''
        return not any([bool(getattr(self, f.name)) for f in dc.fields(self)])


class NoteTypeManager:
    SONAVEEB_MARKER = 'sonaveeb_marker'
    # Sort field index
    SORT_FIELD = 1
    # List of fields that the note type must contain to be valid for this addon.
    FIELDS = [
        'Word ID',
        'Morphology',
        'Definition',
        'Rection',
        'Translation',
        'Examples',
        'URL',
        'Audio',
    ]

    def __init__(self):
        # Read default templates' markups and style
        templates_dir = path.join(path.dirname(__file__), 'templates')
        with open(path.join(templates_dir, 'style.css'), 'r', encoding='utf-8') as file:
            style = file.read()
        with open(path.join(templates_dir, 'into_estonian_front.html'), 'r', encoding='utf-8') as file:
            markup_into_estonian_front = file.read()
        with open(path.join(templates_dir, 'into_estonian_back.html'), 'r', encoding='utf-8') as file:
            markup_into_estonian_back = file.read()
        with open(path.join(templates_dir, 'from_estonian_front.html'), 'r', encoding='utf-8') as file:
            markup_from_estonian_front = file.read()
        with open(path.join(templates_dir, 'from_estonian_back.html'), 'r', encoding='utf-8') as file:
            markup_from_estonian_back = file.read()

        # Default card templates
        templates_from_estonian = {
            'Translate from Estonian': (markup_from_estonian_front, markup_from_estonian_back)
        }
        templates_into_estonian = {
            'Translate into Estonian': (markup_into_estonian_front, markup_into_estonian_back)
        }

        # Default note types
        self.default_notetypes = {
            'Sõnaveeb (bidirectional)': (
                templates_from_estonian | templates_into_estonian, style
            ),
            'Sõnaveeb (from Estonian)': (
                templates_from_estonian, style
            ),
            'Sõnaveeb (into Estonian)': (
                templates_into_estonian, style
            ),
        }

    def is_notetype_valid(self, notetype):
        '''Check if note type is suitable for this addon.
        '''
        note_fields = [f['name'] for f in notetype['flds']]
        return note_fields == self.FIELDS and self.is_notetype_intended(notetype)

    def is_notetype_intended(self, notetype):
        '''Check if note type is intended for this addon.
        '''
        return self.SONAVEEB_MARKER in notetype

    def get_valid_notetypes(self) -> tp.List[NoteType]:
        '''Get a list of note types that are intended and sutiable for this addon.
        '''
        return [
            nt for nt in mw.col.models.all()
            if self.is_notetype_valid(nt)
        ]

    def get_intended_notetypes(self) -> tp.List[NoteType]:
        '''Get a list of note types that are intended for this addon.

        Not all of them might be valid due to being outdated.
        '''
        return [
            nt for nt in mw.col.models.all()
            if self.is_notetype_intended(nt)
        ]

    def get_pending_update(self, notetype) -> NoteTypeChanges:
        '''Get a description of changes necessary to make the note type valid and up-to-date.

        For default note types this includes fields, card templates, and style.
        For custom note types this only includes fields.
        '''
        # For default note types: check fields, templates, and style.
        # For others: check fields only.
        templates, style = self.default_notetypes.get(notetype['name'], (None, None))
        return NoteTypeChanges.compute(notetype, self.FIELDS, self.SORT_FIELD, templates, style)

    def update_notetype(self, notetype) -> bool:
        '''Update the note type.

        For default note types this includes fields, card templates, and style.
        For custom note types this only includes fields.
        '''
        # Update fields for all note types
        updated = update_fields(notetype, self.FIELDS, self.SORT_FIELD)
        # Update templates and style only for default note types
        templates_and_style = self.default_notetypes.get(notetype['name'])
        if templates_and_style is not None:
            templates, style = templates_and_style
            updated |= update_card_templates(notetype, templates, style)
        # Apply updates
        if updated:
            mw.col.models.update_dict(notetype)
        return updated

    def create_missing_defaults(self):
        '''Create default note types if needed.
        '''
        metadata = {self.SONAVEEB_MARKER: None}
        for name, (templates, style) in self.default_notetypes.items():
            if mw.col.models.by_name(name) is None:
                add_notetype(name, self.FIELDS, self.SORT_FIELD, templates, style, metadata)

