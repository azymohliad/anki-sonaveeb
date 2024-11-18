#!/usr/bin/env python

import os
import sys
import argparse

ADDON_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'anki_addon')
sys.path.append(ADDON_PATH)

import sonaveeb


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Sonaveeb text')
    parser.add_argument('word', help='Estonian word to look up')
    parser.add_argument('--lang', default='en', help='Language to translate to (ISO-639 code)')
    parser.add_argument('--dict',
                       default='unif',
                       choices=sonaveeb.Sonaveeb.DICTIONARY_TYPES.keys(),
                       help='Dictionary to use')
    parser.add_argument('--debug', action='store_true', help='Save HTML pages before parsing for debugging')
    args = parser.parse_args()

    sv = sonaveeb.Sonaveeb()
    sv.select_dictionary(args.dict)
    info = sv.get_word_info(args.word, debug=args.debug)
    print(info.summary(lang=args.lang))
