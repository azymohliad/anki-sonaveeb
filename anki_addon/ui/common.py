from aqt.qt import QFrame, QComboBox, QFontMetrics, QSize, Qt, QSizePolicy


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
        metrics = QFontMetrics(self.view().font())
        width = metrics.size(Qt.TextFlag.TextSingleLine, text).width()
        width += 40 # TODO: Add correct drop-down button width
        return QSize(width, super().sizeHint().height())

    def minimumSizeHint(self):
        return self.sizeHint()
