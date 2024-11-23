import os
import bs4
import requests
import typing as tp
from collections import Counter


URL = 'https://translate.google.com/m?tl={target_lang}&sl={source_lang}&q={text}'


def translate(text: str, target_lang: str = 'en', source_lang: str = 'et', debug: bool = False):
    '''Translate text with Google Translate.'''
    # GET request to google translate does not requrie authentication
    url = URL.format(target_lang=target_lang, source_lang=source_lang, text=text)
    resp = requests.get(url)
    if resp.status_code != 200:
        raise RuntimeError(f'Request failed: {resp.status_code}')
    dom = bs4.BeautifulSoup(resp.text, 'html.parser')
    if debug:
        open(os.path.join('debug', f'gtranslate_{text}.html'), 'w').write(dom.prettify())
    if result := dom.find('div', class_='result-container'):
        result = result.string
    return result


def cross_translate(sources: tp.Dict[str, tp.List[str]], lang):
    '''Find the most suitable common translations for multiple synonyms.

    Translate a list of synonyms from multiple source languages into a single target language,
    sort translations by frequency of their repetition, and filter the most popular ones.

    Args:
        source: pairs of source language code and a list of input words in that language.
        lang: target translation language.
    '''
    translations = []
    for source_lang, words in sources.items():
        text = ', '.join(words)
        translation = translate(
            text=text,
            target_lang=lang,
            source_lang=source_lang)
        translations += [t.strip() for t in translation.lower().split(',')]
    counted = Counter(translations)
    threshold = min(len(sources), max(counted.values()))
    ordered = sorted(counted.items(), key=lambda x: x[1], reverse=True)
    filtered = [k for k, v in ordered if v >= threshold]
    return filtered
