from aqt.qt import (
    pyqtSignal, Qt, QSizePolicy,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QButtonGroup, QStackedWidget, QComboBox,
)
from aqt.operations import QueryOp
from aqt import mw

from .sonaveeb import Sonaveeb


class SonaveebNoteDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle('Add Sõnaveeb Notes')

        # Add header bar
        # - Add deck selector
        self._deck_selector = QComboBox()
        for deck in mw.col.decks.all_names_and_ids():
            self._deck_selector.addItem(deck.name, userData=deck.id)
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
        header_bar = QHBoxLayout()
        header_bar.addWidget(QLabel('Deck:'))
        header_bar.addWidget(self._deck_selector)
        header_bar.addStretch(1)
        header_bar.addWidget(QLabel('Translate into:'))
        header_bar.addWidget(self._lang_selector)

        # Add search bar
        self._search = QLineEdit()
        self._search.returnPressed.connect(self.search_triggered)
        self._search_button = QPushButton('Search')
        self._search_button.clicked.connect(self.search_triggered)
        search_bar = QHBoxLayout()
        search_bar.addWidget(self._search)
        search_bar.addWidget(self._search_button)
        search_bar.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Add search results UI
        self._form_selector = SelectorRow()
        self._form_selector.selected.connect(self.form_selected)
        self._info_status = QLabel()
        self._info_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_stack = QStackedWidget()
        self._info_stack.addWidget(self._info_status)
        self._info_stack.setCurrentWidget(self._info_status)
        results_layout = QVBoxLayout()
        results_layout.addWidget(self._form_selector)
        results_layout.addWidget(self._info_stack)
        self._search_results = QWidget()
        self._search_results.setLayout(results_layout)
        self._search_status = QLabel()
        self._search_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_stack = QStackedWidget()
        self._content_stack.addWidget(self._search_results)
        self._content_stack.addWidget(self._search_status)
        self._content_stack.setCurrentWidget(self._search_status)

        # Add control bar
        self._add_button = QPushButton('Add note')
        self._add_button.setEnabled(False)
        self._add_button.clicked.connect(self.add_clicked)

        layout = QVBoxLayout()
        layout.addLayout(header_bar)
        layout.addLayout(search_bar)
        layout.addWidget(self._content_stack)
        layout.addWidget(self._add_button)
        self.setLayout(layout)

        self._sonaveeb = Sonaveeb()
        self._homonyms = []
        self._info_panels = {}

    @property
    def lang_code(self):
        return self._lang_selector.currentData()

    @property
    def deck_id(self):
        return self._deck_selector.currentData()

    def set_search_status(self, status):
        self._search_status.setText(status)
        self._content_stack.setCurrentWidget(self._search_status)

    def set_info_status(self, status):
        self._info_status.setText(status)
        self._info_stack.setCurrentWidget(self._info_status)

    def request_word_info(self, word_id):
        self.set_info_status('Loading...')
        operation = QueryOp(
            parent=self,
            op=lambda col: self._sonaveeb.get_word_info_by_id(word_id),
            success=lambda word_info: self.word_info_received(word_id, word_info)
        )
        operation.run_in_background()

    def request_search(self, query):
        self._search_button.setEnabled(False)
        self.set_search_status('Searching...')
        operation = QueryOp(
            parent=self,
            op=lambda col: self._sonaveeb.get_candidates(query),
            success=self.search_results_received
        )
        operation.run_in_background()

    def search_triggered(self):
        query = self._search.text().strip()
        if query != '':
            self.request_search(query)
            self._add_button.setText('Add note')
            self._add_button.setEnabled(False)
            self._form_selector.clear()
            for info_panel in self._info_panels.values():
                info_panel.deleteLater()
            self._info_panels.clear()

    def form_selected(self, form):
        print(f'Selected form: {form}')
        self._search.setText(form)
        self.search_triggered()

    def language_changed(self, _index):
        lang = self.lang_code
        for panel in self._info_panels.values():
            panel.set_translation_language(lang)

    def add_clicked(self):
        info_widget = self._info_stack.currentWidget()
        if isinstance(info_widget, WordInfoPanel):
            data = info_widget.data
            node_type = mw.col.models.id_for_name('Basic (and reversed card)')
            note = mw.col.new_note(node_type)
            note['Front'] = data.short_record()
            note['Back'] = ', '.join(data.lexemes[0].translations.get('uk', ['<no translation>'])[:3])
            note.add_tag(data.pos)
            mw.col.add_note(note, self.deck_id)
            self._add_button.setText('Note added')
            self._add_button.setEnabled(False)

    def search_results_received(self, result):
        self._homonyms, alt_forms = result
        self._search_button.setEnabled(True)
        if len(self._homonyms) == 0:
            if len(alt_forms) == 0:
                self.set_search_status('Not found :(')
            elif len(alt_forms) == 1:
                self.request_search(alt_forms[0])
            else:
                self._form_selector.set_label('Select base form:')
                self._form_selector.set_options(alt_forms)
                self._form_selector.show()
                self._content_stack.setCurrentWidget(self._search_results)
                self.set_info_status('')
        else:
            self._form_selector.set_options(alt_forms)
            self._form_selector.set_label('See also:')
            self._form_selector.setVisible(len(alt_forms) > 0)
            self._content_stack.setCurrentWidget(self._search_results)
            self.request_word_info(self._homonyms[0].word_id)

    def word_info_received(self, word_id, word_info):
        if word_info is None:
            self._add_button.setEnabled(False)
            self.set_info_status('Failed to obtain word info :(')
        else:
            info_panel = WordInfoPanel(word_info, translate=self.lang_code)
            self._info_panels[word_id] = info_panel
            self._info_stack.addWidget(info_panel)
            self._info_stack.setCurrentWidget(info_panel)
            # Find existing notes
            # query = self.build_search_string(word_info.short_record(), SearchNode(field_name=field_name))
            existing_notes = mw.col.find_notes(f'front:"{word_info.short_record()}"')
            if len(existing_notes) != 0:
                self._add_button.setEnabled(False)
                self._add_button.setText('Note already exists!')
            else:
                self._add_button.setEnabled(True)


class WordInfoPanel(QWidget):
    def __init__(self, data, translate=None, parent=None):
        super().__init__(parent=parent)
        self.data = data
        self._title = QLabel(f'<a href="{data.url}"><h3>{data.word}</h3></a>')
        self._title.setTextFormat(Qt.TextFormat.RichText)
        self._title.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._title.setOpenExternalLinks(True)
        self._morphology = QLabel(data.short_record())
        self._tags = QLabel(f'Tags: {data.pos}')
        self._translations = QLabel()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._title)
        layout.addWidget(self._morphology)
        layout.addWidget(self._tags)
        layout.addWidget(self._translations)
        self.setLayout(layout)
        if translate is not None:
            self.set_translation_language(translate)

    def set_translation_language(self, lang):
        translations = self.data.lexemes[0].translations.get(lang, ['Translation unavailable'])
        translations = ', '.join(translations[:3])
        self._translations.setText(translations)


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
