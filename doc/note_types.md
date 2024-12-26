# Note Types

## Introduction

(Feel free to skip this section if you're already familiar with the concept of note type).

In Anki you don't create flash-cards directly, instead you create **notes**, which are then used to automatically generate **cards**. A **note** stores all the raw information you want to see on a card, but with no say in how this information is displayed to the user. A **card** takes that information and puts it on its front and back sides to be presented to the user. When you click "Add" in Anki's main window or in Sõnaveeb Deck Builder - you add a note, when you study the deck - you go through cards.

This separation allows to generate multiple cards for the same note. For example, one with Estonian word on the front and its translations on the back, the other with flipped sides, or yet another one with a word on the front and its definition on the back. If you update any information for a note, it automatically updates it for all cards generated from it.

The kind of the information a note may contain (fields) and how cards are generated from it is defined by a **note type**. Each note belongs to one. You can view, add, remove, or modify note types using "Tools -> Manage Note Types".

What cards are generated from a note and how they look is dictated by card templates specific to a note type. Click "Cards" in the Note Types window to view or edit card templates. There you can define how the front and the back sides of the card look with HTML/CSS. More info about card template syntax can be found on [Anki Manual](https://docs.ankiweb.net/templates/intro.html).

See also [Key Concepts chapter](https://docs.ankiweb.net/getting-started.html#key-concepts) from Anki Manual for a more comprehensive introduction to these concepts.

## Default Sõnaveeb Note Types

This addon creates the following note types by default:

- Sõnaveeb (from Estonian)
- Sõnaveeb (into Estonian)
- Sõnaveeb (bidirectional)

The first two generate 1 card per note with one-way translations from and into Estonian respectively, the last one generates both.

You cannot edit card templates for these note types (well, you can, but your changes will be reverted automatically). But you can do that if you create your own note type.

## Custom Note Types

With these you can have a full control over which cards are generated from your Sõnaveeb notes and how they look.

1. Go to "Tools -> Manage Note Types" (`Ctrl+Shift+N`).
2. Click "Add".
3. Select "Clone ..." for one of Sõnaveeb default note types, click "OK".
4. Choose any name and click "OK".

The note type should immediately show up in the drop-down list of Sõnaveeb Deck Builder dialog. On step 3 it's important to clone specifically a note type that is already supported by this addon, so that the new note type is supported too.

Now you can select it in "Note Types" window, click "Cards", and go crazy. Do not edit fields, they are enforced by the addon and it will only bother you to revert the change.

If you want to apply these changes to existing notes, change their type to yours.

## Changing Note Type of the Existing Notes

Note type of the existing notes can be changed in the note browser:

1. In the main window select the deck and click "Browse".
2. Select notes the type of which you want to change.
3. Right-click and in the context menu select "Change Note Type..." (`Ctrl+Shift+M`)
4. Select the target note type in the drop-down list in the top.
5. Make sure field and template mappings are correct (usually they are by default).
6. Click save.
