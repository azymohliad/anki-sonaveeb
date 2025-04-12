import logging
import anki.errors
from aqt.qt import (
    Qt, QSizePolicy, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedWidget, QGroupBox, QMessageBox, QStyle, pyqtSignal
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
from ..audio import AudioManager


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
        self._audio_enabled = False
        self._audio_download_in_progress = False

        # Add status label
        self._status_label = QLabel()
        self._status_label.setStyleSheet(f'font-size: 16pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add content UI
        self._title_label = QLabel()
        self._title_label.setTextFormat(Qt.TextFormat.RichText)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._title_label.setOpenExternalLinks(True)
        play_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self._pronounce_button = QPushButton()
        self._pronounce_button.setIcon(play_icon)
        self._pronounce_button.setFixedWidth(30)
        self._pronounce_button.clicked.connect(self._on_pronounce_button_clicked)
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(self._title_label)
        title_layout.addWidget(self._pronounce_button)
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
        self._buttons_status_label = QLabel()
        self._buttons_status_label.setStyleSheet(f'color: {theme_manager.var(colors.FG_SUBTLE)}')
        self._buttons_status_label.hide()

        data_layout = QVBoxLayout()
        data_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        data_layout.addLayout(title_layout)
        data_layout.addWidget(self._morphology_label)
        data_layout.addWidget(self._class_label)

        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        buttons_layout.addWidget(self._add_button, 0, Qt.AlignmentFlag.AlignRight)
        buttons_layout.addWidget(self._delete_button, 0, Qt.AlignmentFlag.AlignRight)
        buttons_layout.addWidget(self._replace_button, 0, Qt.AlignmentFlag.AlignRight)
        buttons_layout.addWidget(self._buttons_status_label, 0, Qt.AlignmentFlag.AlignRight)

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
        self.audio_manager = AudioManager(request_timeout=REQUEST_TIMEOUT)

    def set_translation_language(self, lang):
        '''Set translation language.

        Args:
            lang: Target language code
        '''
        self.lang = lang
        self._lexemes_container.set_translation_language(lang)
        self.refresh_buttons()

    def set_deck_id(self, deck_id):
        '''Set deck ID.'''
        self.deck_id = deck_id
        if self.word_info is not None:
            self.read_existing_note()

    def set_notetype(self, notetype):
        self.notetype = notetype
        self.refresh_buttons()

    def set_audio_enabled(self, enabled: bool):
        self._audio_enabled = enabled
        self.refresh_buttons()

    def set_status(self, status):
        '''Set status message.'''
        self._status_label.setText(status)
        self._stack.setCurrentWidget(self._status_label)

    def set_word_info(self, data):
        '''Set word information and update display.'''
        self.word_info = data
        # Update content
        self._title_label.setText(f'<a href="{data.url}"><h3>{data.word}</h3></a>')
        self._morphology_label.setText(f'**Forms**: {data.essential_forms(compress=True, join=True)}')
        self._class_label.setText(f'**Class**: {data.word_class}')
        self._class_label.setVisible(data.word_class is not None)
        self._lexemes_container.set_data(data.lexemes, data.word_class)
        self._stack.setCurrentWidget(self._content)
        self._pronounce_button.setVisible(bool(data.word_audio_url))
        # Request translations
        self.set_translation_language(self.lang)
        # Update buttons state
        self.read_existing_note()

    def read_existing_note(self):
        '''Read note for the current word if already exists.
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
        if notes:
            self.note = mw.col.get_note(notes[0])
        self.refresh_buttons()

    def refresh_buttons(self):
        note_exists = self.note is not None
        note_updated = self.is_note_content_updated()
        note_updated &= self.is_note_type_updated()
        notetype_ok = self.notetype is not None

        if self.word_info is not None:
            lexeme_widget = self._lexemes_container.get_selected_widget()
            translating = lexeme_widget.translation_in_progress
            translations_ok = bool(lexeme_widget.translations)
        else:
            translating = False
            translations_ok = False

        # Update visibility
        self._add_button.setVisible(not note_exists)
        self._replace_button.setVisible(note_exists and not note_updated)
        self._delete_button.setVisible(note_exists)

        # Update enabled state
        update_enabled = (
            notetype_ok
            and translations_ok
            and not translating
            and not self._audio_download_in_progress
        )
        delete_enabled = not self._audio_download_in_progress
        self._add_button.setEnabled(update_enabled)
        self._replace_button.setEnabled(update_enabled)
        self._delete_button.setEnabled(delete_enabled)

        # Set explanatory tooltip for disabled buttons
        tooltips = []
        if not notetype_ok:
            tooltips.append('Note type is missing')
        if not translations_ok:
            tooltips.append('No translations')
        if translating:
            tooltips.append('Translation is in progress')
        if self._audio_download_in_progress:
            tooltips.append('Downloading audio')
        tooltip = '\n'.join(tooltips)
        self._add_button.setToolTip(tooltip)
        self._replace_button.setToolTip(tooltip)

    def is_note_content_updated(self):
        '''Check if existing note matches the current word info.'''
        # Missing notes are outdated
        if self.note is None:
            return False

        # Notes that lack any field are considered outdated
        if len(set(NoteTypeManager.FIELDS) - set(self.note.keys())) > 0:
            return False

        # Otherwise check if all fields match
        fields, _ = self.note_content()
        skip_fields = ['Audio']
        identical = all([
            self.note[k] == v
            for k, v in fields.items()
            if k not in skip_fields
        ])

        # Check audio presence only
        identical &= bool(self.note['Audio']) == self._audio_enabled
        return identical

    def is_note_type_updated(self):
        '''Check if existing note is of the selected note type.'''
        # Missing notes are outdated
        if self.note is None:
            return False
        # Check if note type matches
        return self.note.mid == self.notetype.get('id')

    def add_note(self):
        '''Add a new note to the collection'''
        note = mw.col.new_note(self.notetype)
        self.fill_note(note)
        mw.col.add_note(note, self.deck_id)
        self.note = note
        if self._audio_enabled:
            self.save_audio()
        else:
            self.refresh_buttons()

    def update_note(self):
        '''Update an existing note with current data'''
        if self.note is not None:
            # Update note content
            # TODO: Check if note content is different
            self.fill_note(self.note)
            if not self._audio_enabled:
                # TODO: Should audio files be manually removed?
                # What if another note from another deck refers
                # to the same audio files?
                self.note['Audio'] = ''
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
            # Download audio if needed but missing
            if self._audio_enabled and not self.note['Audio']:
                self.save_audio()
            else:
                self.refresh_buttons()

    def delete_note(self):
        if self.note is not None:
            # TODO: Should audio files be manually deleted?
            results = mw.col.remove_notes([self.note.id])
            if results.count == 0:
                raise RuntimeError(
                    'Your database appears to be in an inconsistent state.'
                    ' Please use the Check Database action.')
            else:
                self.note = None
        self.refresh_buttons()

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
            'Morphology': self.word_info.essential_forms(compress=True, join=True),
            'URL': self.word_info.url,
            'Translation': ', '.join(lexeme_widget.translations),
            'Definition': lexeme.definition or '',
            'Examples': '<br>'.join(lexeme.examples[:EXAMPLES_LIMIT]),
            'Rection': ', '.join(lexeme.rection),
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

    def save_audio(self):
        self._buttons_status_label.setText('Downloading audio...')
        self._buttons_status_label.show()
        self._audio_download_in_progress = True
        self.refresh_buttons()
        operation = QueryOp(
            parent=self,
            op=lambda col: self.audio_manager.save(
                self.word_info.audio_urls(),
                self.word_info.word,
                self.word_info.word_id
            ),
            success=self._on_audio_received
        ).failure(self._on_save_audio_error)
        operation.run_in_background()

    # Slots & callbacks

    def _on_word_request_error(self, error):
        logging.error(f'Word request failed: {error}')
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

    def _on_save_audio_error(self, error):
        self._audio_download_in_progress = False
        self._buttons_status_label.hide()
        self.refresh_buttons()
        logging.error(f'Failed to save audio: {error}')
        QMessageBox.warning(self, 'Oops...', f'Failed to save pronunciation audio.')

    def _on_audio_received(self, audio_refs):
        self._audio_download_in_progress = False
        self._buttons_status_label.hide()
        if self.note is not None:
            self.note['Audio'] = ' '.join(audio_refs)
            mw.col.update_note(self.note)
        self.refresh_buttons()

    def _on_pronounce_button_clicked(self):
        self._pronounce_button.setEnabled(False)
        operation = QueryOp(
            parent=self,
            op=lambda col: self.audio_manager.play(self.word_info.word_audio_url),
            success=lambda _: self._pronounce_button.setEnabled(True),
        ).failure(self._on_pronounce_error)
        operation.run_in_background()

    def _on_pronounce_error(self, error):
        self._pronounce_button.setEnabled(True)
        logging.error(f'Failed to pronounce: {error}')
        QMessageBox.warning(self, 'Oops...', f'Failed to pronounce the word "{self.word_info.word}".')

    def _on_add_button_clicked(self):
        self.add_note()

    def _on_delete_button_clicked(self):
        try:
            self.delete_note()
        except RuntimeError as e:
            QMessageBox.warning(self, 'Failed to delete the note', str(e))

    def _on_replace_button_clicked(self):
        try:
            self.update_note()
        except anki.errors.NotFoundError as e:
            QMessageBox.warning(self, 'Failed to update the note', str(e))

    def _on_lexeme_selected(self):
        '''Handle lexeme selection'''
        self.refresh_buttons()

    def _on_translations_updated(self, lexeme_widget: LexemeWidget):
        if self._lexemes_container.get_selected_widget() is lexeme_widget:
            self.refresh_buttons()
