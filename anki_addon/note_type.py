from aqt import mw


MODEL_NAME_DEFAULT = 'Sõnaveeb Basic'
MODEL_NAME_USER = 'Sõnaveeb Custom'

MODEL_FIELDS = ['Morphology', 'Translation', 'URL']

TEMPLATE_FORWARD_NAME = 'Translate from Estonian'
TEMPLATE_FORWARD_FRONT = '{{Morphology}}'
TEMPLATE_FORWARD_BACK = '''\
{{FrontSide}}

<hr id=answer>

{{Translation}}

<div class="footer">
    <button onclick="window.location.href='{{URL}}';">
        Sõnaveeb
    </button>
</div>
'''

TEMPLATE_REVERSE_NAME = 'Translate into Estonian'
TEMPLATE_REVERSE_FRONT = '{{Translation}}'
TEMPLATE_REVERSE_BACK = '''\
{{FrontSide}}

<hr id=answer>

{{Morphology}}

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
    return (
        note_type['css'] == STYLE
        and len(note_type['tmpls']) == 2
        and check_template(note_type, TEMPLATE_FORWARD_NAME, TEMPLATE_FORWARD_FRONT, TEMPLATE_FORWARD_BACK)
        and check_template(note_type, TEMPLATE_REVERSE_NAME, TEMPLATE_REVERSE_FRONT, TEMPLATE_REVERSE_BACK)
    )


def update_templates(note_type):
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
