'''
Lexeme widget for displaying word definitions and examples
'''

from dataclasses import dataclass
from typing import List, Optional, Callable
from aqt.qt import QWidget, QVBoxLayout, QGroupBox, QLabel, QRadioButton, QButtonGroup, QSizePolicy
from aqt.theme import theme_manager
from aqt import colors


@dataclass
class LexemeConfig:
    '''Configuration for lexeme display'''
    example_prefix: str = ""


class LexemeWidget(QWidget):
    '''Widget for displaying a single lexeme's information'''
    def __init__(self, index: int, lexeme: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout = QVBoxLayout()

        # Create radio button for selection
        self.radio = QRadioButton(f"{index + 1}")
        self.layout.addWidget(self.radio)

        # Add definition if present
        if lexeme.definition:
            def_label = QLabel(lexeme.definition)
            def_label.setWordWrap(True)
            self.layout.addWidget(def_label)

        # Add translations display
        self.translations_label = QLabel()
        self.translations_label.setWordWrap(True)
        self.translations_label.hide()

        self.translations_status = QLabel()
        self.translations_status.setStyleSheet(f'color: {theme_manager.var(colors.FG_SUBTLE)}')
        self.translations_status.hide()

        self.layout.addWidget(self.translations_label)
        self.layout.addWidget(self.translations_status)

        # Add tags
        tags_label = self._create_tags_label(lexeme)
        self.layout.addWidget(tags_label)

        # Add examples
        header, content = self._create_examples_labels(lexeme)
        self.layout.addWidget(header)
        if content:
            self.layout.addWidget(content)

        self.setLayout(self.layout)

    def set_translations(self, translations: List[str], is_external: bool = False):
        '''Update the translations display'''
        if translations and len(translations) > 0:
            self.translations_label.setText(', '.join(translations))
            self.translations_label.show()
            self.translations_status.setText('Google Translated' if is_external else '')
            self.translations_status.setVisible(is_external)
        else:
            self.translations_label.hide()
            self.translations_status.setText('Translations unavailable')
            self.translations_status.show()

    def _create_tags_label(self, lexeme: dict) -> QLabel:
        '''Create a label for lexeme tags'''
        if self._has_valid_tags(lexeme):
            valid_tags = [tag for tag in lexeme.tags if tag is not None]
            label_text = "Tags: " + ", ".join(valid_tags)
        else:
            label_text = "Tags: None"

        label = QLabel(label_text)
        label.setStyleSheet(f'color: {theme_manager.var(colors.FG_SUBTLE)}')
        return label

    def _has_valid_tags(self, lexeme: dict) -> bool:
        '''Check if lexeme has any valid tags'''
        return lexeme.tags and any(tag is not None for tag in lexeme.tags)

    def _create_examples_labels(self, lexeme: dict) -> tuple[QLabel, Optional[QLabel]]:
        '''Create labels for examples header and content'''
        # Create header label
        header = QLabel("Näited:")
        header.setStyleSheet(f'color: {theme_manager.var(colors.FG_SUBTLE)}')
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Check if lexeme has valid examples
        if not hasattr(lexeme, 'examples') or not lexeme.examples:
            header.setText("Näited: None")
            return header, None

        # Create content label with valid examples
        valid_examples = [ex for ex in lexeme.examples if ex is not None]
        if not valid_examples:
            header.setText("Näited: None")
            return header, None

        content = QLabel("\n".join(f"{ex}" for ex in valid_examples))
        content.setWordWrap(True)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        return header, content

class LexemesContainer(QWidget):
    '''Container widget for managing multiple lexeme widgets'''
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.config = LexemeConfig()
        self.lexeme_widgets: List[LexemeWidget] = []
        self.button_group = QButtonGroup(self)

    def update(self, lexemes: List[dict], max_lexemes: int = 3) -> None:
        '''Update the lexeme display with new data'''
        self._clear_layout()

        for i, lexeme in enumerate(lexemes[:max_lexemes]):
            lexeme_widget = LexemeWidget(i, lexeme, parent=self)
            self.lexeme_widgets.append(lexeme_widget)
            self.layout.addWidget(lexeme_widget)
            self.button_group.addButton(lexeme_widget.radio, i)

        # Select first lexeme by default if any exist
        if self.lexeme_widgets:
            self.lexeme_widgets[0].radio.setChecked(True)

    def get_widget(self, index: int) -> Optional[LexemeWidget]:
        '''Get lexeme widget at specified index'''
        if 0 <= index < len(self.lexeme_widgets):
            return self.lexeme_widgets[index]
        return None

    def _clear_layout(self) -> None:
        '''Clear all widgets from layout'''
        self.lexeme_widgets.clear()
        for button in self.button_group.buttons():
            self.button_group.removeButton(button)
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
