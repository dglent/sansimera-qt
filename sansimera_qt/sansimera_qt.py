# Purpose: Display the events of the day back in the history
# from the website www.sansimera.gr
# Author: Dimitrios Glentadakis dglent@free.fr
# License: GPLv3

from PyQt5.QtCore import (
    QThread, QTimer, Qt, QSettings, QByteArray, pyqtSignal,
    QT_VERSION_STR, PYQT_VERSION_STR
)
from PyQt5.QtGui import QIcon, QCursor, QTextCursor
from PyQt5.QtWidgets import (
    QAction, QMainWindow, QApplication, QSystemTrayIcon,
    QMenu, QTextBrowser, QToolBar, QMessageBox
)
import logging
import re
import platform
import sys
import datetime
import traceback
import os
from io import StringIO

try:
    import qrc_resources
    import sansimera_data
    import sansimera_fetch
    import sansimera_reminder
except ImportError:
    from sansimera_qt import qrc_resources
    from sansimera_qt import sansimera_data
    from sansimera_qt import sansimera_fetch
    from sansimera_qt import sansimera_reminder

__version__ = "1.2.0"


def configure_logging():
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    settings = QSettings()
    logLevel = settings.value('Logging/Level')
    if logLevel == '' or logLevel is None:
        logLevel = 'DEBUG'
        settings.setValue('Logging/Level', logLevel)

    logPath = os.path.dirname(settings.fileName())
    logFile = f'{logPath}/sansimera.log'

    try:
        if not os.path.exists(logPath):
            os.makedirs(logPath)
        if os.path.isfile(logFile):
            fsize = os.stat(logFile).st_size
            if fsize > 10240000:
                with open(logFile, 'rb') as rFile:
                    rFile.seek(102400)
                    logData = rFile.read()
                with open(logFile, 'wb') as wFile:
                    wFile.write(logData)
                del logData
        logging.basicConfig(
            format='%(asctime)s %(levelname)s: %(message)s'
            ' - %(lineno)s: %(module)s',
            datefmt='%Y/%m/%d %H:%M:%S',
            filename=logFile,
            level=logLevel
        )
    except OSError:
        logFile = '/tmp/sansimera.log'
        logging.basicConfig(
            format='%(asctime)s %(levelname)s: %(message)s'
            ' - %(lineno)s: %(module)s',
            datefmt='%Y/%m/%d %H:%M:%S',
            filename=logFile,
            level=logLevel
        )
    logger = logging.getLogger('sansimera-qt')
    logger.setLevel(logLevel)

    handlerStream = logging.StreamHandler()
    loggerStreamFormatter = logging.Formatter(
        '%(levelname)s: %(message)s - %(lineno)s: %(module)s'
    )
    handlerStream.setFormatter(loggerStreamFormatter)
    root_logger.addHandler(handlerStream)
    os.environ['SANSIMERA_QT_LOG_FILE'] = logFile
    os.environ['SANSIMERA_QT_LOG_LEVEL'] = logLevel
    logging.info('Logging started: %s', logFile)
    logging.info('sansimera-qt version: %s', __version__)
    logging.debug('Settings file: %s', settings.fileName())
    logging.debug('Working directory: %s', os.getcwd())
    logging.debug('argv: %s', sys.argv)
    logging.debug('DISPLAY=%s', os.environ.get('DISPLAY'))
    logging.debug('XDG_RUNTIME_DIR=%s', os.environ.get('XDG_RUNTIME_DIR'))
    return logFile


