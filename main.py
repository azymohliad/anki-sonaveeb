#!/usr/bin/env python

import argparse
import sonaveeb


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Anki Sonaveeb')
    parser.add_argument('word')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    sv = sonaveeb.Sonaveeb()
    info = sv.get_word_info(args.word, args.debug)
    print(info.summary(lang='uk'))
