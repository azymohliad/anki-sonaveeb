import os
import re
import typing as tp
import dataclasses as dc

import requests
import bs4


BASE_URL = 'https://sonaveeb.ee'
SEARCH_URL = 'https://sonaveeb.ee/search/unif/dlall/dsall/{word}'
DETAILS_URL = 'https://sonaveeb.ee/worddetails/unif/{word_id}'


class Sonaveeb:
    def __init__(self):
        self.session = requests.Session()

    def _request(self, *args, **kwargs):
        resp = self.session.get(*args, **kwargs)
        if resp.status_code != 200:
            raise RuntimeError(f'Request failed: {resp.status_code}')
        return resp

    def _ensure_session(self):
        if 'ww-sess' not in self.session.cookies:
            self._request(BASE_URL)

    def _word_lookup_dom(self, word):
        self._ensure_session()
        resp = self._request(SEARCH_URL.format(word=word))
        return bs4.BeautifulSoup(resp.text, 'html.parser')

    def _word_details_dom(self, word_id):
        self._ensure_session()
        resp = self._request(DETAILS_URL.format(word_id=word_id))
        return bs4.BeautifulSoup(resp.text, 'html.parser')

    def _parse_search_results(self, dom, lang=None):
        # Parse homonyms list
        homonyms = []
        for homonym in dom.find_all('li', class_='homonym-list-item'):
            kwargs = {}
            if word_id := homonym.find('input', attrs=dict(name='word-id')):
                kwargs['word_id'] = word_id['value']
            if url := homonym.find('input', attrs=dict(name='word-select-url')):
                kwargs['url'] = BASE_URL + '/' + url['value']
            if language := homonym.find(class_='lang-code'):
                kwargs['lang'] = language.string
            if name := homonym.find(class_='homonym-name'):
                kwargs['name'] = name.span.string
            if matches := homonym.find(class_='homonym-matches'):
                kwargs['matches'] = matches.string
            if summary := homonym.find(class_='homonym-intro'):
                kwargs['summary'] = summary.string
            homonyms.append(SearchCandidate(**kwargs))
        # Filter by language
        if lang is not None:
            homonyms = [r for r in homonyms if r.lang == lang]
        # Parse forms
        alt_forms = [b['data-word'] for b in dom.find_all('button', class_='word-form')]
        return homonyms, alt_forms

    def _parse_word_info(self, dom):
        info = WordInfo()
        info.word = dom.find(class_='homonym-name').span.string
        if pos := dom.find(class_='content-title').find(class_='tag'):
            info.pos = pos.string
        info.lexemes = []
        for match in dom.find_all(id=re.compile('^lexeme-section')):
            lexeme = Lexeme()
            if definition := match.find(id=re.compile('^definition-entry')):
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
        if morphology_paradigm := dom.find(class_='morphology-paradigm'):
            motphology_table = morphology_paradigm.find('table')
            for row in motphology_table.find_all('tr'):
                entry = tuple((_remove_eki_tags(c.span) for c in row.find_all('td') if c.span))
                info.morphology.append(entry)
        return info

    def get_candidates(self, word, lang='et', debug=False):
        # Request word lookup page
        dom = self._word_lookup_dom(word)

        # Save HTML page for debugging
        if debug:
            open(os.path.join('debug', f'lookup_{word}.html'), 'w').write(dom.prettify())

        # Parse results
        homonyms, alt_forms = self._parse_search_results(dom, lang='et')
        return homonyms, alt_forms

    def get_word_info_by_candidate(self, candidate, debug=False):
        # Request word details page
        dom = self._word_details_dom(candidate.word_id)

        # Save HTML page for debugging
        if debug:
            open(os.path.join('debug', f'details_{candidate.name}.html'), 'w').write(dom.prettify())

        # Parse results
        word_info = self._parse_word_info(dom)
        word_info.word_id = candidate.word_id
        word_info.url = candidate.url
        return word_info

    def get_word_info(self, word, lang='et', debug=False):
        homonyms, forms = self.get_candidates(word, lang, debug)
        if len(homonyms) == 0 and len(forms) > 0:
            homonyms, forms = self.get_candidates(forms[0], lang, debug)
        if len(homonyms) > 0:
            return self.get_word_info_by_candidate(homonyms[0], debug)
        else:
            return None


@dc.dataclass
class SearchCandidate:
    word_id: int
    url: str
    lang: str
    name: str = None
    matches: str = None
    summary: str = None


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
    word_id: int = None
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
        elif len(forms) > 0:
            short = forms[0]
        else:
            short = self.word
        return short


def _remove_eki_tags(element):
    result = ''.join([el.text for el in element.contents])
    eki_tags = ['eki-stress', 'eki-form']
    for tag in eki_tags:
        result = result.replace(f'<{tag}>', '')
        result = result.replace(f'</{tag}>', '')
    return result
