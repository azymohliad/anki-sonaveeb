import os
import re
import typing as tp
import dataclasses as dc

import requests
import bs4


BASE_URL = 'https://sonaveeb.ee'
VALID_LANGUAGE_LEVELS: tp.ClassVar = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}


@dc.dataclass
class Dictionary:
    name: str
    description: str
    url_forms: str
    url_search: str
    url_details: str


class Sonaveeb:
    DICTIONARY_TYPES: tp.Dict[str, Dictionary] = {
        'lite': Dictionary(
            name='lite',
            description='Dictionary for language learners, with simpler definitions and examples.',
            url_forms='https://sonaveeb.ee/searchwordfrag/lite/{word}',
            url_search='https://sonaveeb.ee/search/lite/dlall/{word}',
            url_details='https://sonaveeb.ee/worddetails/lite/{word_id}'
        ),
        'unif': Dictionary(
            name='unif',
            description='Comprehensive dictionary with detailed information.',
            url_forms='https://sonaveeb.ee/searchwordfrag/unif/{word}',
            url_search='https://sonaveeb.ee/search/unif/dlall/dsall/{word}',
            url_details='https://sonaveeb.ee/worddetails/unif/{word_id}'
        )
    }
    DEFAULT_DICTIONARY: str = 'unif'

    def __init__(self):
        self.session = requests.Session()
        self.select_dictionary(self.DEFAULT_DICTIONARY)

    def select_dictionary(self, dict_type: str) -> None:
        try:
            self.dictionary = self.DICTIONARY_TYPES[dict_type]
        except KeyError:
            self.dictionary = self.DICTIONARY_TYPES[self.DEFAULT_DICTIONARY]

    def _request(self, *args, **kwargs):
        resp = self.session.get(*args, **kwargs)
        if resp.status_code != 200:
            raise RuntimeError(f'Request failed: {resp.status_code}')
        return resp

    def _ensure_session(self, timeout=None):
        if 'ww-sess' not in self.session.cookies:
            self._request(BASE_URL)

    def _word_lookup_dom(self, word, timeout=None):
        self._ensure_session(timeout=timeout)
        url = self.dictionary.url_search.format(word=word)
        resp = self._request(url, timeout=timeout)
        return bs4.BeautifulSoup(resp.text, 'html.parser')

    def _word_details_dom(self, word_id, timeout=None):
        self._ensure_session(timeout=timeout)
        url = self.dictionary.url_details.format(word_id=word_id)
        resp = self._request(url, timeout=timeout)
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
        return homonyms

    def _parse_lexeme_definition(self, definition_row):
        '''Extract definition and language level from a definition row'''
        definition = None
        level = None

        if not definition_row:
            return definition, level

        # Extract language level if present
        if level := definition_row.find(class_='additional-meta', title='Keeleoskustase'):
            level = level.string.strip()
            # TODO: Is this check necessary? Are there words with invalid level value?
            if level not in VALID_LANGUAGE_LEVELS:
                level = None

        # Extract definitions
        definitions = []
        for def_entry in definition_row.find_all(id=re.compile('^definition-entry')):
            if def_text := _remove_eki_tags(def_entry.span):
                definitions.append(def_text.strip())

        if definitions:
            definition = ' '.join(definitions)

        return definition, level

    def _parse_lexeme_rection(self, match) -> tp.List[str]:
        '''Extract rection patterns from a lexeme section.

        Args:
            match: Element containing the lexeme section

        Returns:
            List of rection patterns (e.g. ["keda/mida*", "kellel + mida teha"])
        '''
        rection_div = match.find(class_='rekts-est')
        if not rection_div:
            return []

        rections = []
        for span in rection_div.find_all('span', class_='tag'):
            if span.string:
                rections.append(span.string)
        return rections

    def _parse_lexeme_translations(self, translation_panels):
        '''Extract translations from translation panels'''
        translations = {}
        for panel in translation_panels:
            if lang_code := panel.find(class_='lang-code'):
                lang = lang_code.string
                values = [
                    _remove_eki_tags(a.span.span)
                    for a in panel.find_all('a', class_='matching-word')
                ]
                if values:
                    translations[lang] = values
        return translations

    def _parse_lexeme_examples(self, match):
        '''Extract example sentences'''
        examples = []
        for example in match.find_all(class_='example-text-value'):
            if example.string:
                examples.append(example.string)
        return examples

    def _get_lexeme_number(self, match, fallback_number):
        '''Get lexeme number from match or use fallback'''
        if lexeme_number := match.find(class_='lexeme-level'):
            return lexeme_number.string
        return str(fallback_number)

    def _parse_word_info(self, dom):
        info = WordInfo()

        # Get the word_id from the url
        if word_id_input := dom.find('input', id='selected-word-homonym-nr'):
            info.word_id = word_id_input['value']

        # Get basic word info
        if homonym_name := dom.find(class_='homonym-name'):
            info.word = homonym_name.span.string

        if word_class_tag := dom.find(class_='content-title').find(class_='tag'):
            info.word_class = word_class_tag.string

        # Initialize lexemes list
        info.lexemes = []

        # Find specific word-details div for this homonym
        dom_to_parse = dom
        if info.word_id:
            if word_details := dom.find('div', attrs={'data-homonymnr': info.word_id}):
                dom_to_parse = word_details

        # Parse each lexeme section
        sequential_number = 1
        for match in dom_to_parse.find_all(id=re.compile('^lexeme-section')):
            # Get lexeme number
            number = self._get_lexeme_number(match, sequential_number)
            sequential_number += 1

            # Skip sub-definitions
            if number and '.' in number:
                continue

            # Parse lexeme details
            definition, level = self._parse_lexeme_definition(match.find(class_='definition-row'))
            translations = self._parse_lexeme_translations(
                match.find_all(id=re.compile('^matches-show-more-panel'))
            )
            examples = self._parse_lexeme_examples(match)
            rection = self._parse_lexeme_rection(match)
            tags = [t.string for t in match.find_all(class_='tag') if t.string]
            synonyms = [
                a.span.span.string
                for a in match.find_all('a', class_='synonym')
                if a.span and a.span.span
            ]

            # Create lexeme object
            lexeme = Lexeme(
                definition=definition,
                rection=rection,
                synonyms=synonyms,
                translations=translations,
                examples=examples,
                tags=tags,
                number=number,
                level=level,
            )

            info.lexemes.append(lexeme)

        # Parse morphology
        info.morphology = []
        if morphology_paradigm := dom_to_parse.find(class_='morphology-paradigm'):
            if morphology_table := morphology_paradigm.find('table'):
                for row in morphology_table.find_all('tr'):
                    cells = row.find_all('span', class_='form-value-field')
                    if cells:
                        entry = tuple(_remove_eki_tags(c) for c in cells)
                        info.morphology.append(entry)

        return info

    def get_forms(self, word, timeout=None):
        self._ensure_session(timeout=timeout)
        url = self.dictionary.url_forms.format(word=word)
        resp = self._request(url, timeout=timeout)
        data = resp.json()
        forms = data['formWords']
        match = word if word in data['prefWords'] else None
        return match, forms

    def get_candidates(self, word, lang='et', timeout=None, debug=False):
        # Request word lookup page
        dom = self._word_lookup_dom(word, timeout=None)
        # Save HTML page for debugging
        if debug:
            open(os.path.join('debug', f'lookup_{word}.html'), 'w').write(dom.prettify())
        # Parse results
        homonyms = self._parse_search_results(dom, lang=lang)
        return homonyms

    def get_word_info_by_candidate(self, candidate, timeout=None, debug=False):
        # Request word details page
        dom = self._word_details_dom(candidate.word_id, timeout=timeout)

        # Save HTML page for debugging
        if debug:
            open(os.path.join('debug', f'details_{candidate.name}.html'), 'w').write(dom.prettify())

        # Parse results
        word_info = self._parse_word_info(dom)
        word_info.word_id = candidate.word_id
        word_info.url = candidate.url
        return word_info

    def get_word_info(self, word, lang='et', timeout=None, debug=False):
        match, forms = self.get_forms(word, timeout=timeout)
        if match is None and len(forms) == 0:
            return None
        word = forms[0] if match is None else match
        homonyms = self.get_candidates(word, lang, timeout, debug)
        if len(homonyms) == 0:
            return None
        return self.get_word_info_by_candidate(homonyms[0], timeout, debug)


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
    rection: tp.List[str] = None
    synonyms: tp.List[str] = None
    translations: tp.Dict[str, tp.List[str]] = dc.field(default_factory=dict)
    examples: tp.List[str] = None
    tags: tp.List[str] = None
    number: str = None
    level: str = None


