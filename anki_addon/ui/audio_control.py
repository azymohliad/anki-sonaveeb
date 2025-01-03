from dataclasses import dataclass
from typing import List, Optional
from aqt.qt import QWidget, QHBoxLayout, QPushButton, QMessageBox

from ..audio import Audio


@dataclass
class AudioState:
    '''Represents current audio state.'''
    has_word_audio: bool = False
    has_note_audio: bool = False
    is_playing: bool = False
    is_downloading: bool = False


class AudioControl(QWidget):
    '''Audio control widget with play and download buttons.'''

    def __init__(self, audio: Audio, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.audio = audio
        self.state = AudioState()
        self.urls = []
        self.word = ""
        self.word_id = 0
        self.note = None
        self._setup_ui()

    def _setup_ui(self):
        '''Initialize the UI components.'''
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.play_btn = QPushButton('▶')
        self.play_btn.setFixedWidth(30)
        self.play_btn.clicked.connect(self._on_play)

        self.download_btn = QPushButton('Add Audio')
        self.download_btn.setFixedWidth(100)
        self.download_btn.clicked.connect(self._on_download)

        layout.addWidget(self.play_btn)
        layout.addWidget(self.download_btn)
        self.setLayout(layout)

        # Initially hide both buttons
        self.play_btn.hide()
        self.download_btn.hide()

    def update_state(self, urls: List[str], word: str, word_id: int, note):
        '''Update UI state based on available audio.'''
        self.urls = urls or []
        self.word = word or ""
        self.word_id = word_id or 0
        self.note = note

        self.state.has_word_audio = bool(urls)
        self.state.has_note_audio = bool(note and note['Audio'].strip() if note else False)

        # Show play button if any audio available
        self.play_btn.setVisible(self.state.has_word_audio or self.state.has_note_audio)

        # Show download button if note exists without audio but word has audio
        can_add = bool(note and not self.state.has_note_audio and self.state.has_word_audio)
        self.download_btn.setVisible(can_add)

        if can_add:
            self.download_btn.setText('Add Audio')
            self.download_btn.setEnabled(True)

    def add_audio(self, urls: List[str], word: str, word_id: int, note):
        '''Public method to trigger audio download and addition to note.'''
        self.urls = urls or []
        self.word = word or ""
        self.word_id = word_id or 0
        self.note = note
        self._on_download()

    def _on_play(self):
        '''Handle play button click.'''
        if self.state.is_playing:
            return

        self.state.is_playing = True
        self.play_btn.setEnabled(False)

        try:
            success = self.audio.play(
                note_audio=self.note['Audio'] if self.note else None,
                urls=self.urls
            )
            if not success:
                QMessageBox.warning(self, 'No Audio', 'No audio files available')
        finally:
            self.state.is_playing = False
            self.play_btn.setEnabled(True)

    def _on_download(self):
        '''Handle download button click.'''
        if self.state.is_downloading:
            return

        self.state.is_downloading = True
        self.download_btn.setEnabled(False)
        self.download_btn.setText('Downloading...')

        try:
            success = self.audio.add_to_note(
                urls=self.urls,
                word=self.word,
                word_id=self.word_id,
                note=self.note
            )
            self.download_btn.setText('Audio Added' if success else 'Download Failed')
            if success:
                self.state.has_note_audio = True
                self.download_btn.hide()
        finally:
            self.state.is_downloading = False
            self.download_btn.setEnabled(True)