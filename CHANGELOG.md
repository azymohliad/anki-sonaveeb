# Changelog

## v0.9.2 - 2025-04-25

- Prefer short form of plural partitive (mitmuse osastav).

## v0.9.1 - 2025-04-13

- Revert accidentally enabled nexted lexemes.

## v0.9.0 - 2025-04-13

- Add audio pronunciation support.
- Refined included word forms: add mitmuse osasatav for nouns and adjectives, remove -tud form for verbs.
- Fixed incorrect word forms for plural-only words.
- Fixed breakage after the latest Sõnaveeb update.

## v0.8.2 - 2025-01-03

- Fixed UI regressions on MacOS and native theme on other platforms.

## v0.8.1 - 2024-12-27

- Fixed crash on startup for platforms where UTF-8 is not a default file encoding.

## v0.8.0 - 2024-12-26

- Added multiple default note types to select from.
- Added support for custom user-created note types.

## v0.7.1 - 2024-12-17

- Disabled Sõnaveeb Deck Builder autolaunch at Anki startup, which was enabled for debugging and accidentally leaked into a release.

## v0.7.0 - 2024-11-27

- Added "Word ID", "Definition", "Examples", and "Rection" to note fields.
- Added definition, examples, rection, and tags to card templates.
- Added an option to select between full Sõnaveeb and Keeleõppija Sõnaveeb.
- Added language level to tags, if word comes from Keeleõppija Sõnaveeb.
- Added an option to choose between different lexemes of one homonym (for example, to create a võrk card not for Web, WWW, but for net).
- Fixed possible errors when re-triggering the search repeatedly without delays.
- Fixed incorrect translation override when changing the language while Google Translation is in progress.
- Fixed possibility to duplicate search results by pressing enter in the search bar repeatedly.

## v0.6.0 - 2024-03-06

- Fixed error when parsing morphology for some words (e.g. pidama)
- Fixed incorrectly parsed morphology for some words (e.g. meie)
- Improved short-record algorithm for short words ("öö, öö, ööd" -> "öö, -, -d"; "isa, isa, isa" -> "isa, -, -")

## v0.5.0 - 2024-03-05

- Update Sõnaveeb scrapper, fix search from conjugated forms.

## v0.4.0 - 2024-02-10

- Added "Delete" and "Replace" note buttons.
- Added a mechanism for updating card templates.
- Updated card templates: moved Sõnaveeb link to a separate button to make words more readable.
- Fixed profile switch handling.

## v0.3.0 - 2024-01-30

- Improved cross-translation algorithm.
- Fixed assymetric margins in search results.
- Fixed crash when no Internet connection.
- Fixed theme change not fully applied until restart.
- Fixed typos in some languages names.
- Fixed translations refresh when language changes.


## v0.2.0 - 2024-01-28

- Added fallback to Google Translate for missing translations.
- Added a wide selection of languages for translations.
- Use system language as default for translations.


## v0.1.0 - 2024-01-27

Initial release.