@dc.dataclass
class WordInfo:
    word_id: int = None
    word: str = None
    word_class: str = None
    url: str = None
    lexemes: tp.List[Lexeme] = None
    morphology: tp.List[tp.Tuple[str]] = None

    def summary(self, lang=None):
        data = {
            'word_id': self.word_id,
            'word': self.word,
            'word_class': self.word_class,
            'url': self.url,
            'short_record': self.short_record(),
            'morphology': self.morphology,
            'lexemes': self.lexemes,
        }
        result = '\n'.join([f'{k}: {v}' for k, v in data.items() if v is not None])
        return result

    def short_record(self):
        forms = [form[0] for form in self.morphology if len(form) > 0]
        if len(forms) > 2:
            p1 = os.path.commonprefix([forms[0], forms[1]])
            p2 = os.path.commonprefix([forms[0], forms[1]])
            prefix = p1 if len(p1) > len(p2) else p2
            if len(prefix) > 3 or prefix == forms[0]:
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
    if not element:
        return ''

    result = ''.join(el.text for el in element.contents if el)

    # Clean up common tags
    eki_tags = ['eki-stress', 'eki-form']
    for tag in eki_tags:
        result = result.replace(f'<{tag}>', '')
        result = result.replace(f'</{tag}>', '')

    return result.strip()
