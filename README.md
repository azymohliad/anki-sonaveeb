# Anki Sõnaveeb Integration

[🇺🇦 Українською](README_UK.md)

An [Anki](https://apps.ankiweb.net/) addon for automating Estonian vocabulary flashcards creation.

Simply type an Estonian word in any form, and generate a flashcard containing its principal forms along with translation into your preferred language, definition, examples, and other information in a few clicks.

Dictionary data is obtained from [Sõnaveeb](https://sonaveeb.ee/), with fallback to [Google Translate](https://translate.google.com) for missing translations.

![screenshot](https://github.com/azymohliad/anki-sonaveeb/assets/4020369/d1374e10-abdb-42fe-a083-47e30865b2ce)

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

From Anki main menu select "Tools -> Sõnaveeb Deck Builder". On the toolbar, select your preferred language and the deck to add notes/cards to. Search words, and click "Add note" to add them to your study deck. If notes don't appear in your deck immediately you can restart Anki or run "Tools -> Check Database".

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
