import os
import requests
import typing as tp
from collections import Counter

URL = 'https://api.mymemory.translated.net/get?q={text}&langpair={source_lang}|{target_lang}'


def translate(
    text: str,
    target_lang: str = 'en',
    source_lang: str = 'et',
    timeout: tp.Optional[float] = None,
    cleanup: bool = True
) -> tp.List[str]:
    '''Translates text with MyMemory'''
    url = URL.format(target_lang=target_lang, source_lang=source_lang, text=text)
    headers = {'user-agent': 'azymohliad/anki-sonaveeb'}
    resp = requests.get(url, timeout=timeout, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Request failed: {resp.status_code}')
    resp_data = resp.json()
    translation = resp_data["responseData"]["translatedText"]
    if cleanup:
        # Convert to lowercase, unless the original had uppercase characters.
        if text.islower():
            translation = translation.lower()
        # Remove punctuation, unless the input had it
        punctuation = ".,!?"
        if not any(c in text for c in punctuation):
            mapping = {ord(c): None for c in punctuation}
            translation = translation.translate(mapping)
        # Strip spaces
        translation = translation.strip()
    return translation


def cross_translate(sources: tp.Dict[str, tp.List[str]], lang: str, timeout: float = None):
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
            source_lang=source_lang,
            timeout=timeout
        )
        translations += [t.strip() for t in translation.split(',')]
    counted = Counter(translations)
    threshold = min(len(sources), max(counted.values()))
    ordered = sorted(counted.items(), key=lambda x: x[1], reverse=True)
    filtered = [k for k, v in ordered if v >= threshold]
    return filtered
