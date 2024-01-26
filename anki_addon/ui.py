from aqt.qt import (
    pyqtSignal, Qt, QSizePolicy,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QButtonGroup, QStackedWidget, QComboBox, QGroupBox, QScrollArea,
    QMessageBox,
)
from aqt.operations import QueryOp
from aqt.theme import theme_manager
from aqt import mw, colors

from .sonaveeb import Sonaveeb
from .note_type import find_note_type, verify_note_type, add_note_type


class SonaveebNoteDialog(QWidget):
    def __init__(self, sonaveeb=None, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle('Add Sõnaveeb Notes')
        self.resize(600, 600)

        # Add header bar
        # - Add deck selector
        self._deck_selector = QComboBox()
        for deck in mw.col.decks.all_names_and_ids():
            self._deck_selector.addItem(deck.name, userData=deck.id)
        self._deck_selector.currentIndexChanged.connect(self.deck_changed)
        # - Add language selector
        languages = {
            'uk': 'Українська',
            'ru': 'Русский',
            'en': 'English',
            'fr': 'Française',
        }
        self._lang_selector = QComboBox()
        for code, lang in languages.items():
            self._lang_selector.addItem(lang, userData=code)
        self._lang_selector.currentIndexChanged.connect(self.language_changed)
        self._lang_selector.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        # - Populate header bar
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel('Deck:'))
        header_layout.addWidget(self._deck_selector)
        header_layout.addStretch(1)
        header_layout.addWidget(QLabel('Translate into:'))
        header_layout.addWidget(self._lang_selector)
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_bar = QWidget()
        header_bar.setStyleSheet(f'background: {theme_manager.var(colors.CANVAS_ELEVATED)}')
        header_bar.setLayout(header_layout)

        # Add search bar
        self._search = QLineEdit()
        self._search.setFocus()
        self._search.returnPressed.connect(self.search_triggered)
        self._search_button = QPushButton('Search')
        self._search_button.clicked.connect(self.search_triggered)
        search_layout = QHBoxLayout()
        search_layout.addWidget(self._search)
        search_layout.addWidget(self._search_button)
        search_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        search_layout.setContentsMargins(10, 5, 10, 5)
        search_bar = QWidget()
        search_bar.setFixedWidth(500)
        search_bar.setLayout(search_layout)

        # Add content UI
        self._form_selector = SelectorRow()
        self._form_selector.selected.connect(self.form_selected)
        self._search_results_layout = QVBoxLayout()
        self._search_results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        search_results_container = QWidget()
        search_results_container.setLayout(self._search_results_layout)
        search_results_container.setMaximumWidth(600)
        search_results_scrollarea = QScrollArea()
        search_results_scrollarea.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        search_results_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        search_results_scrollarea.setWidget(search_results_container)
        search_results_scrollarea.setWidgetResizable(True)
        # search_results_scrollarea.setStyleSheet('border: 0')
        content_layout = QVBoxLayout()
        content_layout.addWidget(self._form_selector)
        content_layout.addWidget(search_results_scrollarea)
        content_layout.setContentsMargins(0, 0, 0, 0)
        self._content = QWidget()
        self._content.setLayout(content_layout)
        self._status = QLabel()
        self._status.setStyleSheet(f'font-size: 18pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_stack = QStackedWidget()
        self._content_stack.addWidget(self._content)
        self._content_stack.addWidget(self._status)
        self._content_stack.setCurrentWidget(self._status)

        layout = QVBoxLayout()
        layout.addWidget(header_bar)
        layout.addWidget(search_bar)
        layout.addWidget(self._content_stack)
        layout.setAlignment(search_bar, Qt.AlignmentFlag.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self._search.setFocus()
        self.set_status('Search something :)')

        self._sonaveeb = sonaveeb or Sonaveeb()

        # Restore config
        self._config = mw.addonManager.getConfig(__name__)
        if deck := self._config.get('deck'):
            self._deck_selector.setCurrentText(deck)
        if lang := self._config.get('language'):
            index = self._lang_selector.findData(lang)
            if index >= 0:
                self._lang_selector.setCurrentIndex(index)

    def lang_code(self):
        return self._lang_selector.currentData()

    def deck_id(self):
        return self._deck_selector.currentData()

    def search_results(self):
        return [
            self._search_results_layout.itemAt(i).widget()
            for i in range(self._search_results_layout.count())
        ]

    def set_status(self, status):
        self._status.setText(status)
        self._content_stack.setCurrentWidget(self._status)

    def clear_search_results(self):
        self._form_selector.clear()
        while self._search_results_layout.count():
            child = self._search_results_layout.takeAt(0)
            child.widget().deleteLater()

    def request_search(self, query):
        self._search_button.setEnabled(False)
        self.set_status('Searching...')
        operation = QueryOp(
            parent=self,
            op=lambda col: self._sonaveeb.get_candidates(query),
            success=self.search_results_received
        )
        operation.run_in_background()

    def search_triggered(self):
        self.clear_search_results()
        query = self._search.text().strip()
        if query != '':
            self.request_search(query)
        else:
            self.set_status('Search something :)')

    def form_selected(self, form):
        print(f'Selected form: {form}')
        self._search.setText(form)
        self.search_triggered()

    def language_changed(self, _index):
        lang = self.lang_code()
        for word_panel in self.search_results():
            word_panel.set_translation_language(lang)
        self._config['language'] = lang
        mw.addonManager.writeConfig(__name__, self._config)

    def deck_changed(self, _index):
        deck_id = self.deck_id()
        for word_panel in self.search_results():
            word_panel.set_deck(deck_id)
        self._config['deck'] = self._deck_selector.currentText()
        mw.addonManager.writeConfig(__name__, self._config)

    def search_results_received(self, result):
        homonyms, alt_forms = result
        self._search_button.setEnabled(True)
        if len(homonyms) == 0:
            if len(alt_forms) == 0:
                self.set_status('Not found :(')
            elif len(alt_forms) == 1:
                self.request_search(alt_forms[0])
            else:
                self._form_selector.set_label('Select base form:')
                self._form_selector.set_options(alt_forms)
                self._form_selector.show()
                self._content_stack.setCurrentWidget(self._content)
        else:
            self._form_selector.set_options(alt_forms)
            self._form_selector.set_label('See also:')
            self._form_selector.setVisible(len(alt_forms) > 0)
            self._content_stack.setCurrentWidget(self._content)
            for homonym in homonyms:
                word_panel = WordInfoPanel(homonym, self._sonaveeb, self.deck_id(), self.lang_code())
                self._search_results_layout.addWidget(word_panel)



class WordInfoPanel(QGroupBox):
    def __init__(self, search_info, sonaveeb, deck_id, lang, parent=None):
        super().__init__(parent=parent)
        # Set state
        self.deck_id = deck_id
        self.lang = lang
        self.search_info = search_info
        self.word_info = None
        self._note_type_id = None
        self._sonaveeb = sonaveeb
        # Add status label
        self._status = QLabel()
        self._status.setStyleSheet(f'font-size: 16pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Add content UI
        self._title = QLabel()
        self._title.setTextFormat(Qt.TextFormat.RichText)
        self._title.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._title.setOpenExternalLinks(True)
        self._morphology = QLabel()
        self._pos = QLabel()
        self._translations = QLabel()
        data_layout = QVBoxLayout()
        data_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        data_layout.addWidget(self._title)
        data_layout.addWidget(self._morphology)
        data_layout.addWidget(self._pos)
        data_layout.addWidget(self._translations)
        self._add_button = QPushButton()
        self._add_button.setEnabled(False)
        self._add_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self._add_button.clicked.connect(self.add_button_clicked)
        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        buttons_layout.addWidget(self._add_button)
        buttons_layout.setContentsMargins(10,0,10,0)
        content_layout = QHBoxLayout()
        content_layout.addLayout(data_layout)
        content_layout.addLayout(buttons_layout)
        content_layout.setContentsMargins(10,0,10,0)
        self._content = QWidget()
        self._content.setLayout(content_layout)
        # Populate the UI
        self._stack = QStackedWidget()
        self._stack.addWidget(self._status)
        self._stack.addWidget(self._content)
        self._stack.setCurrentWidget(self._status)
        layout = QVBoxLayout()
        layout.addWidget(self._stack)
        layout.setContentsMargins(10,0,10,0)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        # Request word info
        self.set_note_added(False)
        self.request_word_info()

    def translation(self):
        if self.word_info is None or self.lang is None:
            return None
        translations = self.word_info.lexemes[0].translations.get(self.lang)
        if translations is not None:
            translations = [t.replace('!', '') for t in translations]
            translations = ', '.join(translations[:3])
        return translations

    def set_translation_language(self, lang):
        self.lang = lang
        if translation := self.translation():
            self._translations.setText(translation)
        else:
            self._translations.setText('Translation unavailable')
            self._translations.setStyleSheet(f'color: {theme_manager.var(colors.FG_SUBTLE)}')

    def set_deck(self, deck_id):
        self.deck_id = deck_id
        self.check_note_added()

    def set_status(self, status):
        self._status.setText(status)
        self._stack.setCurrentWidget(self._status)

    def set_word_info(self, data):
        self.word_info = data
        self._title.setText(f'<a href="{data.url}"><h3>{data.word}</h3></a>')
        self._morphology.setText(data.short_record())
        self._pos.setText(f'PoS: {data.pos}')
        self._pos.setVisible(data.pos is not None)
        self.set_translation_language(self.lang)
        self._stack.setCurrentWidget(self._content)

    def set_note_added(self, state):
        self._add_button.setText('Note added' if state else 'Add note')
        self._add_button.setDisabled(state)

    def check_note_added(self):
        deck = mw.col.decks.get(self.deck_id)['name']
        existing_notes = mw.col.find_notes(f'URL:"{self.word_info.url}" deck:"{deck}"')
        self.set_note_added(len(existing_notes) != 0)

    def request_word_info(self):
        self.set_status('Loading...')
        operation = QueryOp(
            parent=self,
            op=lambda col: self._sonaveeb.get_word_info_by_candidate(self.search_info),
            success=self.word_info_received
        ).failure(self.handle_request_error)
        operation.run_in_background()

    def handle_request_error(self, error):
        print(error)
        self.set_status('Error :(')

    def get_note_type_id(self):
        if self._note_type_id is not None:
            return self._note_type_id

        if (ntid := find_note_type()) is not None:
            if verify_note_type(ntid):
                self._note_type_id = ntid
                return ntid
            else:
                QMessageBox.warning(self, 'Malformed note type')

        self._note_type_id = add_note_type()
        return self._note_type_id

    def add_note(self):
        if (ntid := self.get_note_type_id()) is not None:
            note = mw.col.new_note(ntid)
            note['Morphology'] = self.word_info.short_record()
            note['Translation'] = self.translation()
            note['URL'] = self.word_info.url
            note.add_tag(self.word_info.pos)
            mw.col.add_note(note, self.deck_id)
            self.set_note_added(True)

    def word_info_received(self, word_info):
        if word_info is None:
            self._add_button.setEnabled(False)
            self.set_status('Failed to obtain word info :(')
        else:
            self.set_word_info(word_info)
            self.check_note_added()

    def add_button_clicked(self):
        self.add_note()


class SelectorRow(QWidget):
    selected = pyqtSignal(str)
    selected_index = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._buttons = QButtonGroup()
        self._buttons.idToggled.connect(self._button_toggled)
        self._label = QLabel()
        self._layout = QHBoxLayout()
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._layout.addWidget(self._label)
        self.setLayout(self._layout)

    def set_label(self, label):
        self._label.setText(label)

    def set_options(self, options):
        self.clear()
        for i, option in enumerate(options):
            button = QPushButton(option)
            button.setFlat(True)
            button.setCheckable(True)
            # button.setChecked(i == 0)
            self._buttons.addButton(button, i)
            self._layout.addWidget(button)

    def clear(self):
        for button in self._buttons.buttons():
            self._buttons.removeButton(button)
            self._layout.removeWidget(button)
            button.deleteLater()

    def _button_toggled(self, index, checked):
        if checked:
            self.selected.emit(self._buttons.button(index).text())
            self.selected_index.emit(index)
