# Changelog

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
