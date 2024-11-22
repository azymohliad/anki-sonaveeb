from aqt import mw


MODEL_NAME_DEFAULT = 'Sõnaveeb Basic'
MODEL_NAME_USER = 'Sõnaveeb Custom'

MODEL_FIELDS = [
    'Word ID',
    'Morphology',
    'Definition',
    'Rection',
    'Translation',
    'Examples',
    'URL',
]

TEMPLATE_FORWARD_NAME = 'Translate from Estonian'
TEMPLATE_FORWARD_FRONT = '''\
<div class="tags">{{Tags}}</div>
{{Morphology}}
<div class="rection">{{Rection}}</div>
{{#Examples}}
<div class="examples">
    <h4>Näited:</h4>
    {{Examples}}
</div>
{{/Examples}}
'''
TEMPLATE_FORWARD_BACK = '''\
{{FrontSide}}

<hr id=answer>

<div class="definition">{{Definition}}</div>

<div class="translation">{{Translation}}</div>

<div class="footer">
    <button onclick="window.location.href='{{URL}}';">
        Sõnaveeb
    </button>
</div>
'''

TEMPLATE_REVERSE_NAME = 'Translate into Estonian'
TEMPLATE_REVERSE_FRONT = '''\
<div class="tags">{{Tags}}</div>
{{Translation}}
'''
TEMPLATE_REVERSE_BACK = '''\
{{FrontSide}}

<hr id=answer>

{{Morphology}}
<div class="rection">{{Rection}}</div>

<div class="definition">{{Definition}}</div>

{{#Examples}}
<div class="examples">
    <h4>Näited:</h4>
    {{Examples}}
</div>
{{/Examples}}

<div class="footer">
    <button onclick="window.location.href='{{URL}}';">
        Sõnaveeb
    </button>
</div>
'''

STYLE = '''\
.card {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}

.tags {
    text-align: right;
    font-style: italic;
    color: #666;
    margin: 10px 0;
    font-size: 18px;
}

.rection {
    text-align: center;
    font-style: italic;
    color: #555;
    margin: 10px 0;
    font-size: 16px;
}

.definition {
    font-style: italic;
    color: #666;
    margin: 10px 0;
    font-size: 18px;
}

.translation {
    font-weight: bold;
    margin: 10px 0;
}

.examples {
    margin: 15px 20px;
    font-size: 18px;
}

.examples h4 {
    color: #666;
    margin-bottom: 5px;
}

.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    margin-bottom: 20px;
}
'''


class NoteTypeError(Exception):
    def __init__(self, note_type, msg=None):
        super().__init__(msg)
        self.note_type = note_type


def find_default_note_type():
    return mw.col.models.by_name(MODEL_NAME_DEFAULT)


def find_user_note_type():
    return mw.col.models.by_name(MODEL_NAME_USER)


def note_type_valid(note_type):
    note_fields = [f['name'] for f in note_type['flds']]
    return note_fields == MODEL_FIELDS


def validate_note_type(note_type):
    if not note_type_valid(note_type):
        raise NoteTypeError(note_type)


def templates_match(note_type):
    if not note_type_valid(note_type):
        return False
    try:
        matches = (
            len(note_type['tmpls']) == 2
            and check_template(note_type, TEMPLATE_FORWARD_NAME, TEMPLATE_FORWARD_FRONT, TEMPLATE_FORWARD_BACK)
            and check_template(note_type, TEMPLATE_REVERSE_NAME, TEMPLATE_REVERSE_FRONT, TEMPLATE_REVERSE_BACK)
            and note_type['css'] == STYLE
        )
        return matches
    except (KeyError, AttributeError):
        return False


def update_templates(note_type):
    models = mw.col.models
    # Add any missing fields
    existing_fields = [f['name'] for f in note_type['flds']]
    for field in MODEL_FIELDS:
        if field not in existing_fields:
            models.add_field(note_type, models.new_field(field))

    # Reorder fields to match MODEL_FIELDS order
    for idx, field_name in enumerate(MODEL_FIELDS):
        current_position = next(i for i, f in enumerate(note_type['flds']) if f['name'] == field_name)
        if current_position != idx:
            models.reposition_field(note_type, note_type['flds'][current_position], idx)

    # Update templates
    templates = note_type["tmpls"]
    if len(templates) == 2:
        forward_template = find_template_by_name(note_type, TEMPLATE_FORWARD_NAME) \
            or find_template_by_field_content(note_type, 'qfmt', '{{Morphology}}')
        reverse_template = find_template_by_name(note_type, TEMPLATE_REVERSE_NAME) \
            or find_template_by_field_content(note_type, 'qfmt', '{{Translation}}')
        if forward_template is not None and reverse_template is not None and forward_template is not reverse_template:
            update_template(note_type, forward_template, TEMPLATE_FORWARD_NAME, TEMPLATE_FORWARD_FRONT, TEMPLATE_FORWARD_BACK)
            update_template(note_type, reverse_template, TEMPLATE_REVERSE_NAME, TEMPLATE_REVERSE_FRONT, TEMPLATE_REVERSE_BACK)
            note_type['css'] = STYLE
            mw.col.models.update_dict(note_type)
            return
    raise NoteTypeError(note_type, 'Cannot update card templates safely')


def add_default_note_type():
    models = mw.col.models
    note_type = models.new(MODEL_NAME_DEFAULT)
    for field in MODEL_FIELDS:
        models.add_field(note_type, models.new_field(field))
    add_template(note_type, TEMPLATE_FORWARD_NAME, TEMPLATE_FORWARD_FRONT, TEMPLATE_FORWARD_BACK)
    add_template(note_type, TEMPLATE_REVERSE_NAME, TEMPLATE_REVERSE_FRONT, TEMPLATE_REVERSE_BACK)
    note_type['css'] = STYLE
    models.add(note_type)
    return note_type


def find_template_by_name(note_type, name):
    return next((t for t in note_type['tmpls'] if t['name'] == name), None)


def find_template_by_field_content(note_type, field, content):
    return next((t for t in note_type['tmpls'] if content in t[field]), None)


def check_template(note_type, name, front, back):
    template = find_template_by_name(note_type, name)
    return (
        template is not None
        and template['qfmt'] == front
        and template['afmt'] == back
    )


def update_template(note_type, template, name, front, back):
    template['name'] = name
    template['qfmt'] = front
    template['afmt'] = back


def add_template(note_type, name, front, back):
    forward_template = mw.col.models.new_template(name)
    forward_template['qfmt'] = front
    forward_template['afmt'] = back
    mw.col.models.add_template(note_type, forward_template)
