import anki.errors
from aqt.qt import (
    Qt, QSizePolicy,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedWidget,QGroupBox, QMessageBox,
)
from aqt.operations import QueryOp
from aqt.theme import theme_manager
from aqt import mw, colors

from ..note_type import find_note_type, verify_note_type, add_note_type
from ..gtranslate import cross_translate


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
        self._note_type_id = None
        self._sonaveeb = sonaveeb
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

    def set_translations(self, translations, external=False, limit=3):
        if len(translations) == 0:
            self._translations_status.setText('Translations unavailable')
            self._translations_status.show()
            self._add_button.setEnabled(False)
            self._replace_button.hide()
        else:
            filtered = [t.strip('!., ') for t in translations[:limit]]
            self.translations = ', '.join(filtered)
            self._translations_label.setText(self.translations)
            self._translations_label.show()
            self._translations_status.setText('Google Translated')
            self._translations_status.setVisible(external)
            self._add_button.setEnabled(True)
            self.check_note_identical()

    def set_translation_language(self, lang):
        self.lang = lang
        self._translations_label.hide()
        self._add_button.setEnabled(False)
        self._replace_button.hide()
        if self.word_info is not None:
            translations = self.word_info.lexemes[0].translations.get(self.lang)
            if translations is not None:
                self.set_translations(translations, False)
            elif len(self.word_info.lexemes[0].translations) == 0:
                self.set_translations([])
            else:
                self.request_cross_translations()

    def set_deck(self, deck_id):
        self.deck_id = deck_id
        self.check_note_exists()

    def set_status(self, status):
        self._status_label.setText(status)
        self._stack.setCurrentWidget(self._status_label)

    def set_word_info(self, data):
        self.word_info = data
        self._title_label.setText(f'<a href="{data.url}"><h3>{data.word}</h3></a>')
        self._morphology_label.setText(data.short_record())
        self._pos_label.setText(f'PoS: {data.pos}')
        self._pos_label.setVisible(data.pos is not None)
        self.set_translation_language(self.lang)
        self._stack.setCurrentWidget(self._content)

    def check_note_exists(self):
        deck = mw.col.decks.get(self.deck_id)['name']
        existing_notes = mw.col.find_notes(f'URL:"{self.word_info.url}" deck:"{deck}"')
        exists = len(existing_notes) > 0
        self._add_button.setVisible(not exists)
        self._delete_button.setVisible(exists)
        if exists:
            self.note = mw.col.get_note(existing_notes[0])
            self.check_note_identical()
        else:
            self.note = None

    def check_note_identical(self):
        if self.note is not None:
            identical = (
                self.note['Morphology'] == self.word_info.short_record() and
                self.note['Translation'] == self.translations and
                self.note['URL'] == self.word_info.url
            )
            self._replace_button.setVisible(not identical)

    def get_note_type_id(self):
        if self._note_type_id is not None:
            return self._note_type_id

        if (ntid := find_note_type()) is not None:
            if verify_note_type(ntid):
                self._note_type_id = ntid
                return ntid
            else:
                QMessageBox.warning(self, 'Malformed note type',
                    f'Note type "{mw.col.models.get(ntid)["name"]}" is malformed.'
                    ' You can try to remove it from "Tools -> Manage Note Types"')

        self._note_type_id = add_note_type()
        return self._note_type_id

    def add_note(self):
        if (ntid := self.get_note_type_id()) is not None:
            note = mw.col.new_note(ntid)
            self.fill_note(note)
            mw.col.add_note(note, self.deck_id)
            self.note = note

    def update_note(self):
        if self.note is not None:
            self.fill_note(self.note)
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
        note['Morphology'] = self.word_info.short_record()
        note['Translation'] = self.translations
        note['URL'] = self.word_info.url
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

    def request_cross_translations(self):
        self._translations_status.setText('Google translating...')
        self._translations_status.show()
        operation = QueryOp(
            parent=self,
            op=lambda col: cross_translate(
                sources=self.word_info.lexemes[0].translations,
                lang=self.lang
            ),
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

    def translations_received(self, translations):
        # As a special case, add "to" before verbs infinitives in English
        if self.lang == 'en' and self.word_info.pos == 'tegusõna':
            translations = [f'to {verb}'.replace('to to ', 'to ') for verb in translations]
        self.set_translations(translations, True)

    def add_button_clicked(self):
        self.add_note()
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

