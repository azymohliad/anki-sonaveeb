#!/usr/bin/env python

import argparse
import sonaveeb
from anki.collection import Collection

ANKI_COLLECTION = '/home/azymohliad/.var/app/net.ankiweb.Anki/data/Anki2/User 1/collection.anki2'


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Sonaveeb example')
    parser.add_argument('deck')
    parser.add_argument('word')
    parser.add_argument('-l', '--language', default='uk')
    args = parser.parse_args()

    sv = sonaveeb.Sonaveeb()
    word_info = sv.get_word_info(args.word)
    if word_info is None:
        print('Word not found! :(')
        exit(1)

    tag = word_info.pos
    front = word_info.short_record()
    translations = word_info.lexemes[0].translations.get(args.language)
    if translations is None:
        langs = word_info.lexemes[0].translations.keys()
        print(f'No translation {word_info.word} into "{args.language}". Available translations: {", ".join(langs)}')
        exit(1)
    back = ', '.join(translations[:3])

    print('Note preview:')
    print(f'  Front: {front}')
    print(f'  Back: {back}')
    print(f'  Tags: {tag}')
    response = input('Add note? [Y/n]: ')

    if response == '' or response == 'Y':
        col = Collection(ANKI_COLLECTION)
        deck = col.decks.id(args.deck)
        node_type = col.models.id_for_name('Basic (and reversed card)')
        note = col.new_note(node_type)
        note['Front'] = front
        note['Back'] = back
        note.add_tag(tag)
        col.add_note(note, deck)
