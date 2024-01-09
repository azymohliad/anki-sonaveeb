#!/usr/bin/env python

import re
import argparse
import requests
import bs4

BASE_URL = 'https://sonaveeb.ee'
SEARCH_URL = 'https://sonaveeb.ee/search/unif/dlall/dsall/{word}/1'
DETAILS_URL = 'https://sonaveeb.ee/worddetails/unif/{word_id}'


def nested_to_string(data, indent=2, level=0):
    level += 1
    prefix = ' ' * indent * level
    if isinstance(data, dict):
        result = ''
        for k, v in data.items():
            result += f'\n{prefix}{k}: {nested_to_string(v, level=level)}'
    elif isinstance(data, (list, tuple, set)):
        if not is_nested(data):
            result = ', '.join([str(v) for v in data])
            if len(result) < 80:
                return result
        result = ''
        for v in data:
            result += f'\n{prefix}{nested_to_string(v, level=level)}'
    else:
        result = str(data)
    return result


def is_nested(data):
    collections = (dict, list, tuple, set)
    if isinstance(data, collections):
        return any([isinstance(el, collections) for el in data])
    return False


def desressify(content):
    return ''.join([el.text for el in content]).replace('<eki-stress>', '').replace('</eki-stress>', '')


def remove_eki_tags(element):
    result = ''.join([el.text for el in element.contents])
    eki_tags = ['eki-stress', 'eki-form']
    for tag in eki_tags:
        result = result.replace(f'<{tag}>', '')
        result = result.replace(f'</{tag}>', '')
    return result

def get_word_id(session, word):
    resp = session.get(SEARCH_URL.format(word=word))
    html = resp.text
    dom = bs4.BeautifulSoup(html, 'html.parser')

    word_id = dom.find(attrs=dict(name='word-id'))
    if word_id is not None:
        word_id = word_id['value']
    return word_id, dom

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Anki Sonaveeb')
    parser.add_argument('word')
    parser.add_argument('--save-details-page', action='store_true')
    args = parser.parse_args()

    session = requests.Session()
    resp = session.get(BASE_URL)

    word = args.word
    word_id, dom = get_word_id(session, word)
    if word_id is None:
        forms = [a['data-word'] for a in dom.find(class_='word-details').find_all('a', 'word-form')]
        word = forms[0]
        word_id, _ = get_word_id(session, word)
    # print(f'Word ID: {word} = {word_id}')

    resp = session.get(DETAILS_URL.format(word_id=word_id))
    html = resp.text
    soup = bs4.BeautifulSoup(html, 'html.parser')

    if args.save_details_page:
        with open(f'{word}.html', 'w') as f:
            f.write(soup.prettify())

    data = {}
    data['word'] = soup.find(class_='homonym-name').span.string
    data['url'] = SEARCH_URL.format(word=word)
    data['part_of_speech'] = soup.find(class_='content-title').find(class_='tag').string
    entries = []
    for match in soup.find_all(id=re.compile('^lexeme-section')):
        try:
            entry = {}
            definition = match.find(id=re.compile('^definition-entry'))
            if definition is not None:
                entry['definition'] = remove_eki_tags(definition.span)
            entry['tags'] = [t.string for t in match.find_all(class_='tag')]
            entry['synonyms'] = [a.span.span.string for a in match.find_all('a', class_='synonym')]
            translations = {}
            for translation in match.find_all(id=re.compile('^matches-show-more-panel')):
                lang = translation.find(class_='lang-code')['title']
                values = [remove_eki_tags(a.span.span) for a in translation.find_all('a', class_='matching-word')]
                translations[lang] = values
            entry['translations'] = translations
            entry['examples'] = [s.string for s in match.find_all(class_='example-text-value')]
            entries.append(entry)
        except Exception as e:
            print(e)
    data['matches'] = entries

    morphology = []
    motphology_table = soup.find(class_='morphology-paradigm').find('table')
    for row in motphology_table.find_all('tr'):
        for cell in row.find_all('td'):
            if cell.span:
                morphology.append(remove_eki_tags(cell.span))
    data['morphology'] = morphology

    simplified = dict(
        word=data['word'],
        url=data['url'],
        part_of_speech=data['part_of_speech'],
        morphology=data['morphology'][::2],
        definition=data['matches'][0].get('definition'),
        translation=data['matches'][0]['translations']['ukraina'],
    )

    print(nested_to_string(simplified))
    # print(nested_to_string(data))



