import os
import re
import enum
import logging
import typing as tp
import dataclasses as dc

import requests
import bs4


# Essential to study forms per word class (part of speech).
# For word classes not listed here only the first form is used.
ESSENTIAL_FORMS_BY_CLASS = dict(
    nimisõna=['ainsuse nimetav', 'ainsuse omastav', 'ainsuse osastav', 'mitmuse osastav'],
    omadussõna=['ainsuse nimetav', 'ainsuse omastav', 'ainsuse osastav', 'mitmuse osastav'],
    mitmus=['mitmuse nimetav', 'mitmuse omastav', 'mitmuse osastav'],
    tegusõna=['ma-tegevusnimi', 'da-tegevusnimi', 'kindla kõneviisi oleviku ainsuse 3.p.'],
)


def compress_word_forms(forms: tp.List[str]) -> tp.List[str]:
    '''Shortens word forms by deduplicating a common part.

    For example: [suur, suure, suurt] -> [suur, -e, -t].
    '''
    prefix = os.path.commonprefix(forms)
    if len(prefix) > 3 or prefix == forms[0]:
        # The prefix is long enough or contains full 1st form (e.g. öö) - compress.
        compressed = []
        if forms[0] == prefix:
            compressed.append(forms[0])
        else:
            compressed.append(forms[0].replace(prefix, f'{prefix}/'))
        compressed.extend([f.replace(prefix, '-') for f in forms[1:]])
        return compressed
    else:
        # The prefix is too short - return as is.
        return forms


class SonaveebMode(enum.Enum):
    Lite = 0
    Advanced = 1


@dc.dataclass
class LexemeInfo:
    definition: str = None
    rection: tp.List[str] = dc.field(default_factory=list)
    synonyms: tp.List[str] = dc.field(default_factory=list)
    translations: tp.Dict[str, tp.List[str]] = dc.field(default_factory=dict)
    examples: tp.List[str] = dc.field(default_factory=list)
    tags: tp.List[str] = dc.field(default_factory=list)
    number: str = None
    level: str = None


@dc.dataclass
class WordInfo:
    word_id: int = None
    word: str = None
    word_class: str = None
    word_audio_url: str = None
    url: str = None
    lexemes: tp.List[LexemeInfo] = None
    morphology: tp.Dict[str, str] = dc.field(default_factory=dict)
    morphology_audio_urls: tp.Dict[str, str] = dc.field(default_factory=dict)

    def __post_init__(self):
        # Validate present form types
        if missing_forms := self.missing_form_types():
            logging.error(
                'Missing expected forms for the word '
                f'"{self.word}" [##{self.word_id}]: {missing_forms}'
            )

    def audio_urls(self) -> tp.List[str]:
        '''Returns a list audio URLs corresponding to essential_forms list.

        Not every form is guaranteed to have an audio, but every audio is
        guaranteed to be one of the essential forms.
        '''
        keys = self.present_form_types()
        urls = [self.morphology_audio_urls.get(key) for key in keys]
        urls = [u for u in urls if u is not None]
        if not urls and self.word_audio_url is not None:
            urls = [self.word_audio_url]
        return urls

    def essential_forms(self, compress=False, join=False) -> tp.Union[tp.List[str], str]:
        '''Returns a list of essential to study forms of this word.

        Args:
            compress: avoid repeating a common part in every form, replace it with "-".
                Unless it's too short. For example: [suur, suure, suurt] -> [suur, -e, -t].
            join: return comma-separated string instead of a list.
        Returns:
            A list or a comma-separated string of word forms.
        '''
        keys = self.present_form_types()
        if keys:
            forms = [self.morphology[key] for key in keys]
        else:
            forms = [self.word]
        if compress:
            forms = compress_word_forms(forms)
        if join:
            forms = ', '.join(forms)
        return forms

    def present_form_types(self) -> tp.List[str]:
        '''Returns essential form names that are present for this word.

        It is expected that all essential forms for the word class
        would be present, unless there's a parsing bug or Sõnaveeb inconsistency.
        '''
        keys = ESSENTIAL_FORMS_BY_CLASS.get(self.word_class, [])
        return [k for k in keys if k in self.morphology]

    def missing_form_types(self) -> tp.List[str]:
        '''Returns essential form names that are missing for this word.

        A non-empty list indicates either a parsing bug or Sõnaveeb inconsistency.
        '''
        keys = ESSENTIAL_FORMS_BY_CLASS.get(self.word_class, [])
        return [k for k in keys if k not in self.morphology]


@dc.dataclass
class WordReference:
    word_id: int
    url: str
    lang: str
    name: str = None
    matches: str = None
    summary: str = None


@dc.dataclass
class LookupUrls:
    forms: str
    search: str
    details: str


