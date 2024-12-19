from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import re
import tempfile
import requests

from aqt import mw
from aqt.sound import av_player, SoundOrVideoTag

class TempFileLocation(Enum):
    '''Where to store temporary audio files.'''
    SYSTEM = auto()      # System's temporary directory
    ANKI_MEDIA = auto()  # Anki's media directory


@dataclass
class AudioManager:
    '''Manages audio operations for word pronunciations.'''
    base_url: str
    request_timeout: int

    def _download_audio_file(self, url: str, location: TempFileLocation = TempFileLocation.SYSTEM) -> Path:
        '''Download audio file from URL to temporary location.

        Args:
            url: Audio file URL
            location: Where to store the temporary file

        Returns:
            Path to downloaded temporary file

        Raises:
            requests.RequestException: If download fails
        '''
        response = requests.get(url, timeout=self.request_timeout)
        response.raise_for_status()

        temp_dir = mw.col.media.dir() if location == TempFileLocation.ANKI_MEDIA else None

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False, dir=temp_dir) as temp_file:
            temp_file.write(response.content)
            return Path(temp_file.name)

    def download_and_attach_audio(self, urls: List[str], word: str, word_id: int, note) -> bool:
        '''Download audio files and attach them to the note.'''
        if not urls:
            return False

        audio_refs = []
        temp_files = []

        try:
            for i, url in enumerate(urls, 1):
                try:
                    temp_file = self._download_audio_file(url, TempFileLocation.SYSTEM)
                    temp_files.append(temp_file)
                except (requests.RequestException, OSError):
                    continue

                try:
                    filename = f"{word}_{word_id}_{i}.mp3"
                    target_path = Path(mw.col.media.dir()) / filename
                    temp_file.rename(target_path)
                    audio_refs.append(f"[sound:{filename}]")
                    temp_files.remove(temp_file)
                except OSError as err:
                    continue

            if audio_refs:
                note['Audio'] = ' '.join(audio_refs)
                mw.col.update_note(note)
                return True

            return False

        except Exception as err:
            return False
        finally:
            for temp_file in temp_files:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass

    def play(self, note_audio: Optional[str], urls: List[str]) -> bool:
        '''Play audio from note or download and play from URL.'''
        if note_audio:
            sound_tags = [
                SoundOrVideoTag(filename=m)
                for m in re.findall(r'\[sound:(.*?)\]', note_audio)
            ]
            if sound_tags:
                av_player.play_tags(sound_tags)
                return True

        if not urls:
            return False

        temp_file = None
        try:
            temp_file = self._download_audio_file(urls[0], TempFileLocation.SYSTEM)
            av_player.play_file(str(temp_file))
            return True

        except requests.RequestException:
            return False
        finally:
            if temp_file and temp_file.exists():
                mw.progress.timer(
                    3000,
                    lambda: temp_file.unlink() if temp_file.exists() else None,
                    False
                )
