import anki.errors
from aqt.qt import (
    Qt, QSizePolicy,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedWidget,QGroupBox, QMessageBox,
)
from aqt.operations import QueryOp
from aqt.theme import theme_manager
from aqt import mw, colors

from .. import note_type as nt
from ..gtranslate import cross_translate

from .lexeme import LexemeWidget

VALID_LANGUAGE_LEVELS = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}

class WordInfoPanel(QGroupBox):
    def __init__(self, search_info, sonaveeb, deck_id, lang, parent=None):
        super().__init__(parent=parent)
        # Set state
        self.deck_id = deck_id
        self.lang = lang
        self.search_info = search_info
        self.word_info = None
        self.translations = None
        self.note = None
        self._note_type = None
        self._sonaveeb = sonaveeb
        self.max_lexemes = 3

        # Add status label
        self._status_label = QLabel()
        self._status_label.setStyleSheet(f'font-size: 16pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add content UI
        self._title_label = QLabel()
        self._title_label.setTextFormat(Qt.TextFormat.RichText)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._title_label.setOpenExternalLinks(True)
        self._morphology_label = QLabel()
        self._pos_label = QLabel()

        # Add translations
        self._translations_label = QLabel()
        self._translations_label.hide()
        self._translations_status = QLabel()
        self._translations_status.setStyleSheet(f'color: {theme_manager.var(colors.FG_SUBTLE)}')
        self._translations_status.hide()

        data_layout = QVBoxLayout()
        data_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        data_layout.addWidget(self._title_label)
        data_layout.addWidget(self._morphology_label)
        data_layout.addWidget(self._pos_label)
        data_layout.addWidget(self._translations_label)
        data_layout.addWidget(self._translations_status)

        # Add lexeme container
        self.lexeme_widget = LexemeWidget()
        data_layout.addWidget(self.lexeme_widget)

        self._add_button = QPushButton('Add')
        self._add_button.setFixedWidth(100)
        self._add_button.hide()
        self._add_button.clicked.connect(self.add_button_clicked)
        self._delete_button = QPushButton('Delete')
        self._delete_button.setFixedWidth(100)
        self._delete_button.hide()
        self._delete_button.clicked.connect(self.delete_button_clicked)
        self._replace_button = QPushButton('Replace')
        self._replace_button.setFixedWidth(100)
        self._replace_button.hide()
        self._replace_button.clicked.connect(self.replace_button_clicked)

        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        buttons_layout.addWidget(self._add_button)
        buttons_layout.addWidget(self._delete_button)
        buttons_layout.addWidget(self._replace_button)

        content_layout = QHBoxLayout()
        content_layout.addLayout(data_layout)
        content_layout.addLayout(buttons_layout)
        content_layout.setContentsMargins(10,0,10,0)

        self._content = QWidget()
        self._content.setLayout(content_layout)

        # Populate the UI
        self._stack = QStackedWidget()
        self._stack.addWidget(self._status_label)
        self._stack.addWidget(self._content)
        self._stack.setCurrentWidget(self._status_label)

        layout = QVBoxLayout()
        layout.addWidget(self._stack)
        layout.setContentsMargins(10,0,10,0)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        # Request word info
        self.request_word_info()

    def _on_lexeme_selected(self, index: int, checked: bool) -> None:
        """Handle lexeme selection"""
        if checked:
            self.selected_lexeme = index
            # Update translations display for the selected lexeme
            if hasattr(self, 'lexeme_translations') and index < len(self.lexeme_translations):
                translations = self.lexeme_translations[index]
                if translations:
                    self.translations = ', '.join(translations)
                    self._translations_label.setText(self.translations)
                    self._translations_label.show()
                    self.check_note_identical()

    def set_translations(self, translations, lexeme_index=0, external=False, limit=3):
        if not hasattr(self, 'lexeme_translations'):
            self.lexeme_translations = []

        # Ensure we have enough slots for translations
        while len(self.lexeme_translations) <= lexeme_index:
            self.lexeme_translations.append(None)

        if len(translations) == 0:
            self.lexeme_translations[lexeme_index] = None
            if all(t is None for t in self.lexeme_translations[:self.max_lexemes]):
                self._translations_status.setText('Translations unavailable')
                self._translations_status.show()
                self._add_button.setEnabled(False)
                self._replace_button.hide()
        else:
            filtered = [t.strip('!., ') for t in translations[:limit]]
            self.lexeme_translations[lexeme_index] = filtered

            # Format all available translations
            all_translations = []
            for i, trans in enumerate(self.lexeme_translations[:self.max_lexemes]):
                if trans:
                    all_translations.append(f"{i+1}. {', '.join(trans)}")

            # Update display
            self.translations = '\n'.join(all_translations)
            self._translations_label.setText(self.translations)
            self._translations_label.show()
            self._translations_status.setText('Google Translated' if external else '')
            self._translations_status.setVisible(external)
            self._add_button.setEnabled(True)
            self.check_note_identical()

    def set_translation_language(self, lang):
        self.lang = lang
        self._translations_label.hide()
        self._add_button.setEnabled(False)
        self._replace_button.hide()
        self.lexeme_translations = []

        if self.word_info is not None:
            has_translations = False
            for i, lexeme in enumerate(self.word_info.lexemes[:self.max_lexemes]):
                translations = lexeme.translations.get(self.lang)
                if translations is not None:
                    self.set_translations(translations, i, False)
                    has_translations = True
                elif len(lexeme.translations) == 0:
                    self.set_translations([], i)
                else:
                    self.request_cross_translations(i)
                    has_translations = True

            if not has_translations:
                self._translations_status.setText('No translations available')
                self._translations_status.show()
                self._add_button.setEnabled(False)

    def set_deck(self, deck_id):
        self.deck_id = deck_id
        if self.word_info is not None:
            self.check_note_exists()

    def set_status(self, status):
        self._status_label.setText(status)
        self._stack.setCurrentWidget(self._status_label)

    def set_word_info(self, data):
        """Set word information and update display"""
        self.word_info = data
        self._title_label.setText(f'<a href="{data.url}"><h3>{data.word}</h3></a>')
        self._morphology_label.setText(data.short_record())
        self._pos_label.setText(f'PoS: {data.pos}')
        self._pos_label.setVisible(data.pos is not None)

        # Update lexeme display
        self.lexeme_widget.update(data.lexemes, self._on_lexeme_selected)

        # Reset translations
        self.lexeme_translations = []
        self.set_translation_language(self.lang)

        self._stack.setCurrentWidget(self._content)
        self.check_note_exists()

    def check_note_exists(self):
        """Check if note exists, checking Word ID for modern cards and URL for legacy ones"""
        if self.word_info is None:
            return

        deck = mw.col.decks.get(self.deck_id)['name']

        # First try to find by Word ID (modern cards)
        if self.word_info.word_id:
            word_id_notes = mw.col.find_notes(f'"Word ID:{self.word_info.word_id}" deck:"{deck}"')
            if word_id_notes:
                self.note = mw.col.get_note(word_id_notes[0])
                self._add_button.hide()
                self._delete_button.show()
                self.check_note_identical()
                return

        # Fall back to URL check for legacy cards
        if self.word_info.url:
            url_notes = mw.col.find_notes(f'URL:"{self.word_info.url}" deck:"{deck}"')
            if url_notes:
                self.note = mw.col.get_note(url_notes[0])
                self._add_button.hide()
                self._delete_button.show()
                self._replace_button.show()  # Always show replace for legacy cards
                return

        # No existing note found
        self.note = None
        self._add_button.show()
        self._delete_button.hide()
        self._replace_button.hide()

    def check_note_identical(self):
        """Check if note content matches current selection"""
        if (self.note is not None and
            hasattr(self, 'selected_lexeme') and
            self.word_info.lexemes):

            lexeme = self.word_info.lexemes[self.selected_lexeme]
            has_word_id = 'Word ID' in self.note.keys()

            # Legacy notes without Word ID always show replace button
            if not has_word_id:
                self._replace_button.show()
                return

            # For notes with Word ID, check all fields match
            identical = all([
                self.note['Word ID'] == self.word_info.word_id,
                self.note['Morphology'] == self.word_info.short_record(),
                self.note['Translation'] == self.translations,
                self.note['URL'] == self.word_info.url,
                self.note['Definition'] == lexeme.definition,
            ])

            if lexeme.examples:
                identical = identical and bool(self.note['Examples'])

            self._replace_button.setVisible(not identical)

    def get_note_type(self):
        if self._note_type is None:
            if (ntype := nt.find_user_note_type()) is not None:
                nt.validate_note_type(ntype)
                self._note_type = ntype['id']
            elif (ntype := nt.find_default_note_type()) is not None:
                nt.validate_note_type(ntype)
                self._note_type = ntype['id']
            else:
                self._note_type = nt.add_default_note_type()
        return self._note_type

    def add_note(self):
        ntype = self.get_note_type()
        note = mw.col.new_note(ntype)
        self.fill_note(note)
        mw.col.add_note(note, self.deck_id)
        self.note = note

    def update_note(self):
        if self.note is not None:
            self.fill_note(self.note)
            self.note.flush()  # Ensure field updates are saved
            mw.col.update_note(self.note, self.deck_id)

    def delete_note(self):
        if self.note is not None:
            results = mw.col.remove_notes([self.note.id])
            if results.count == 0:
                raise RuntimeError(
                    'Your database appears to be in an inconsistent state.'
                    ' Please use the Check Database action.')
            else:
                self.note = None

    def fill_note(self, note):
        """Fill note with current lexeme data"""
        note['Word ID'] = self.word_info.word_id
        note['Morphology'] = self.word_info.short_record()
        note['URL'] = self.word_info.url

        if hasattr(self, 'selected_lexeme') and self.word_info.lexemes:
            lexeme = self.word_info.lexemes[self.selected_lexeme]

            if hasattr(self, 'translations') and self.translations:
                note['Translation'] = self.translations

            if lexeme.definition:
                note['Definition'] = lexeme.definition

            if lexeme.examples:
                examples = [ex for ex in lexeme.examples[:3] if ex is not None]
                if examples:
                    note['Examples'] = '<br>'.join(f"{ex}" for ex in examples)

            if lexeme.level and lexeme.level.upper() in VALID_LANGUAGE_LEVELS:
                note.add_tag(lexeme.level.upper())

        if self.word_info.pos is not None:
            note.add_tag(self.word_info.pos)

    def request_word_info(self):
        self.set_status('Loading...')
        operation = QueryOp(
            parent=self,
            op=lambda col: self._sonaveeb.get_word_info_by_candidate(self.search_info),
            success=self.word_info_received
        ).failure(self.handle_word_request_error)
        operation.run_in_background()

    def request_cross_translations(self, lexeme_index):
        self._translations_status.setText('Google translating...')
        self._translations_status.show()
        operation = QueryOp(
            parent=self,
            op=lambda col: (lexeme_index, cross_translate(
                sources=self.word_info.lexemes[lexeme_index].translations,
                lang=self.lang
            )),
            success=self.translations_received
        ).failure(self.handle_translations_request_error)
        operation.run_in_background()

    def handle_word_request_error(self, error):
        print(error)
        self.set_status('Error :(')

    def handle_translations_request_error(self, error):
        print(error)
        self._translations_status.setText('Failed to translate :(')
        self._translations_status.show()

    def word_info_received(self, word_info):
        if word_info is None:
            self.set_status('Failed to obtain word info :(')
        else:
            self.set_word_info(word_info)
            self.check_note_exists()

    def translations_received(self, result):
        lexeme_index, translations = result
        # As a special case, add "to" before verbs infinitives in English
        if self.lang == 'en' and self.word_info.pos == 'tegusõna':
            translations = [f'to {verb}'.replace('to to ', 'to ') for verb in translations]
        self.set_translations(translations, lexeme_index, True)

    def add_button_clicked(self):
        try:
            self.add_note()
        except nt.NoteTypeError as exc:
            QMessageBox.warning(self, 'Malformed note type',
                f'Note type "{exc.note_type["name"]}" is malformed. You can'
                ' remove or rename it from "Tools -> Manage Note Types", and'
                ' the default one will be recreated automatically'
            )
        else:
            self._add_button.hide()
            self._delete_button.show()

    def delete_button_clicked(self):
        try:
            self.delete_note()
        except RuntimeError as e:
            QMessageBox.warning(self, 'Failed to delete the note', str(e))
        else:
            self._add_button.show()
            self._delete_button.hide()
            self._replace_button.hide()

    def replace_button_clicked(self):
        try:
            self.update_note()
        except anki.errors.NotFoundError as e:
            QMessageBox.warning(self, 'Failed to update the note', str(e))
        else:
            self._replace_button.hide()

