from aqt.qt import QFrame, QComboBox, Qt, QSizePolicy, QStyle, QStyleOptionComboBox


class HSeparator(QFrame):
    def __init__(self, shadow: QFrame.Shadow = QFrame.Shadow.Plain):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(shadow)


class VSeparator(QFrame):
    def __init__(self, shadow: QFrame.Shadow = QFrame.Shadow.Plain):
        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(shadow)


class ShrinkingComboBox(QComboBox):
    '''ComboBox that shrinks to the width of the currently selected item.
    '''
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.currentTextChanged.connect(self.updateGeometry)

    def sizeHint(self):
        text = self.currentText()
        metrics = self.fontMetrics()
        text_size = metrics.size(Qt.TextFlag.TextSingleLine, text)
        style_opt = QStyleOptionComboBox()
        self.initStyleOption(style_opt)
        size = self.style().sizeFromContents(
            QStyle.ContentsType.CT_ComboBox,
            style_opt,
            text_size,
            self
        )
        return size

    def minimumSizeHint(self):
        return self.sizeHint()

    def showPopup(self):
        # Make sure the drop-down list is wide enough to fit all items
        # (this seems unnecessary on Linux, but is needed on MacOS)
        metrics = self.fontMetrics()
        widths = [
            metrics.horizontalAdvance(self.itemText(i))
            for i in range(self.count())
        ]
        widths.append(self.width())
        self.view().setMinimumWidth(max(widths))
        super().showPopup()
