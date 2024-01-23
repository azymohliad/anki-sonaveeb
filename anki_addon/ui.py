from aqt.qt import (
    pyqtSignal, Qt, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QButtonGroup, QStackedWidget
)
from aqt.operations import QueryOp

from .sonaveeb import Sonaveeb


class SonaveebNoteDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle('Add Sõnaveeb Notes')

        self._search = QLineEdit()
        self._search.returnPressed.connect(self.search_triggered)
        self._search_button = QPushButton('Search')
        self._search_button.clicked.connect(self.search_triggered)
        search_line = QHBoxLayout()
        search_line.addWidget(self._search)
        search_line.addWidget(self._search_button)
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
        layout = QVBoxLayout()
        layout.addLayout(search_line)
        layout.addWidget(self._content_stack)
        self.setLayout(layout)

        self._sonaveeb = Sonaveeb()
        self._homonyms = []
        self._info_panels = {}

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
            self._form_selector.clear()
            for info_panel in self._info_panels.values():
                info_panel.deleteLater()
            self._info_panels.clear()

    def form_selected(self, form):
        print(f'Selected form: {form}')
        self._search.setText(form)
        self.search_triggered()

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
            self.set_info_status('Failed to obtain word info :(')
        else:
            info_panel = WordInfoPanel(word_info)
            self._info_panels[word_id] = info_panel
            self._info_stack.addWidget(info_panel)
            self._info_stack.setCurrentWidget(info_panel)


class WordInfoPanel(QWidget):
    def __init__(self, data, translate='uk', parent=None):
        super().__init__(parent=parent)
        title = QLabel(f'<a href="{data.url}"><h3>{data.word}</h3></a>')
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        title.setOpenExternalLinks(True)
        morphology = QLabel(data.short_record())
        tags = QLabel(f'Tags: {data.pos}')
        translations = ', '.join(data.lexemes[0].translations.get(translate, ['<no translation>'])[:3])
        translations = QLabel(translations)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(title)
        layout.addWidget(morphology)
        layout.addWidget(tags)
        layout.addWidget(translations)
        self.setLayout(layout)


class SelectorRow(QWidget):
    selected = pyqtSignal(str)
    selected_index = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._buttons = QButtonGroup()
        self._buttons.idToggled.connect(self._button_toggled)
        self._label = QLabel()
        self._layout = QHBoxLayout()
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
