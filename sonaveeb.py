import os
import re
import typing as tp
import dataclasses as dc

import requests
import bs4


BASE_URL = 'https://sonaveeb.ee'
SEARCH_URL = 'https://sonaveeb.ee/search/unif/dlall/dsall/{word}/1'
DETAILS_URL = 'https://sonaveeb.ee/worddetails/unif/{word_id}'


class Sonaveeb:
    def __init__(self):
        self.session = requests.Session()
        # Obtain session cookies (wl_sess)
        # Without it other requests won't work
        self._request(BASE_URL)

    def _request(self, *args, **kwargs):
        resp = self.session.get(*args, **kwargs)
        if resp.status_code != 200:
            raise RuntimeError(f'Request failed: {resp.status_code}')
        return resp

    def _word_lookup_dom(self, word):
        resp = self._request(SEARCH_URL.format(word=word))
        return bs4.BeautifulSoup(resp.text, 'html.parser')

    def _word_details_dom(self, word_id):
        resp = self._request(DETAILS_URL.format(word_id=word_id))
        return bs4.BeautifulSoup(resp.text, 'html.parser')

    def _parse_word_id(self, dom):
        word_id = dom.find(attrs=dict(name='word-id'))
        if word_id is not None:
            word_id = word_id['value']
        return word_id

    def _parse_forms(self, dom):
        return [a['data-word'] for a in dom.find(class_='word-details').find_all('a', 'word-form')]

    def _parse_word_info(self, dom, word):
        info = WordInfo()
        info.word = dom.find(class_='homonym-name').span.string
        info.url = SEARCH_URL.format(word=word)
        info.pos = dom.find(class_='content-title').find(class_='tag').string
        info.lexemes = []
        for match in dom.find_all(id=re.compile('^lexeme-section')):
                lexeme = Lexeme()
                definition = match.find(id=re.compile('^definition-entry'))
                if definition is not None:
                    lexeme.definition = _remove_eki_tags(definition.span)
                lexeme.tags = [t.string for t in match.find_all(class_='tag')]
                lexeme.synonyms = [a.span.span.string for a in match.find_all('a', class_='synonym')]
                lexeme.translations = {}
                for translation in match.find_all(id=re.compile('^matches-show-more-panel')):
                    lang = translation.find(class_='lang-code').string
                    values = [_remove_eki_tags(a.span.span) for a in translation.find_all('a', class_='matching-word')]
                    lexeme.translations[lang] = values
                lexeme.examples = [s.string for s in match.find_all(class_='example-text-value')]
                info.lexemes.append(lexeme)

        info.morphology = []
        motphology_table = dom.find(class_='morphology-paradigm').find('table')
        for row in motphology_table.find_all('tr'):
            entry = tuple((_remove_eki_tags(c.span) for c in row.find_all('td') if c.span))
            info.morphology.append(entry)
        return info

    def get_word_info(self, word, debug=False):
        # Look-up base form word ID
        dom = self._word_lookup_dom(word)
        word_id = self._parse_word_id(dom)

        # If not found, the word may be in conjugated form. Find the base form
        if word_id is None:
            forms = self._parse_forms(dom)
            word = forms[0]
            dom = self._word_lookup_dom(word)
            word_id = self._parse_word_id(dom)

        # The word is not found
        if word_id is None:
            return None

        # Look-up word details
        dom = self._word_details_dom(word_id)
        if debug:
            open(os.path.join('debug', f'{word}.html'), 'w').write(dom.prettify())

        word_info = self._parse_word_info(dom, word)
        return word_info


@dc.dataclass
class Lexeme:
    definition: str = None
    synonyms: tp.List[str] = None
    translations: tp.Dict[str, tp.List[str]] = None
    examples: tp.List[str] = None
    tags: tp.List[str] = None


@dc.dataclass
class WordInfo:
    word: str = None
    url: str = None
    pos: str = None
    lexemes: tp.List[Lexeme] = None
    morphology: tp.List[tp.Tuple[str]] = None

    def summary(self, lang=None):
        data = {
            'word': self.word,
            'url': self.url,
            'pos': self.pos,
            'definition': self.lexemes[0].definition,
            'morphology': self.morphology,
            'translations': self.lexemes[0].translations.get(lang)
        }
        result = '\n'.join([f'{k}: {v}' for k, v in data.items() if v is not None])
        return result

    def short_record(self):
        forms = [form[0] for form in self.morphology]
        if len(forms) > 2:
            p1 = os.path.commonprefix([forms[0], forms[1]])
            p2 = os.path.commonprefix([forms[0], forms[1]])
            prefix = p1 if len(p1) > len(p2) else p2
            if len(prefix) > 3:
                if forms[0] == prefix:
                    short = forms[0]
                else:
                    short = forms[0].replace(prefix, f'{prefix}/')
                for form in forms[1:]:
                    short += ', ' + form.replace(prefix, '-')
            else:
                short = ', '.join(forms)
        else:
            short = forms[0]
        return short


def _remove_eki_tags(element):
    result = ''.join([el.text for el in element.contents])
    eki_tags = ['eki-stress', 'eki-form']
    for tag in eki_tags:
        result = result.replace(f'<{tag}>', '')
        result = result.replace(f'</{tag}>', '')
    return result