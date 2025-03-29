import anki.lang
from aqt.qt import (
    pyqtSignal, Qt, QEvent, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QButtonGroup, QStackedWidget, QScrollArea, QFrame, QMessageBox,
    QCheckBox
)
from aqt.operations import QueryOp
from aqt.theme import theme_manager
from aqt import mw, colors, gui_hooks

from ..sonaveeb import Sonaveeb, SonaveebMode
from ..notetypes import NoteTypeManager
from ..globals import REQUEST_TIMEOUT
from .word_info import WordInfoPanel
from .common import VSeparator, ShrinkingComboBox


class SonaveebDialog(QWidget):
    def __init__(self, notetype_manager=None, sonaveeb=None, parent=None):
        super().__init__(parent=parent)
        self._notetype_manager = notetype_manager or NoteTypeManager()
        self._sonaveeb = sonaveeb or Sonaveeb()
        self._config = mw.addonManager.getConfig(__name__)

        notetype_manager.create_missing_defaults()

        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle('Sõnaveeb Deck Builder')
        self.resize(700, 800)

        # Add header bar
        # - Add deck selector
        self._deck_selector = ShrinkingComboBox()
        self._deck_selector.setMinimumWidth(100)
        self._refresh_deck_list()
        self._deck_selector.currentIndexChanged.connect(self._on_deck_changed)
        self._deck_selector.setPlaceholderText('None')
        deck_label = QLabel('&Deck:')
        deck_label.setStyleSheet(f'font-size: 10pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        deck_label.setBuddy(self._deck_selector)
        deck_layout = QVBoxLayout()
        deck_layout.addWidget(deck_label)
        deck_layout.addWidget(self._deck_selector)

        # - Add note type selector
        self._notetype_selector = ShrinkingComboBox()
        self._notetype_selector.setMinimumWidth(100)
        self._refresh_notetype_list()
        self._notetype_selector.currentIndexChanged.connect(self._on_notetype_changed)
        self._notetype_selector.setPlaceholderText('None')
        notetype_label = QLabel('&Note Type:')
        notetype_label.setStyleSheet(f'font-size: 10pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        notetype_label.setBuddy(self._notetype_selector)
        self._notetype_update_button = QPushButton('Apply Updates')
        self._notetype_update_button.setStyleSheet('font-size: 10pt')
        self._notetype_update_button.clicked.connect(self._apply_notetype_updates)
        notetype_title_layout = QHBoxLayout()
        notetype_title_layout.setContentsMargins(0, 0, 0, 0)
        notetype_title_layout.addWidget(notetype_label)
        notetype_title_layout.addWidget(self._notetype_update_button)
        notetype_layout = QVBoxLayout()
        notetype_layout.addLayout(notetype_title_layout)
        notetype_layout.addWidget(self._notetype_selector)

        # - Add language selector
        languages = {
            code.split('_')[0]: name.split(' ')[0]
            for name, code in anki.lang.langs
        }
        # - Fix language name typos
        languages['uk'] = 'Українська'
        languages['jbo'] = 'Lojban'
        self._lang_selector = ShrinkingComboBox()
        self._lang_selector.setMinimumWidth(100)
        for code, lang in languages.items():
            self._lang_selector.addItem(lang, userData=code)
        self._lang_selector.currentIndexChanged.connect(self._on_language_changed)
        lang_label = QLabel('&Translate into:')
        lang_label.setStyleSheet(f'font-size: 10pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        lang_label.setBuddy(self._lang_selector)
        lang_layout = QVBoxLayout()
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self._lang_selector)

        # - Add mode selector
        mode_tooltip = (
            'Sõnaveeb mode:\n'
            f"- {SonaveebMode.Lite.name}: Learner's Sõnaveeb - dictionary for "
            "language learners with simpler definitions and examples.\n"
            f"- {SonaveebMode.Advanced.name}: Full Sõnaveeb - comprehensive "
            "dictionary with detailed information."
        )
        self._mode_selector = ShrinkingComboBox()
        self._mode_selector.setMinimumWidth(100)
        for mode in SonaveebMode:
            self._mode_selector.addItem(mode.name, userData=mode)
        self._mode_selector.currentIndexChanged.connect(self._on_mode_changed)
        self._mode_selector.setToolTip(mode_tooltip)
        mode_label = QLabel('Sõnaveeb &Mode:')
        mode_label.setToolTip(mode_tooltip)
        mode_label.setStyleSheet(f'font-size: 10pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        mode_label.setBuddy(self._mode_selector)
        mode_layout = QVBoxLayout()
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self._mode_selector)

        # - Add audio checkbox
        audio_tooltip = 'Save pronunciation audio into the notes'
        self._audio_checkbox = QCheckBox()
        self._audio_checkbox.toggled.connect(self._on_save_audio_changed)
        self._audio_checkbox.setToolTip(audio_tooltip)
        audio_label = QLabel('&Audio:')
        audio_label.setToolTip(audio_tooltip)
        audio_label.setStyleSheet(f'font-size: 10pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        audio_label.setBuddy(self._mode_selector)
        audio_layout = QVBoxLayout()
        audio_layout.addWidget(audio_label)
        audio_layout.addWidget(self._audio_checkbox)
        audio_layout.setAlignment(self._audio_checkbox, Qt.AlignmentFlag.AlignHCenter)

        # - Populate header bar
        header_layout = QHBoxLayout()
        header_layout.addLayout(deck_layout)
        header_layout.addWidget(VSeparator(QFrame.Shadow.Sunken))
        header_layout.addLayout(notetype_layout)
        header_layout.addStretch(1)
        header_layout.addWidget(VSeparator(QFrame.Shadow.Sunken))
        header_layout.addLayout(lang_layout)
        header_layout.addWidget(VSeparator(QFrame.Shadow.Sunken))
        header_layout.addLayout(mode_layout)
        header_layout.addWidget(VSeparator(QFrame.Shadow.Sunken))
        header_layout.addLayout(audio_layout)
        header_layout.setContentsMargins(10, 5, 10, 5)
        self._header_bar = QWidget()
        # CSS properties marked with "Native theme" comment simply duplicate
        # Anki theme values (qt/aqt/stylesheets.py) necessary to fix some issues
        # with the native theme.
        self._header_bar.setStyleSheet(f'''
            QWidget {{
                background: {theme_manager.var(colors.CANVAS_ELEVATED)};
            }}
            QComboBox {{
                border: none;
                /* Native theme: fix spacing between drop-down arrow and the list */
                padding-left: 6px;
            }}
            QComboBox::drop-down {{
                subcontrol-position: center left;
                /* Native theme: disable button shadows */
                border-style: solid;
            }}
            /* Native theme: replace drop-down icon, otherwise it becomes invisible with disabled border */
            QComboBox::down-arrow {{
                image: url({theme_manager.themed_icon("mdi:chevron-down")});
            }}
            QComboBox::down-arrow:disabled {{
                image: url({theme_manager.themed_icon("mdi:chevron-down-FG_DISABLED")});
            }}
        ''')
        self._header_bar.setLayout(header_layout)

        # Add search bar
        self._search = QLineEdit()
        self._search.setFocus()
        self._search.returnPressed.connect(self._on_search_triggered)
        self._search_button = QPushButton('Search')
        self._search_button.clicked.connect(self._on_search_triggered)
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
        self._form_selector.selected.connect(self._on_form_selected)
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

        report_link = QLabel('See any mistakes or other problems? Please report <a href="https://github.com/azymohliad/anki-sonaveeb/issues">here</a>')
        report_link.setTextFormat(Qt.TextFormat.RichText)
        report_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        report_link.setOpenExternalLinks(True)
        report_link.setStyleSheet(f'font-size: 9pt; color: {theme_manager.var(colors.FG_SUBTLE)}')
        report_link.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        layout = QVBoxLayout()
        layout.addWidget(self._header_bar)
        layout.addWidget(search_bar)
        layout.addWidget(self._content_stack)
        layout.addWidget(report_link)
        layout.setAlignment(search_bar, Qt.AlignmentFlag.AlignHCenter)
        layout.setContentsMargins(0, 0, 0, 5)
        self.setLayout(layout)
        self._search.setFocus()
        self.set_status('Search something :)')

        self._apply_notetype_updates()
        gui_hooks.theme_did_change.append(self._on_theme_changed)

        # Restore config
        # - Deck
        deck_id = self._config.get('deck')
        index_deck = self._deck_selector.findData(deck_id)
        if index_deck >= 0:
            self._deck_selector.setCurrentIndex(index_deck)
        # - Note Type
        notetype = self._config.get('notetype')
        index_notetype = self._notetype_selector.findData(notetype)
        if index_notetype >= 0:
            self._notetype_selector.setCurrentIndex(index_notetype)
        # - Translation language
        default_lang = anki.lang.get_def_lang()[1].split('_')[0]
        lang = self._config.get('language', default_lang)
        index_lang = self._lang_selector.findData(lang)
        if index_lang >= 0:
            self._lang_selector.setCurrentIndex(index_lang)
        # - Sonaveeb modes
        try:
            mode = SonaveebMode[self._config.get('mode')]
        except KeyError:
            mode = Sonaveeb.DEFAULT_MODE
        self._mode_selector.setCurrentText(mode.name)
        # - Audio
        save_audio = self._config.get('save_audio', False)
        self._audio_checkbox.setChecked(save_audio)

        # Track Google translate requests in progress
        self.pending_translation_requests = set()

    def language_code(self):
        return self._lang_selector.currentData()

    def deck_id(self):
        return self._deck_selector.currentData()

    def notetype_id(self):
        return self._notetype_selector.currentData()

    def sonaveeb_mode(self):
        return self._mode_selector.currentData()

    def save_audio(self):
        return self._audio_checkbox.isChecked()

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
        self._lang_selector.setEnabled(True)

    def _request_search(self, query):
        self._search_button.setEnabled(False)
        self._mode_selector.setEnabled(False)
        self._search.setEnabled(False)
        self.set_status('Searching...')
        operation = QueryOp(
            parent=self,
            op=lambda col: self._search_candidates(query, REQUEST_TIMEOUT),
            success=self._on_search_results_received
        ).failure(self._on_search_error)
        operation.run_in_background()

    def _search_candidates(self, query, timeout=None):
        match, forms = self._sonaveeb.get_base_form(query, timeout=timeout)
        if match is not None:
            references = self._sonaveeb.get_references(match, timeout=timeout)
        else:
            references = []
        return references, forms

    def _save_config_value(self, key, value):
        self._config[key] = value
        mw.addonManager.writeConfig(__name__, self._config)

    def _on_search_triggered(self):
        self.clear_search_results()
        query = self._search.text().strip()
        if query != '':
            self._request_search(query)
        else:
            self.set_status('Search something :)')

    def _on_theme_changed(self):
        self._header_bar.setStyleSheet(f'background: {theme_manager.var(colors.CANVAS_ELEVATED)}')

    def _on_form_selected(self, form):
        print(f'Selected form: {form}')
        self._search.setText(form)
        self._on_search_triggered()

    def _on_language_changed(self, _index):
        lang = self.language_code()
        for word_panel in self.search_results():
            word_panel.set_translation_language(lang)
        self._save_config_value('language', lang)

    def _on_mode_changed(self, _index):
        mode = self.sonaveeb_mode()
        self._sonaveeb.set_mode(mode)
        self._save_config_value('mode', mode.name)
        if self._search.text().strip():
            self._on_search_triggered()

    def _on_deck_changed(self, _index):
        deck_id = self.deck_id()
        for word_panel in self.search_results():
            word_panel.set_deck_id(deck_id)
        self._save_config_value('deck', deck_id)

    def _on_notetype_changed(self, _index):
        notetype_id = self.notetype_id()
        notetype = mw.col.models.get(notetype_id)
        for word_panel in self.search_results():
            word_panel.set_notetype(notetype)
        self._save_config_value('notetype', notetype_id)

    def _on_save_audio_changed(self, save_audio):
        for word_panel in self.search_results():
            word_panel.set_save_audio(save_audio)
        self._save_config_value('save_audio', save_audio)

    def _on_search_results_received(self, result):
        references, forms = result
        self._search_button.setEnabled(True)
        self._mode_selector.setEnabled(True)
        self._search.setEnabled(True)
        self._search.setFocus()
        if len(references) == 0:
            if len(forms) == 0:
                self.set_status('Not found :(')
            elif len(forms) == 1:
                self._request_search(forms[0])
            else:
                self._form_selector.set_label('Select base form:')
                self._form_selector.set_options(forms)
                self._form_selector.show()
                self._content_stack.setCurrentWidget(self._content)
        else:
            self._form_selector.set_options(forms)
            self._form_selector.set_label('See also:')
            self._form_selector.setVisible(len(forms) > 0)
            self._content_stack.setCurrentWidget(self._content)
            notetype = mw.col.models.get(self.notetype_id())
            for reference in references:
                word_panel = WordInfoPanel(reference, self._sonaveeb, self.deck_id(), notetype, self.language_code())
                word_panel.set_save_audio(self.save_audio())
                word_panel.translations_requested.connect(self._on_word_translation_requested)
                self._search_results_layout.addWidget(word_panel)

    def _on_search_error(self, error):
        print(error)
        self.set_status('Search failed :(\nPlease retry')
        self._search_button.setEnabled(True)
        self._mode_selector.setEnabled(True)
        self._search.setEnabled(True)
        self._search.setFocus()

    def _on_word_translation_requested(self, active):
        widget = self.sender()
        if active:
            if not self.pending_translation_requests:
                # The first translation request started
                self._lang_selector.setEnabled(False)
            self.pending_translation_requests.add(widget.word_info.word_id)
        else:
            self.pending_translation_requests.discard(widget.word_info.word_id)
            if not self.pending_translation_requests:
                # The last translation request finished
                self._lang_selector.setEnabled(True)

    def _refresh_combobox(self, combobox, items):
        # Remove redundant items
        for i in reversed(range(combobox.count())):
            name = combobox.itemText(i)
            data = combobox.itemData(i)
            if not any([n == name and d == data for n, d in items]):
                combobox.removeItem(i)
        # Add missing items
        for name, data in items:
            idx = combobox.findText(name)
            if idx == -1:
                combobox.addItem(name, userData=data)
        # Select first item if none is selected
        if combobox.currentIndex() == -1 and combobox.count() > 0:
            combobox.setCurrentIndex(0)

    def _refresh_notetype_list(self):
        notetypes = self._notetype_manager.get_valid_notetypes()
        items = [(nt['name'], nt['id']) for nt in notetypes]
        self._refresh_combobox(self._notetype_selector, items)

    def _refresh_deck_list(self):
        decks = mw.col.decks.all_names_and_ids()
        items = [(d.name, d.id) for d in decks]
        self._refresh_combobox(self._deck_selector, items)

    def _check_notetypes_updates(self):
        notetypes = self._notetype_manager.get_intended_notetypes()
        updates = [self._notetype_manager.get_pending_update(n) for n in notetypes]
        available = any([not u.is_empty() for u in updates])
        self._notetype_update_button.setVisible(available)

    def _apply_notetype_updates(self):
        notetypes = self._notetype_manager.get_intended_notetypes()
        updates = [self._notetype_manager.get_pending_update(n) for n in notetypes]
        required = any([u.is_required() for u in updates])
        can_or_need = 'need to' if required else 'can'
        if any([u.is_consequential() for u in updates]):
            # If there are consequential note type updates, ask user to confirm
            # If all note type updates are purely additive or cosmetic,
            # update without bothering a user
            message = (
                f'Sõnaveeb note types {can_or_need} be updated, but some of the '
                'changes are consequential and require your confirmation.'
            )
            message += '<ol>'
            for notetype, update in zip(notetypes, updates):
                if update.is_empty():
                    continue
                message += f'<li>{notetype["name"]}:<ul>'
                if update.fields_to_add:
                    message += f'<li>Add fields: {", ".join(update.fields_to_add)}</li>'
                if update.fields_to_remove:
                    message += f'<li>Remove fields: {", ".join(update.fields_to_remove)}</li>'
                if update.templates_to_add:
                    message += f'<li>Add card templates: {", ".join(update.templates_to_add)}</li>'
                if update.templates_to_remove:
                    message += f'<li>Remove card templates: {", ".join(update.templates_to_remove)}</li>'
                if update.templates_to_update:
                    message += f'<li>Update card templates: {", ".join(update.templates_to_update)}</li>'
                if update.style:
                    message += '<li>Change style</li>'
                if update.fields_order:
                    message += '<li>Change fields order</li>'
                message += '</ul></li>'
            message += '</ol>'
            message += (
                '<br>'
                'These changes may affect your collection, so it is recommended '
                'to create a backup before applying the updates (File -> Create Backup).'
                '<br><br>'
                'Would you like to apply these updates now?'
            )
            answer = QMessageBox.question(
                mw,
                'Update note types?',
                message,
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.No
            )
            if answer == QMessageBox.StandardButton.No:
                return
        # Apply updates
        for notetype, update in zip(notetypes, updates):
            if not update.is_empty():
                self._notetype_manager.update_notetype(notetype)
        # Hide update button
        self._notetype_update_button.hide()
        self._refresh_notetype_list()

    # QWidget overrides
    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                # Window activated
                # On a laptop with NVMe SSD and a relatively small Anki database
                # these checks usually take approximately 0.5 ms, while a single
                # database query within them is usually between 0.05 to 0.15 ms.
                # Theoretically, one note type DB query could be optimized away,
                # and reused for _refresh_notetype_list and _check_notetypes_updates,
                # but it's probably not worth the added complexity.
                self._refresh_deck_list()
                self._refresh_notetype_list()
                self._check_notetypes_updates()


class SelectorRow(QWidget):
    selected = pyqtSignal(str)
    selected_index = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._buttons = QButtonGroup()
        self._buttons.idToggled.connect(self._on_button_toggled)
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

    def _on_button_toggled(self, index, checked):
        if checked:
            self.selected.emit(self._buttons.button(index).text())
            self.selected_index.emit(index)
