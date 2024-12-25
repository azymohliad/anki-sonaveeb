# Note Types

## Introduction

(Feel free to skip this section if you're already familiar with the concept of note type).

In Anki you don't create flash-cards directly, instead you create **notes**, which are then used to automatically generate **cards**. A **note** stores all the information you want to see on a card, but it has no say in how this information is displayed. A **card** takes that information from its corresponding note, and formats it to be presented to the user. In other words, notes define raw information, cards define how this information is visualized. When you click "Add" in Anki's main window or in Sõnaveeb Deck Builder - you add a note, when you study the deck - you go through cards.

This separation allows to generate multiple cards for the same note. For example, one with Estonian word on the front and its translations on the back, the other with flipped sides, and let's say yet another one with a word on the front and its definition on the back. If you update any information for a note, it automatically updates it for all cards generated from it.

The exact structure of the information a note may contain (fields) and what cards are generated from it, is defined by a **note type**. Each note belongs to one. You can view, add, remove, or modify note types using "Tools -> Manage Note Types". Click "Cards" in the openned window to view or edit card templates.

## Default Sõnaveeb Note Types

This addon creates the following note types by default:

- Sõnaveeb (bidirectional)
- Sõnaveeb (from Estonian)
- Sõnaveeb (into Estonian)

As you can probably guess, the first note type generates 2 cards per note - with translations into and from Estonian respectively, and the latter two generate 1 card per note with one-way translation.

## Custom Card Templates

If you try to edit one of these default note types, your changes will be reverted on the next launch. But if you would like to modify the default card templates, you can totally do that by creating your own note type.

1. Go to "Tools -> Manage Note Types" (`Ctrl+Shift+N`).
2. Click "Add".
3. Select "Clone ..." for one of Sõnaveeb default note types, click "OK".
4. Choose any name and click "OK".

The note type should immediately show up in the drop-down list of Sõnaveeb Deck Builder dialog. Feel free to edit cards however you want, but do not edit fields.

On step 3 it's important to clone specifically a note type that is supported by this addon, so that the new note type is supported too.

## Changing Note Type of the Existing Notes

Note type of the existing notes can be changed in the note browser:

1. In the main window select the deck and click "Browse".
2. Select notes the type of which you want to change.
3. Right-click and in the context menu select "Change Note Type..." (`Ctrl+Shift+M`)
4. Select the target note type in the drop-down list in the top.
5. Make sure field and template mappings are correct (usually they are by default).
6. Click save.
