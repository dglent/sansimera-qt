# Purpose: Display the events of the day back in the history
# from the website www.sansimera.gr
# Author: Dimitrios Glentadakis dglent@free.fr
# License: GPLv3

from PyQt5.QtCore import (
    QThread, QTimer, Qt, QSettings, QByteArray, pyqtSignal,
    QT_VERSION_STR, PYQT_VERSION_STR
)
from PyQt5.QtGui import QIcon, QCursor, QTextCursor, QTextDocument
from PyQt5.QtWidgets import (
    QAction, QMainWindow, QApplication, QSystemTrayIcon,
    QMenu, QTextBrowser, QToolBar, QMessageBox
)
import re
import platform
import sys

try:
    import qrc_resources
    import sansimera_data
    import sansimera_fetch
    import sansimera_reminder
except:
    from sansimera_qt import qrc_resources
    from sansimera_qt import sansimera_data
    from sansimera_qt import sansimera_fetch
    from sansimera_qt import sansimera_reminder

__version__ = "0.7"


class Sansimera(QMainWindow):
    def __init__(self, parent=None):
        super(Sansimera, self).__init__(parent)
        self.settings = QSettings()
        self.timer = QTimer(self)
        self.timer_reminder = QTimer(self)
        self.timer_reminder.timeout.connect(self.reminder_tray)
        interval = self.settings.value('Interval') or '1'
        if interval != '0':
            self.timer_reminder.start(int(interval) * 60 * 60 * 1000)
        self.tentatives = 0
        self.gui()
        self.lista = []
        self.lista_pos = 0
        self.eortazontes_shown = False
        self.eortazontes_names = ''

    def gui(self):
        self.systray = QSystemTrayIcon()
        self.icon = QIcon(':/sansimera.png')
        self.systray.setIcon(self.icon)
        self.systray.setToolTip('Σαν σήμερα...')
        self.menu = QMenu()
        self.exitAction = QAction('&Έξοδος', self)
        self.refreshAction = QAction('&Ανανέωση', self)
        self.aboutAction = QAction('&Σχετικά', self)
        self.notification_interval = QAction('Ει&δοποίηση εορταζόντων', self)
        self.menu.addAction(self.notification_interval)
        self.menu.addAction(self.refreshAction)
        self.menu.addAction(self.aboutAction)
        self.menu.addAction(self.exitAction)
        self.systray.setContextMenu(self.menu)
        self.notification_interval.triggered.connect(self.interval_namedays)
        self.exitAction.triggered.connect(exit)
        self.refreshAction.triggered.connect(self.refresh)
        self.aboutAction.triggered.connect(self.about)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.setWindowIcon(self.icon)
        self.setWindowTitle('Σαν σήμερα...')
        self.setCentralWidget(self.browser)
        self.systray.show()
        self.systray.activated.connect(self.activate)
        self.browser.append('Λήψη...')
        nicon = QIcon(':/next')
        picon = QIcon(':/previous')
        ricon = QIcon(':/refresh')
        iicon = QIcon(':/info')
        qicon = QIcon(':/exit')
        inicon = QIcon(':/notifications')
        self.nextAction = QAction('Επόμενο', self)
        self.nextAction.setIcon(nicon)
        self.previousAction = QAction('Προηγούμενο', self)
        self.refreshAction.triggered.connect(self.refresh)
        self.nextAction.triggered.connect(self.nextItem)
        self.previousAction.triggered.connect(self.previousItem)
        self.previousAction.setIcon(picon)
        self.refreshAction.setIcon(ricon)
        self.exitAction.setIcon(qicon)
        self.aboutAction.setIcon(iicon)
        self.notification_interval.setIcon(inicon)
        controls = QToolBar()
        self.addToolBar(Qt.BottomToolBarArea, controls)
        controls.setObjectName('Controls')
        controls.addAction(self.previousAction)
        controls.addAction(self.nextAction)
        controls.addAction(self.refreshAction)
        self.restoreGeometry(self.settings.value("MainWindow/Geometry", QByteArray()))
        self.refresh()

    def interval_namedays(self):
        dialog = sansimera_reminder.Reminder(self)
        dialog.applied_signal['QString'].connect(self.reminder)
        dialog.exec_()

    def reminder(self, time):
        self.settings.setValue('Interval', time)
        if time != '0':
            self.timer_reminder.start(int(time) * 60 * 60 * 1000)

    def nextItem(self):
        if len(self.lista) >= 1:
            self.browser.clear()
            if self.lista_pos != len(self.lista) - 1:
                self.lista_pos += 1
            else:
                self.lista_pos = 0
            self.browser.append(self.lista[self.lista_pos])
            self.browser.moveCursor(QTextCursor.Start)
        else:
            return

    def previousItem(self):
        if len(self.lista) >= 1:
            self.browser.clear()
            if self.lista_pos == 0:
                self.lista_pos = len(self.lista) - 1
            else:
                self.lista_pos -= 1
            self.browser.append(self.lista[self.lista_pos])
            self.browser.moveCursor(QTextCursor.Start)
        else:
            return

    def refresh(self):
        try:
            if self.workThread.isRunning():
                return
        except AttributeError:
            pass
        self.menu.hide()
        self.browser.clear()
        self.lista = []
        self.systray.setToolTip('Σαν σήμερα...')
        self.browser.append('Λήψη...')
        self.tentatives = 0
        self.eortazontes_shown = False
        self.download()

    def activate(self, reason):
        self.menu.hide()
        state = self.isVisible()
        if reason == 3:
            if state:
                self.hide()
                return
            else:
                self.show()
                return
        if reason == 1:
            self.menu.hide()
            self.menu.popup(QCursor.pos())

    def download(self):
        self.gnomika_html = ''
        self.workThread = WorkThread()
        self.workThread.online_signal[bool].connect(self.status)
        self.workThread.finished.connect(self.window)
        self.workThread.event['QString'].connect(self.addlist)
        self.workThread.names['QString'].connect(self.nameintooltip)
        self.workThread.orthodox_signal.connect(self.orthodox_synarxistis)
        self.workThread.gnomika_signal.connect(self.gnomika)
        self.workThread.start()

    def gnomika(self, html):
        self.gnomika_html = html

    def orthodox_synarxistis(self, html):
        self.lista.append(html)

    def addlist(self, text):
        self.lista.append(text)

    def status(self, status):
        self.status_online = status

    def reminder_tray(self):
        text = self.eortazontes_names.replace('<br/>', '\n')
        urltexts = re.findall('(<a [\S]+php">)', text)
        urltexts.extend(['</a>', '<p>', '<div>'])
        show_notifier_text = text
        for i in urltexts:
            show_notifier_text = show_notifier_text.replace(i, '')
        show_notifier_text = show_notifier_text.replace('\n\n', '\n')
        show_notifier_text = show_notifier_text.replace('www.eortologio.gr)', 'www.eortologio.gr)\n')
        self.systray.showMessage('', show_notifier_text)
        self.systray.setToolTip(show_notifier_text)

    def nameintooltip(self, text):
        self.eortazontes_names = text
        for i in ['<br/>', '<div>']:
            text = text.replace(i, '')
        self.eortazontes_in_window = text
        if self.eortazontes_shown:
            return
        self.reminder_tray()
        self.eortazontes_shown = True

    def window(self):
        # Add the gnomika at the end while downloading the images
        self.lista.append(self.gnomika_html)
        if self.status_online:
            self.browser.clear()
            self.browser.append(self.lista[0])
            self.browser.moveCursor(QTextCursor.Start)
            self.lista_pos = 0
            return
        else:
            if self.tentatives == 10:
                return
            self.timer.singleShot(5000, self.refresh)
            self.tentatives += 1

    def hideEvent(self, event):
        self.settings.setValue("MainWindow/Geometry", self.saveGeometry())

    def closeEvent(self, event):
        self.settings.setValue("MainWindow/Geometry", self.saveGeometry())

    def about(self):
        self.menu.hide()
        QMessageBox.about(
            self,
            "Εφαρμογή «Σαν σήμερα...»",
            """<b>sansimera-qt</b> v{0}
            <p>Δημήτριος Γλενταδάκης <a href="mailto:dglent@free.fr">dglent@free.fr</a>
            <br/>Ιστοσελίδα: <a href="https://github.com/dglent/sansimera-qt">
            github sansimera-qt</a>
            <p>Εφαρμογή πλαισίου συστήματος για την προβολή
            <br/>των γεγονότων από την ιστοσελίδα <a href="http://www.sansimera.gr">
            www.sansimera.gr</a><br/>
            Πηγή εορτολογίου: <a href="http://www.saint.gr/index.aspx">
            www.saint.gr</a><br/>
            Πηγή γνωμικών:<a href="https://www.gnomikologikon.gr">
            www.gnomikologikon.gr</a>
            <p>Άδεια χρήσης: GPLv3 <br/>Python {1} - Qt {2} - PyQt {3} σε {4}""".format(
                __version__, platform.python_version(),
                QT_VERSION_STR, PYQT_VERSION_STR, platform.system()
            )
        )


class WorkThread(QThread):
    online_signal = pyqtSignal([bool])
    event = pyqtSignal(['QString'])
    names = pyqtSignal(['QString'])
    orthodox_signal = pyqtSignal(['QString'])
    gnomika_signal = pyqtSignal(['QString'])

    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        fetch = sansimera_fetch.Sansimera_fetch()
        fetch.html()
        orthodox_names = fetch.orthodoxos_synarxistis()
        gnomika = fetch.gnomika()
        self.orthodox_signal.emit(orthodox_names)
        self.gnomika_signal.emit(gnomika)
        doc = QTextDocument()
        doc.setHtml(orthodox_names)
        text = doc.toPlainText()
        self.names.emit(text)

        online = fetch.online
        data = sansimera_data.Sansimera_data()
        lista = data.getAll()
        for i in lista:
            self.event['QString'].emit(i)
        self.online_signal[bool].emit(online)
        return


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setOrganizationName('sansimera-qt')
    app.setOrganizationDomain('sansimera-qt')
    app.setApplicationName('sansimera-qt')
    prog = Sansimera()
    app.exec_()


if __name__ == '__main__':
    main()
