import anki.errors
from aqt.qt import (
    Qt, QSizePolicy, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedWidget, QGroupBox, QMessageBox, pyqtSignal
)
from aqt.operations import QueryOp
from aqt.theme import theme_manager
from aqt import mw, colors

from ..notetypes import NoteTypeManager
from ..globals import (
    REQUEST_TIMEOUT,
    TRANSLATIONS_LIMIT,
    EXAMPLES_LIMIT,
    LEXEMES_LIMIT,
)


from .lexeme import LexemesContainer, LexemeWidget
from ..audio import Audio
from .audio_control import AudioControl


class WordInfoPanel(QGroupBox):
    translations_requested = pyqtSignal(bool)

    def __init__(self, word_reference, sonaveeb, deck_id, notetype, lang, parent=None):
        super().__init__(parent=parent)
        # Set state
        self.deck_id = deck_id
        self.notetype = notetype
        self.lang = lang
        self.word_reference = word_reference
        self.word_info = None
        self.note = None
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
        self._morphology_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self._class_label = QLabel()
        self._class_label.setTextFormat(Qt.TextFormat.MarkdownText)

        # Add lexeme container
        self._lexemes_container = LexemesContainer(
            lexemes_limit=LEXEMES_LIMIT,
            examples_limit=EXAMPLES_LIMIT,
            translations_limit=TRANSLATIONS_LIMIT
        )
        self._lexemes_container.lexeme_selected.connect(self._on_lexeme_selected)
        self._lexemes_container.translations_updated.connect(self._on_translations_updated)
        self._lexemes_container.translations_requested.connect(self.translations_requested)

        self._add_button = QPushButton('Add')
        self._add_button.setFixedWidth(100)
        self._add_button.hide()
        self._add_button.clicked.connect(self._on_add_button_clicked)
        self._delete_button = QPushButton('Delete')
        self._delete_button.setFixedWidth(100)
        self._delete_button.hide()
        self._delete_button.clicked.connect(self._on_delete_button_clicked)
        self._replace_button = QPushButton('Replace')
        self._replace_button.setFixedWidth(100)
        self._replace_button.hide()
        self._replace_button.clicked.connect(self._on_replace_button_clicked)

        data_layout = QVBoxLayout()
        data_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        data_layout.addWidget(self._title_label)
        data_layout.addWidget(self._morphology_label)
        data_layout.addWidget(self._class_label)

        # Add audio buttons
        self._audio_button_layout = QHBoxLayout()

        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        buttons_layout.addWidget(self._add_button)
        buttons_layout.addWidget(self._delete_button)
        buttons_layout.addWidget(self._replace_button)
        buttons_layout.addLayout(self._audio_button_layout)

        header_layout = QHBoxLayout()
        header_layout.addLayout(data_layout)
        header_layout.addLayout(buttons_layout)
        header_layout.setContentsMargins(0,0,0,0)

        content_layout = QVBoxLayout()
        content_layout.addLayout(header_layout)
        content_layout.addWidget(self._lexemes_container)
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
        self.set_notetype(notetype)
        self.request_word_info()

        # Initialize audio handler
        self.audio = Audio(
            base_url=sonaveeb.BASE_URL,
            request_timeout=REQUEST_TIMEOUT
        )

        # Initialize audio UI
        self.audio_control = AudioControl(self.audio)
        self._audio_button_layout.addWidget(self.audio_control)

    def set_translation_language(self, lang):
        '''Set translation language.

        Args:
            lang: Target language code
        '''
        self.lang = lang
        self._add_button.setEnabled(False)
        self._replace_button.hide()
        self._lexemes_container.set_translation_language(lang)

    def set_deck_id(self, deck_id):
        '''Set deck ID.'''
        self.deck_id = deck_id
        if self.word_info is not None:
            self.check_note_exists()

    def set_notetype(self, notetype):
        self.notetype = notetype
        ok = notetype is not None
        tooltip = None if ok else 'Note type is missing!'
        self._add_button.setEnabled(ok)
        self._add_button.setToolTip(tooltip)
        self._replace_button.setEnabled(ok)
        self._replace_button.setToolTip(tooltip)
        self.check_note_identical()

    def set_status(self, status):
        '''Set status message.'''
        self._status_label.setText(status)
        self._stack.setCurrentWidget(self._status_label)

    def set_word_info(self, data):
        '''Set word information and update display.'''
        self.word_info = data
        # Update content
        self._title_label.setText(f'<a href="{data.url}"><h3>{data.word}</h3></a>')
        self._morphology_label.setText(f'**Forms**: {data.short_record()}')
        self._class_label.setText(f'**Class**: {data.word_class}')
        self._class_label.setVisible(data.word_class is not None)
        self._lexemes_container.set_data(data.lexemes, data.word_class)
        self._stack.setCurrentWidget(self._content)
        # Request translations
        self.set_translation_language(self.lang)
        # Update buttons state
        self.check_note_exists()

        # Update audio UI state
        self.audio_control.update_state(
            urls=data.audio_urls,
            word=data.word,
            word_id=data.word_id,
            note=self.note
        )

    def check_note_exists(self):
        '''Check if note for the current word exists.

        Change visibility of add and delete buttons accordingly.
        '''
        if self.word_info is None:
            return
        # Search note by Word ID (modern notes)
        deck = mw.col.decks.get(self.deck_id)['name']
        query = f'"Word ID:{self.word_info.word_id}" deck:"{deck}"'
        notes = mw.col.find_notes(query)
        if not notes:
            # Fallback to search by URL (legacy notes)
            query = f'URL:"{self.word_info.url}" deck:"{deck}"'
            notes = mw.col.find_notes(query)
        exists = len(notes) > 0
        if exists:
            self.note = mw.col.get_note(notes[0])
        # Update buttons visibility
        self._add_button.setVisible(not exists)
        self._delete_button.setVisible(exists)
        self.check_note_identical()
        self.check_note_audio()

    def check_note_audio(self):
        '''Update audio UI state'''
        urls = self.word_info.audio_urls if self.word_info else []
        word = self.word_info.word if self.word_info else ""
        word_id = self.word_info.word_id if self.word_info else 0

        self.audio_control.update_state(
            urls=urls,
            word=word,
            word_id=word_id,
            note=self.note
        )

    def check_note_identical(self):
        '''Check if existing note fully matches the current word info and selected note type.

        Change visibility of the replace button accordingly.
        '''
        # TODO: Split into functions:
        # - Check content equality - return bool
        # - Check note type eqality - return bool
        # - Update buttons visibility
        exists = self.note is not None
        if exists:
            if len(set(NoteTypeManager.FIELDS) - set(self.note.keys())) > 0:
                # Notes that lack any field are considered outdated
                identical = False
            else:
                # Otherwise check if all fields match
                fields, _ = self.note_content()
                identical = all([self.note[k] == v for k, v in fields.items()])
                # Check if note type matches
                identical &= self.note.mid == self.notetype.get('id')
        # Update button visibility
        self._replace_button.setVisible(exists and not identical)

    def add_note(self):
        '''Add a new note to the collection'''
        note = mw.col.new_note(self.notetype)
        self.fill_note(note)
        mw.col.add_note(note, self.deck_id)
        self.note = note

    def update_note(self):
        '''Update an existing note with current data'''
        if self.note is not None:
            # Update note content
            # TODO: Check if note content is different
            self.fill_note(self.note)
            mw.col.update_note(self.note)
            # Update note type if needed
            old_ntid = self.note.mid
            new_ntid = self.notetype.get('id')
            if old_ntid != new_ntid:
                info = mw.col.models.change_notetype_info(old_notetype_id=old_ntid, new_notetype_id=new_ntid)
                request = info.input
                print(request.note_ids)
                request.note_ids.extend([self.note.id])
                mw.col.models.change_notetype_of_notes(request)
            # Re-read updated note from DB
            self.note = mw.col.get_note(self.note.id)

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
        '''Fill note with current lexeme data'''
        fields, tags = self.note_content()
        for key, value in fields.items():
            note[key] = value
        for tag in tags:
            note.add_tag(tag)

    def note_content(self):
        '''Derive fields and tags values for the note to be created'''
        lexeme_widget = self._lexemes_container.get_selected_widget()
        lexeme = lexeme_widget.lexeme
        # Populate fields
        fields = {
            'Word ID': self.word_info.word_id,
            'Morphology': self.word_info.short_record(),
            'URL': self.word_info.url,
            'Translation': ', '.join(lexeme_widget.translations),
            'Definition': lexeme.definition or '',
            'Examples': '<br>'.join(lexeme.examples[:EXAMPLES_LIMIT]),
            'Rection': ', '.join(lexeme.rection)
        }
        # Populate tags
        tags = []
        if self.word_info.word_class is not None:
            tags.append(self.word_info.word_class)
        if lexeme.level:
            tags.append(lexeme.level)
        return fields, tags

    def request_word_info(self):
        self.set_status('Loading...')
        operation = QueryOp(
            parent=self,
            op=lambda col: self._sonaveeb.get_word_info_by_reference(
                self.word_reference, timeout=REQUEST_TIMEOUT
            ),
            success=self._on_word_info_received
        ).failure(self._on_word_request_error)
        operation.run_in_background()

    # Slots & callbacks

    def _on_word_request_error(self, error):
        print(error)
        self.set_status('Error :(')

    def _on_word_info_received(self, word_info):
        # Test if this widget still exists
        try:
            self.isVisible()
        except RuntimeError:
            # Panel was deleted
            return
        if word_info is None:
            self.set_status('Failed to obtain word info :(')
        else:
            self.set_word_info(word_info)

    def _on_add_button_clicked(self):
        self.add_note()
        self._add_button.hide()
        self._delete_button.show()
        # Update audio UI state after adding note
        self.audio_control.update_state(
            urls=self.word_info.audio_urls if self.word_info else [],
            word=self.word_info.word if self.word_info else "",
            word_id=self.word_info.word_id if self.word_info else 0,
            note=self.note
        )

    def _on_delete_button_clicked(self):
        try:
            self.delete_note()
        except RuntimeError as e:
            QMessageBox.warning(self, 'Failed to delete the note', str(e))
        else:
            self._add_button.show()
            self._delete_button.hide()
            self._replace_button.hide()

    def _on_replace_button_clicked(self):
        try:
            self.update_note()
        except anki.errors.NotFoundError as e:
            QMessageBox.warning(self, 'Failed to update the note', str(e))
        else:
            self._replace_button.hide()

    def _on_lexeme_selected(self):
        '''Handle lexeme selection'''
        self.check_note_identical()

    def _on_translations_updated(self, lexeme_widget: LexemeWidget):
        if self._lexemes_container.get_selected_widget() is lexeme_widget:
            if len(lexeme_widget.translations) > 0:
                self._add_button.setEnabled(self.notetype is not None)
                self.check_note_identical()
