from PyQt5.QtCore import Qt, pyqtSignal, QSettings
from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QSpinBox, QHBoxLayout,
                            QDialogButtonBox, QGridLayout, QDialog)


class Reminder(QDialog):
    applied_signal = pyqtSignal(['QString'])

    def __init__(self, parent=None):
        super(Reminder, self).__init__(parent)
        self.settings = QSettings()
        self.layout = QVBoxLayout()
        self.interval_namedays()
        self.buttonbox()
        self.setLayout(self.layout)

    def interval_namedays(self):
        interval_label = QLabel('Χρονικό διάστημα ειδοποιήσης εορταζόντων\n0 = χωρίς ειδοποίηση')
        interval_unit = QLabel('ώρες')
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(0, 24)
        time = self.settings.value('Interval') or '1'
        self.interval_spinbox.setValue(int(time))
        grid = QGridLayout()
        grid.addWidget(interval_label, 0, 0)
        grid.addWidget(self.interval_spinbox, 0, 1)
        grid.addWidget(interval_unit, 0, 2)
        self.layout.addLayout(grid)

    def buttonbox(self):
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonBox = QDialogButtonBox()
        buttonBox.setOrientation(Qt.Horizontal)
        buttonBox.setStandardButtons(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.setContentsMargins(0, 30, 0, 0)
        buttonLayout.addWidget(buttonBox)
        self.layout.addLayout(buttonLayout)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def accept(self):
        interval = str(self.interval_spinbox.value())
        self.applied_signal.emit(interval)
        QDialog.accept(self)
