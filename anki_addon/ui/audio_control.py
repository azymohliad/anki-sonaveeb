from dataclasses import dataclass
from typing import List, Optional
from aqt.qt import QWidget, QHBoxLayout, QPushButton, QMessageBox

from ..audio import AudioManager


@dataclass
class AudioState:
    '''Represents current audio state.'''
    has_remote_audio: bool = False
    has_note_audio: bool = False
    is_playing: bool = False
    is_downloading: bool = False


class AudioControl(QWidget):
    '''Audio control widget with play and download buttons.'''

    def __init__(self, audio: AudioManager, parent: Optional[QWidget] = None):
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

        self.play_button = QPushButton('▶')
        self.play_button.setFixedWidth(30)
        self.play_button.clicked.connect(self._on_play)

        self.download_button = QPushButton('Add Audio')
        self.download_button.setFixedWidth(100)
        self.download_button.clicked.connect(self._on_download)

        layout.addWidget(self.play_button)
        layout.addWidget(self.download_button)
        self.setLayout(layout)

        # Initially hide both buttons
        self.play_button.hide()
        self.download_button.hide()

    def update_state(self, urls: List[str], word: str, word_id: int, note):
        '''Update UI state based on available audio.'''
        self.urls = urls or []
        self.word = word or ""
        self.word_id = word_id or 0
        self.note = note

        self.state.has_remote_audio = bool(self.urls)
        self.state.has_note_audio = bool(note and note['Audio'].strip())

        self.play_button.setVisible(self.state.has_remote_audio or self.state.has_note_audio)

        can_download_audio = bool(note and not self.state.has_note_audio and self.state.has_remote_audio)
        self.download_button.setVisible(can_download_audio)

        if can_download_audio:
            self.download_button.setText('Add Audio')
            self.download_button.setEnabled(True)

    def add_audio(self, urls: List[str], word: str, word_id: int, note):
        '''Public method to trigger audio download and addition to note.'''
        self.update_state(urls, word, word_id, note)
        self._on_download()

    def _on_play(self):
        '''Handle play button click.'''
        if self.state.is_playing:
            return

        self.state.is_playing = True
        self.play_button.setEnabled(False)

        try:
            success = False
            if self.urls:
                success = self.audio.play(self.urls[0])
            if not success:
                QMessageBox.warning(self, 'No Audio', 'No audio files available')
        finally:
            self.state.is_playing = False
            self.play_button.setEnabled(True)

    def _on_download(self):
        '''Handle download button click.'''
        if self.state.is_downloading:
            return

        self.state.is_downloading = True
        self.download_button.setEnabled(False)
        self.download_button.setText('Downloading...')

        try:
            success = self.audio.save(
                note=self.note,
                urls=self.urls,
                word=self.word,
                word_id=self.word_id,
            )
            self.download_button.setText('Audio Added' if success else 'Download Failed')
            if success:
                self.state.has_note_audio = True
                self.download_button.hide()
        finally:
            self.state.is_downloading = False
            self.download_button.setEnabled(True)
