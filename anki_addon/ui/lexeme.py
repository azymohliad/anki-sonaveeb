"""
Lexeme widget for displaying word definitions and examples
"""

from dataclasses import dataclass
from typing import List, Optional, Callable
from aqt.qt import QWidget, QVBoxLayout, QGroupBox, QLabel, QRadioButton, QButtonGroup, QSizePolicy
from aqt.theme import theme_manager
from aqt import colors

@dataclass
class LexemeConfig:
    """Configuration for lexeme display"""
    max_examples: int = 3
    max_lexemes: int = 3
    example_prefix: str = ""

class LexemeWidget(QWidget):
    """Widget for displaying and selecting lexeme information"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.button_group = QButtonGroup(self)
        self.setLayout(self.layout)
        self.config = LexemeConfig()

    def update(self, lexemes: List[dict], on_select: Callable[[int, bool], None]) -> None:
        """Update the lexeme display with new data"""
        self._clear_layout()

        for i, lexeme in enumerate(lexemes[:self.config.max_lexemes]):
            box = self._create_lexeme_box(i, lexeme, on_select)
            self.layout.addWidget(box)

    def _create_lexeme_box(self, index: int, lexeme: dict, on_select: Callable) -> QGroupBox:
        """Create a box containing lexeme information"""
        box = QGroupBox()
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout()

        # Add selection radio
        radio = QRadioButton(f"{index+1}")
        self.button_group.addButton(radio, index)
        radio.toggled.connect(lambda checked: on_select(index, checked))
        layout.addWidget(radio)

        # Add definition if present
        if lexeme.definition:
            def_label = QLabel(lexeme.definition)
            def_label.setWordWrap(True)
            layout.addWidget(def_label)

        # Add tags if valid ones exist
        if self._has_valid_tags(lexeme):
            tags_label = self._create_tags_label(lexeme)
        else:
            tags_label = QLabel("Tags: None")
            tags_label.setStyleSheet(f'color: {theme_manager.var(colors.FG_SUBTLE)}')
        layout.addWidget(tags_label)

        # Add examples
        header, content = self._create_examples_label(lexeme)
        layout.addWidget(header)
        if content:
            layout.addWidget(content)

        box.setLayout(layout)
        return box

    def _create_examples_label(self, lexeme: dict) -> tuple[QLabel, Optional[QLabel]]:
        """Create labels for examples header and content"""
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

        # Create examples content
        content = QLabel("\n".join(f"{ex}" for ex in valid_examples))
        content.setWordWrap(True)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        return header, content

    def _create_tags_label(self, lexeme: dict) -> QLabel:
        """Create a label for lexeme tags"""
        valid_tags = [tag for tag in lexeme.tags if tag is not None]
        label = QLabel("Tags: " + ", ".join(valid_tags))
        label.setStyleSheet(f'color: {theme_manager.var(colors.FG_SUBTLE)}')
        return label

    def _has_valid_tags(self, lexeme: dict) -> bool:
        """Check if lexeme has any valid tags"""
        return lexeme.tags and any(tag is not None for tag in lexeme.tags)

    def _clear_layout(self) -> None:
        """Clear all widgets from layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def select_lexeme(self, index: int) -> None:
        """Select a lexeme by index"""
        if 0 <= index < len(self.button_group.buttons()):
            self.button_group.button(index).setChecked(True)