class Sansimera(QMainWindow):
    def __init__(self, parent=None):
        super(Sansimera, self).__init__(parent)
        logging.debug('Initializing main window')
        self.settings = QSettings()
        self.timer = QTimer(self)
        self.timer_reminder = QTimer(self)
        self.timer_reminder.timeout.connect(self.reminder_tray)
        interval = self.settings.value('Interval') or '1'
        if interval != '0':
            self.timer_reminder.start(int(interval) * 60 * 60 * 1000)
        self.tentatives = 0
        self.refresh_pending = False
        self.gui()
        self.lista = []
        self.lista_pos = 0
        self.status_online = False
        self.eortazontes_shown = False
        self.eortazontes_names = ''

    def gui(self):
        logging.debug('Building UI')
        self.systray = QSystemTrayIcon()
        self.icon = QIcon(':/sansimera.png')
        toggle_icon = QIcon(':/toggle_window')
        self.systray.setIcon(self.icon)
        self.systray.setToolTip('Σαν σήμερα...')
        self.menu = QMenu()
        self.exitAction = QAction('&Έξοδος', self)
        self.refreshAction = QAction('&Ανανέωση', self)
        self.aboutAction = QAction('&Σχετικά', self)
        toggle_window_action = QAction('Εναλλαγή παραθύρου', self)
        toggle_window_action.setIcon(toggle_icon)
        toggle_window_action.triggered.connect(self.toggle_main_window)
        self.menu.addAction(toggle_window_action)
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
        logging.debug('Initial refresh requested from gui setup')
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
        logging.info('Refresh requested')
        try:
            if self.workThread.isRunning():
                logging.info('Refresh requested while worker is running; queued')
                self.refresh_pending = True
                self.systray.setToolTip('Αναμονή για ανανέωση')
                self.browser.clear()
                self.browser.append('Αναμονή για ανανέωση...')
                return
        except AttributeError:
            logging.debug('No existing worker before refresh')
            pass
        self.menu.hide()
        self.refreshAction.setEnabled(False)
        self.browser.clear()
        self.lista = []
        self.systray.setToolTip('Σαν σήμερα...')
        self.browser.append('Λήψη...')
        logging.debug('Displayed loading message')
        self.tentatives = 0
        self.eortazontes_shown = False
        self.download()

    def toggle_main_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

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
        logging.debug('Starting download worker')
        self.gnomika_html = ''
        self.workThread = WorkThread()
        self.workThread.online_signal.connect(self.status)
        self.workThread.finished.connect(self.window)
        self.workThread.event.connect(self.addlist)
        self.workThread.names.connect(self.nameintooltip)
        self.workThread.orthodox_signal.connect(self.orthodox_synarxistis)
        self.workThread.gnomika_signal.connect(self.gnomika)
        self.workThread.start()
        logging.debug('Download worker started')

    def gnomika(self, html):
        logging.debug('Received gnomika html, length=%s', len(html or ''))
        self.gnomika_html = html

    def orthodox_synarxistis(self, html):
        logging.debug('Received orthodox html, length=%s', len(html or ''))
        self.lista.append(html)
        self.browser.clear()
        self.browser.append(html)

    def addlist(self, text):
        logging.debug('Received event item, length=%s', len(text or ''))
        self.lista.append(text)

    def status(self, status):
        logging.info('Online status received: %s', status)
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
        self.systray.setToolTip(show_notifier_text.replace(',', '\n'))

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
        logging.debug('Worker finished; list items=%s, online=%s', len(self.lista), self.status_online)
        # Add the gnomika at the end while downloading the images
        self.lista.append(self.gnomika_html)
        if self.status_online or len(self.lista) > 0:
            self.browser.clear()
            self.browser.append(self.lista[0])
            self.browser.moveCursor(QTextCursor.Start)
            self.lista_pos = 0
            logging.debug('Main window updated with first item')
        else:
            logging.warning('Worker finished without data to display')
        if self.refresh_pending:
            logging.info('Running queued refresh')
            self.refresh_pending = False
            QTimer.singleShot(0, self.refresh)
        else:
            self.refreshAction.setEnabled(True)

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
        logging.debug('Worker run started')
        try:
            fetch = sansimera_fetch.Sansimera_fetch()
            logging.debug('Fetching sansimera html')
            fetch.html()
            logging.debug('Sansimera fetch done; online=%s error=%s', fetch.online, fetch.last_error)
            logging.debug('Fetching orthodox names')
            orthodox_names, err = fetch.orthodoxos_synarxistis()
            logging.debug('Orthodox fetch done; success=%s error=%s', bool(orthodox_names), err)
            logging.debug('Fetching gnomika')
            gnomika = fetch.gnomika()
            logging.debug('Gnomika fetch done, length=%s', len(gnomika or ''))

            self.gnomika_signal.emit(gnomika)
            # emit Text or False
            self.orthodox_signal.emit(orthodox_names or err)
            if orthodox_names and not err:
                # Extract the names from the html text
                self.names.emit(re.findall(r'title="([\w\W]+)" class', orthodox_names, re.U)[0])
            else:
                self.names.emit('https://www.saint.gr/calendar.aspx')

            online = fetch.online
            logging.debug('Parsing sansimera data')
            data = sansimera_data.Sansimera_data()
            lista = data.getAll()
            logging.debug('Parsed %s sansimera items', len(lista))
            for i in lista:
                self.event.emit(i)
            self.online_signal.emit(online)
        except Exception:
            logging.exception('Unhandled error in worker')
            self.gnomika_signal.emit('')
            self.orthodox_signal.emit('Σφάλμα κατά τη λήψη δεδομένων.')
            self.names.emit('https://www.saint.gr/calendar.aspx')
            self.online_signal.emit(False)
        logging.debug('Worker run finished')
        return


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setOrganizationName('sansimera-qt')
    app.setOrganizationDomain('sansimera-qt')
    app.setApplicationName('sansimera-qt')
    configure_logging()
    logging.debug('QApplication created')
    logging.debug('Creating Sansimera main object')
    prog = Sansimera()
    logging.debug('Entering QApplication event loop')
    app.exec_()
    logging.info('QApplication event loop finished')


def excepthook(exc_type, exc_value, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    Parameters
    ----------
    exc_type : str
        exception type
    exc_value : int
        exception value
    tracebackobj : traceback
        traceback object
    """
    separator = '-' * 80

    now = f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")} CRASH:'

    info = StringIO()
    traceback.print_tb(tracebackobj, None, info)
    info.seek(0)
    info = info.read()

    errmsg = '{}\t \n{}'.format(exc_type, exc_value)
    sections = [now, separator, errmsg, separator, info]
    msg = '\n'.join(sections)

    print(msg)
    logging.critical(msg)

    settings = QSettings()
    logPath = os.path.dirname(settings.fileName())
    logFile = f'{logPath}/sansimera.log'
    try:
        if not os.path.exists(logPath):
            os.makedirs(logPath)
        with open(logFile, 'a') as logfile:
            logfile.write(msg)
    except OSError:
        with open('/tmp/sansimera.log', 'a') as logfile:
            logfile.write(msg)


sys.excepthook = excepthook


if __name__ == '__main__':
    main()
