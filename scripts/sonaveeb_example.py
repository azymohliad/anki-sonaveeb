#!/usr/bin/env python

import os
import sys
import argparse

ADDON_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'anki_addon')
sys.path.append(ADDON_PATH)

import sonaveeb


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Sonaveeb example')
    parser.add_argument('word')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    sv = sonaveeb.Sonaveeb()
    info = sv.get_word_info(args.word, debug=args.debug)
    print(info.summary(lang='uk'))
