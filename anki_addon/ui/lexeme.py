'''
Lexeme widget for displaying word definitions and examples
'''

from typing import List, Optional
from aqt.qt import (
    Qt, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QRadioButton, QButtonGroup,
    QSizePolicy, pyqtSignal
)
from aqt import colors
from aqt.theme import theme_manager
from aqt.operations import QueryOp

from ..sonaveeb import LexemeInfo
from ..gtranslate import cross_translate
from ..globals import REQUEST_TIMEOUT
from .common import HSeparator


class LexemeWidget(QWidget):
    '''Widget for displaying a single lexeme's information'''
    translations_updated = pyqtSignal()
    translations_requested = pyqtSignal(bool)
    clicked = pyqtSignal()

    def __init__(
            self,
            lexeme: LexemeInfo,
            word_class: str,
            examples_limit: int = None,
            translations_limit: int = None,
            parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.lexeme = lexeme
        self.word_class = word_class
        self.examples_limit = examples_limit
        self.translations_limit = translations_limit
        self.translations = []
        self.lang = None
        self.translation_in_progress = False

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Add translations display
        translation_layout = QHBoxLayout()
        self.translations_label = QLabel()
        self.translations_label.setWordWrap(True)
        self.translations_label.hide()
        translation_layout.addWidget(self.translations_label)

        self.translation_status = QLabel()
        self.translation_status.setStyleSheet(f'color: {theme_manager.var(colors.FG_SUBTLE)}')
        self.translation_status.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.translation_status.hide()
        translation_layout.addWidget(self.translation_status)
        self.layout.addLayout(translation_layout)

        # Add definition if present
        if lexeme.definitions:
            definition_label = QLabel(f'**Definition:** *{";\n".join(lexeme.definitions)}*')
            definition_label.setTextFormat(Qt.TextFormat.MarkdownText)
            definition_label.setWordWrap(True)
            self.layout.addWidget(definition_label)

        # Add examples
        if lexeme.examples:
            examples = '- ' + '\n- '.join(lexeme.examples[:examples_limit])
            examples_label = QLabel(f'**Examples:**\n{examples}')
            examples_label.setTextFormat(Qt.TextFormat.MarkdownText)
            examples_label.setWordWrap(True)
            self.layout.addWidget(examples_label)

        # Add rection
        if lexeme.rection:
            rection = ', '.join(lexeme.rection)
            rection_label = QLabel(f'**Rection:** {rection}')
            rection_label.setTextFormat(Qt.TextFormat.MarkdownText)
            self.layout.addWidget(rection_label)

        # Add language level
        if lexeme.level:
            level_label = QLabel(f'**Level:** {lexeme.level}')
            level_label.setTextFormat(Qt.TextFormat.MarkdownText)
            self.layout.addWidget(level_label)

    def set_translation_language(self, lang):
        self.lang = lang
        translations = self.lexeme.translations.get(lang, [])
        if translations:
            # Process and set translations for this lexeme, limiting to specified amount
            self.set_translations(translations)
            self.set_translation_status(None)
        elif len(self.lexeme.translations) == 0:
            # No translations available for this lexeme
            self.set_translations(None)
            self.set_translation_status('No translations available')
        else:
            # Request translations from external source
            self.set_translation_status('Google translating...')
            self.request_cross_translations()
        return bool(translations)

    def set_translations(self, translations: List[str]):
        '''Update the translations display'''
        translations = translations or []
        self.translations = [t.strip('!., ') for t in translations[:self.translations_limit]]
        self.translations_label.setText(', '.join(self.translations))
        self.translations_label.setVisible(bool(translations))
        self.translations_updated.emit()

    def set_translation_status(self, status):
        '''Set translation status text'''
        self.translation_status.setText(str(status))
        self.translation_status.setVisible(bool(status))

    def request_cross_translations(self):
        '''Request translations for a specific lexeme'''
        self.translation_in_progress = True
        operation = QueryOp(
            parent=self,
            op=lambda col: cross_translate(
                sources=self.lexeme.translations,
                lang=self.lang,
                timeout=REQUEST_TIMEOUT,
            ),
            success=self._on_translations_received
        ).failure(self._on_translations_request_error)
        operation.run_in_background()
        self.translations_requested.emit(True)

    def _on_translations_request_error(self, error):
        '''Handle translation request errors'''
        self.translation_in_progress = False
        self.translations_requested.emit(False)
        self.set_translation_status('Failed to translate :(')

    def _on_translations_received(self, translations):
        '''Handle received translations'''
        # Test if this widget still exists
        self.translation_in_progress = False
        try:
            self.isVisible()
        except RuntimeError:
            return
        self.translations_requested.emit(False)
        self.set_translation_status('Google translated')
        # As a special case, add "to" before verbs infinitives in English
        if self.lang == 'en' and self.word_class == 'tegusõna':
            translations = [f'to {verb}'.replace('to to ', 'to ') for verb in translations]
        self.set_translations(translations)

    # Qt events
    def mousePressEvent(self, event):
        self.clicked.emit()
        return super().mousePressEvent(event)


class LexemesContainer(QWidget):
    '''Container widget for managing multiple lexeme widgets'''
    translations_updated = pyqtSignal(QWidget)
    translations_requested = pyqtSignal(bool)
    lexeme_selected = pyqtSignal()

    def __init__(
            self,
            lexemes: List[LexemeInfo] = None,
            lexemes_limit: int = None,
            examples_limit: int = None,
            translations_limit: int = None,
            parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.lexemes_limit = lexemes_limit
        self.examples_limit = examples_limit
        self.translations_limit = translations_limit
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        self.lexeme_widgets = []
        self.button_group = QButtonGroup(self)
        self.button_group.idToggled.connect(self._on_button_toggled)
        self.pending_translation_requests = set()
        if lexemes:
            self.set_data(lexemes)

    def set_data(self, lexemes: List[LexemeInfo], word_class: str):
        '''Update the lexeme display with new data'''
        self.clear()
        for i, lexeme in enumerate(lexemes[:self.lexemes_limit]):
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(0, 0, 0, 0)
            radio_button = QRadioButton()
            lexeme_widget = LexemeWidget(
                lexeme=lexeme,
                word_class=word_class,
                examples_limit=self.examples_limit,
                translations_limit=self.translations_limit,
                parent=self
            )
            lexeme_widget.translations_updated.connect(self._on_child_translations_updated)
            lexeme_widget.translations_requested.connect(self._on_child_translations_requested)
            lexeme_widget.clicked.connect(radio_button.click)
            item_layout.addWidget(radio_button)
            item_layout.addWidget(lexeme_widget)
            self.button_group.addButton(radio_button, i)
            self.layout.addWidget(HSeparator())
            self.layout.addLayout(item_layout)
            self.lexeme_widgets.append(lexeme_widget)
        # Select first lexeme by default if any exist
        if len(lexemes) > 0:
            self.button_group.button(0).setChecked(True)
        if len(lexemes) == 1:
            radio_button.hide()

    def set_translation_language(self, lang):
        for widget in self.lexeme_widgets:
            widget.set_translation_language(lang)

    def get_widget(self, index: int) -> LexemeWidget:
        '''Get lexeme widget at specified index'''
        if index < 0:
            return None
        return self.lexeme_widgets[index]

    def get_selected_index(self) -> int:
        '''Get the index of the selected lexeme'''
        return self.button_group.checkedId()

    def get_selected_widget(self) -> LexemeWidget:
        '''Get the selected lexeme widget'''
        index = self.button_group.checkedId()
        return self.get_widget(index)

    def clear(self):
        '''Clear lexemes list'''
        self.lexeme_widgets.clear()
        for button in self.button_group.buttons():
            self.button_group.removeButton(button)
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_child_translations_updated(self):
        widget = self.sender()
        self.translations_updated.emit(widget)

    def _on_child_translations_requested(self, active):
        widget = self.sender()
        if active:
            if not self.pending_translation_requests:
                # The first translation request started
                self.translations_requested.emit(True)
            self.pending_translation_requests.add(widget.lexeme.lexeme_id)
        else:
            self.pending_translation_requests.discard(widget.lexeme.lexeme_id)
            if not self.pending_translation_requests:
                # The last translation request finished
                self.translations_requested.emit(False)

    def _on_button_toggled(self, index, checked):
        if checked:
            self.lexeme_selected.emit()
