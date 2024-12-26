# Anki Sõnaveeb Integration

[🇺🇦 Українською](README_UK.md)

An [Anki](https://apps.ankiweb.net/) addon that helps creating Estonian vocabulary flashcards.

Simply type an Estonian word in any form, and generate a flashcard containing its principal forms along with translation into your preferred language, definition, examples, and other information in a few clicks.

Dictionary data is obtained from [Sõnaveeb](https://sonaveeb.ee/), with fallback to [Google Translate](https://translate.google.com) for missing translations.

![screenshot](https://github.com/user-attachments/assets/beb1ce2b-d3e6-4752-9288-01e7b6db0c75)

### About Anki

[Anki](https://apps.ankiweb.net/) is flexible and powerful platform for intelligent spaced repetition. It allows to create and study custom flashcard decks. Applications are available on all popular desktop and mobile platforms. And it is free and open source. Optionally you can [create Anki Web account](https://ankiweb.net/account/signup), sign in from your Anki apps, and it will seemlesly synchronize your decks and study progress accross your devices.

### About Sõnaveeb

[Sõnaveeb](https://sonaveeb.ee/) (WordWeb) is the language portal of the [Institute of the Estonian Language (EKI)](https://www.eki.ee/EN/) containing lexical information from a growing number of dictionaries and databases.


## Installation

### 1. Install Anki desktop app

Download it [here](https://apps.ankiweb.net/#download) for your computer.

### 2. Install Sõnaveeb Integration addon

From Anki main menu select "Tools -> Add-ons -> Get Add-ons...", paste code `1005526508`, and press "OK". Then restart Anki.


## Usage

From Anki main menu select "Tools -> Sõnaveeb Deck Builder". Set your preferred settings on the toolbar. Search words, and click "Add" to add them to your collection.

The toolbar contains the following settings:
- Deck to add your Sõnaveeb cards into.
- Note type. Out of the box it allows you to select between generating cards with translations from your language to Estonian, or from Estonian to your language, or both. But with custom note types you can have full control over which cards to generate and how they look, see more about it [here](doc/note_types.md).
- Translation language.
- Sõnaveeb Mode:
    - "Lite" gets the data from [Keeleõppija Sõnaveeb](https://sonaveeb.ee/lite). It has simpler definitions and examples, fewer lexemes, and is recommended for language learners.
    - "Advanced" gets the data from regular [Sõnaveeb](https://sonaveeb.ee/).

For more information about general Anki usage please refer to [Anki documentation](https://docs.ankiweb.net/).

## Development

To test the addon during development you can symlink or copy its directory directly into Anki's addon folder.

1. Disable upstream version of this addon if installed: "Tools -> Add-ons -> Sonaveeb Integration -> Toggle Enabled"
2. Locate Anki addon folder (`addons21`): "Tools -> Add-ons -> View Files".
3. Symlink or copy `anki_addon` directory from the repository into the located folder (under a more descriptive name for convenience).
For example, on Linux (replace the destination with the correct path):

```
ln -s ${PWD}/anki_addon /path/to/Anki2/addons21/sonaveeb
```

4. Restart Anki. `sonaveeb` should appear in the list of add-ons.

See also: [Writing Anki Add-ons](https://addon-docs.ankiweb.net/) tutorial book.

## Sõnaveeb Copyrights

The dictionary data is provided by Sõnaveeb and is a subject to [its copyrights](https://sonaveeb.ee/about#autor).
