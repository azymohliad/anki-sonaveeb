#!/usr/bin/env python

import os
import sys
import argparse

ADDON_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'anki_addon')
sys.path.append(ADDON_PATH)

import gtranslate


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Google Translate text')
    parser.add_argument('text', help='Source text')
    parser.add_argument('--source-lang', default='et', help='Source language (ISO-639 code)')
    parser.add_argument('--target-lang', default='en', help='Target language (ISO-639 code)')
    parser.add_argument('--debug', action='store_true', help='Save HTML page before parsing for debugging')
    args = parser.parse_args()

    result = gtranslate.translate(
        text=args.text,
        target_lang=args.target_lang,
        source_lang=args.source_lang,
        debug=args.debug)
    print(result)
