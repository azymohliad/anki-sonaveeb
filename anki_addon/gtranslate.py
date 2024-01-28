import os
import bs4
import requests
from collections import Counter


URL = 'https://translate.google.com/m?tl={target_lang}&sl={source_lang}&q={text}'


def translate(text, target_lang='en', source_lang='et', debug=False):
    # GET request to google translate does not requries authentication
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


def cross_translate(sources, lang, threshold=None):
    translations = []
    for source_lang, words in sources.items():
        text = ', '.join(words)
        translation = translate(
            text=text,
            target_lang=lang,
            source_lang=source_lang)
        translations += [t.strip() for t in translation.lower().split(',')]
    threshold = threshold or len(sources)
    counted = Counter(translations)
    filtered = [k for k, v in counted.items() if v >= threshold]
    return filtered