class Sonaveeb:
    '''Sonaveeb API wrapper.

    There are two ways of using it:
    - High-level API: simply
    '''
    BASE_URL = 'https://sonaveeb.ee'
    MODE_URLS = {
        SonaveebMode.Lite: LookupUrls(
            forms='https://sonaveeb.ee/searchwordfrag/lite/{word}',
            search='https://sonaveeb.ee/search/lite/dlall/{word}',
            details='https://sonaveeb.ee/worddetails/lite/{word_id}'
        ),
        SonaveebMode.Advanced: LookupUrls(
            forms='https://sonaveeb.ee/searchwordfrag/unif/{word}',
            search='https://sonaveeb.ee/search/unif/dlall/eki/{word}',
            details='https://sonaveeb.ee/worddetails/unif/{word_id}'
        )
    }
    DEFAULT_MODE = SonaveebMode.Lite

    def __init__(self):
        self.session = requests.Session()
        self.set_mode(self.DEFAULT_MODE)

    def set_mode(self, mode: SonaveebMode) -> None:
        '''Set Sõnaveeb mode.'''
        self.urls = self.MODE_URLS[mode]
        self.mode = mode

    def get_base_form(self, word: str, timeout=None) -> tp.Tuple[str, tp.List[str]]:
        '''Search for a base form of a requested word.

        Args:
            word: Estonian word in any form.

        Returns: tuple
            exact_match: The query word itself if it was in its
                base form already or None.
            base_forms: list of words in their base forms, a form
                of which the query word could be.
        '''
        self._ensure_session(timeout=timeout)
        url = self.urls.forms.format(word=word)
        resp = self._request(url, timeout=timeout)
        data = resp.json()
        base_forms = data['formWords']
        exact_match = word if word in data['prefWords'] else None
        return exact_match, base_forms

    def get_references(self, base_form: str, lang='et', timeout=None, debug=False) -> tp.List[WordReference]:
        '''Get a list of references for all homonyms of the word.

        Args:
            base_form: Estonian word in its base form.

        Returns:
            references: List of WordReference objects.
        '''
        # Request word lookup page
        dom = self._word_lookup_dom(base_form, timeout=None)
        # Save HTML page for debugging
        if debug:
            open(os.path.join('debug', f'lookup_{base_form}.html'), 'w').write(dom.prettify())
        # Parse results
        references = self._parse_search_results(dom, lang=lang)
        return references

    def get_word_info_by_reference(self, reference: WordReference, timeout=None, debug=False):
        '''Get word info from word reference.

        Args:
            reference: WordReference object.

        Returns:
            word_info: WordInfo object.
        '''
        # Request word details page
        dom = self._word_details_dom(reference.word_id, timeout=timeout)

        # Save HTML page for debugging
        if debug:
            open(os.path.join('debug', f'details_{reference.name}.html'), 'w').write(dom.prettify())

        # Parse results
        word_info = self._parse_word_info(dom)
        word_info.word_id = reference.word_id
        word_info.url = reference.url
        return word_info

    def get_word_info(self, word: str, lang='et', timeout=None, debug=False):
        '''Get word info for the first matching homonym of a requested word.

        This is a high-level API that performs end-to-end search from a
        query word to `WordInfo` object. It is the simplest API to use, but
        it doesn't allow to select a base form word and homonym if there
        are multiple.

        Args:
            word: Estonian word in any form.

        Returns:
            word_info: WordInfo object.
        '''
        match, forms = self.get_base_form(word, timeout=timeout)
        if match is None and len(forms) == 0:
            return None
        word = forms[0] if match is None else match
        homonyms = self.get_references(word, lang, timeout, debug)
        if len(homonyms) == 0:
            return None
        return self.get_word_info_by_reference(homonyms[0], timeout, debug)

    def _request(self, *args, **kwargs):
        resp = self.session.get(*args, **kwargs)
        if resp.status_code != 200:
            raise RuntimeError(f'Request failed: {resp.status_code}')
        return resp

    def _ensure_session(self, timeout=None):
        if 'ww-sess' not in self.session.cookies:
            self._request(self.BASE_URL)

    def _word_lookup_dom(self, word, timeout=None):
        self._ensure_session(timeout=timeout)
        url = self.urls.search.format(word=word)
        resp = self._request(url, timeout=timeout)
        return bs4.BeautifulSoup(resp.text, 'html.parser')

    def _word_details_dom(self, word_id, timeout=None):
        self._ensure_session(timeout=timeout)
        url = self.urls.details.format(word_id=word_id)
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
                kwargs['url'] = self.BASE_URL + '/' + url['value']
            if language := homonym.find(class_='lang-code'):
                kwargs['lang'] = language.string
            if name := homonym.find(class_='homonym-name'):
                kwargs['name'] = name.span.string
            if matches := homonym.find(class_='homonym-matches'):
                kwargs['matches'] = matches.string
            if summary := homonym.find(class_='homonym-intro'):
                kwargs['summary'] = summary.string
            homonyms.append(WordReference(**kwargs))
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

        # Extract definitions
        definitions = []
        for def_entry in definition_row.find_all(id=re.compile('^definition-entry')):
            if def_text := self._remove_eki_tags(def_entry.span):
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
                    self._remove_eki_tags(a.span.span)
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

        if audio_button := dom.find('div', class_='content-title').find('button', class_='btn-speaker'):
            if audio_url := audio_button.get('data-url-to-audio'):
                info.word_audio_url = self.BASE_URL + audio_url

        # Parse word class (part of speech)
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
            lexeme = LexemeInfo(
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

        # Parse morphology forms and audio URLs
        if morphology_paradigm := dom_to_parse.find(class_='morphology-paradigm'):
            if morphology_table := morphology_paradigm.find('table'):
                cells = morphology_table.find_all('span', class_='form-value-field')
                for cell in cells:
                    key = cell.get('title').split(' - ')[0]
                    value = self._remove_eki_tags(cell)
                    info.morphology[key] = value
                    if audio_button := cell.find_next_sibling('button', class_='btn-speaker'):
                        if audio_url := audio_button.get('data-url-to-audio'):
                            info.morphology_audio_urls[key] = self.BASE_URL + audio_url

        # Get audio URLs, prioritizing morphological forms
        return info

    @staticmethod
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
