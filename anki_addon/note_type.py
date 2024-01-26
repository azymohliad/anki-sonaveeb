from aqt import mw


MODEL_NAME = 'Sõnaveeb Basic'
MODEL_FIELDS = ['Morphology', 'Translation', 'URL']
ORIGINAL_TEMPLATE = '<a href="{{URL}}">{{Morphology}}</a>'
TRANSLATION_TEMPLATE = '{{Translation}}'


def find_note_type():
    return mw.col.models.id_for_name(MODEL_NAME)


def verify_note_type(ntid):
    note_type = mw.col.models.get(ntid)
    note_fields = [f['name'] for f in note_type['flds']]
    return note_fields == MODEL_FIELDS


def add_note_type():
    models = mw.col.models
    note_type = models.new(MODEL_NAME)
    for field in MODEL_FIELDS:
        models.add_field(note_type, models.new_field(field))

    forward_template = models.new_template('Translate from Estonian')
    forward_template['qfmt'] = ORIGINAL_TEMPLATE
    forward_template['afmt'] = '{{FrontSide}}\n\n<hr id=answer>\n\n' + TRANSLATION_TEMPLATE
    models.add_template(note_type, forward_template)

    reverse_template = models.new_template('Translate into Estonian')
    reverse_template['qfmt'] = TRANSLATION_TEMPLATE
    reverse_template['afmt'] = '{{FrontSide}}\n\n<hr id=answer>\n\n' + ORIGINAL_TEMPLATE
    models.add_template(note_type, reverse_template)

    result = models.add(note_type)
    return result.id
