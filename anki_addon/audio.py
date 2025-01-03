from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import re
import tempfile
import requests

from aqt import mw
from aqt.sound import av_player, SoundOrVideoTag


@dataclass
class Audio:
    '''Manages audio operations for word pronunciations.'''
    base_url: str
    request_timeout: int

    def add_to_note(self, urls: List[str], word: str, word_id: int, note) -> bool:
        '''Download audio files and add them to note.'''
        if not urls:
            return False

        temp_file = None
        try:
            audio_refs = []
            for i, url in enumerate(urls, 1):
                response = requests.get(url, timeout=self.request_timeout)
                response.raise_for_status()

                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tf:
                    tf.write(response.content)
                    temp_file = Path(tf.name)

                try:
                    filename = f"{word}_{word_id}_{i}.mp3"
                    target_path = Path(mw.col.media.dir()) / filename
                    temp_file.rename(target_path)
                    audio_refs.append(f"[sound:{filename}]")
                finally:
                    if temp_file.exists():
                        temp_file.unlink()

            if audio_refs:
                note['Audio'] = ' '.join(audio_refs)
                mw.col.update_note(note)
                return True

            return False

        except (requests.RequestException, OSError):
            return False
        finally:
            if temp_file and temp_file.exists():
                temp_file.unlink()

    def play(self, note_audio: Optional[str], urls: List[str]) -> bool:
        '''Play audio from note or download and play from URL.'''
        # Try playing from note first
        if note_audio:
            sound_tags = [
                SoundOrVideoTag(filename=m)
                for m in re.findall(r'\[sound:(.*?)\]', note_audio)
            ]
            if sound_tags:
                av_player.play_tags(sound_tags)
                return True

        # Fall back to downloading and playing
        if not urls:
            return False

        temp_file = None
        try:
            response = requests.get(urls[0], timeout=self.request_timeout)
            response.raise_for_status()

            # Create temp file in Anki media directory to ensure proper playback
            with tempfile.NamedTemporaryFile(suffix='.mp3', dir=mw.col.media.dir(), delete=False) as tf:
                tf.write(response.content)
                temp_file = Path(tf.name)

            av_player.play_file(str(temp_file))
            return True

        except requests.RequestException:
            return False
        finally:
            # Clean up temp file after a short delay to ensure playback completes
            if temp_file and temp_file.exists():
                mw.progress.timer(
                    1000,  # 1 second delay
                    lambda: temp_file.unlink() if temp_file.exists() else None,
                    False
                )
