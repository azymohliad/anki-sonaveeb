from typing import List, Optional
from pathlib import Path
import shutil
import tempfile
import logging
import requests

from aqt import mw
from aqt.sound import av_player


class AudioManager:
    '''Manages audio operations for word pronunciations.'''
    def __init__(self, request_timeout=None):
        self._request_timeout = request_timeout
        self._cache = {}

    def __del__(self):
        self.cleanup()

    def get_audio_file(self, url: str, filepath: Optional[Path] = None) -> Path:
        '''Get local audio filepath from Sõnaveeb audio URL.

        Download and cache audio file when requested for the first time.
        Return cached path upon repeated requests.

        Args:
            url: Audio file URL
            filepath: Target filepath. If not specified and cache is missing,
                a temporary file is used. If specified while already cached elsewhere,
                the cached file is moved (if temporary) or copied (if not).

        Returns:
            Path to a downloaded audio file.

        '''
        if url in self._cache:
            # Audio file is cached
            cached_path, is_temporary = self._cache[url]
            logging.debug(f'Audio is cached: {cached_path} (temporary: {is_temporary})')
            # If different target path is requested,
            # move or copy the file and update cache
            if filepath is not None and filepath != cached_path:
                if is_temporary:
                    shutil.move(cached_path, filepath)
                else:
                    shutil.copy(cached_path, filepath)
                cached_path = filepath
                self._cache[url] = (cached_path, False)
                logging.debug(f'Cache updated: {cached_path} (temporary: {False})')
        else:
            logging.debug('Cache is missing, downloading audio file')
            # Cache is missing, download the file
            response = requests.get(url, timeout=self._request_timeout)
            response.raise_for_status()
            # Create target file
            is_temporary = filepath is None
            if is_temporary:
                file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            else:
                file = open(filepath, 'wb')
            cached_path = Path(file.name)
            # Save content
            with file as f:
                f.write(response.content)
            # Update cache
            self._cache[url] = (cached_path, is_temporary)
            logging.debug(f'Cache updated: {cached_path} (temporary: {is_temporary})')
        return cached_path

    def save(self, note, urls: List[str], word: str, word_id: int) -> bool:
        '''Download audio files and attach them to the note.'''
        audio_refs = []
        for i, url in enumerate(urls, 1):
            try:
                filename = f'sonaveeb_{word}_{word_id}_{i}.mp3'
                filepath = Path(mw.col.media.dir()) / filename
                self.get_audio_file(url, filepath)
                audio_refs.append(f'[sound:{filename}]')
            except requests.RequestException:
                logging.error(f'Unable to download audio file: {url}')
            except OSError:
                logging.error('Unable to add audio file to a note')

        if audio_refs:
            note['Audio'] = ' '.join(audio_refs)
            mw.col.update_note(note)
            return True

        return False

    def play(self, url: str) -> bool:
        '''Play audio from note or download and play from URL.'''
        try:
            temp_file = self.get_audio_file(url)
            av_player.play_file(str(temp_file))
            return True
        except requests.RequestException:
            return False

    def cleanup(self):
        '''Clear download cache and remove all temporary files.'''
        for filepath, is_temporary in self._cache.values():
            if is_temporary and filepath.exists():
                try:
                    filepath.unlink()
                except Exception:
                    logging.error(f'Unable to remove temporary audio file: {filepath}')
        self._cache.clear()
