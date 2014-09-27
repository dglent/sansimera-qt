#!/usr/bin/python3
# Purpose: Display the events of the day back in the history
# from the website www.sansimera.gr
# Author: Dimitrios Glentadakis dglent@free.fr
# License: GPLv3

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import platform
import sys
import os
import re
import qrc_resources
import sansimera_data
import sansimera_fetch

__version__ = "0.1"


class Sansimera(QMainWindow):
    def __init__(self, parent=None):
        super(Sansimera, self).__init__(parent)
        self.timer = QTimer(self)
        self.tentatives = 0
        self.gui()
        self.lista=[]
        self.lista_pos = 0
        self.eortazontes_shown = False

    def gui(self):
        self.systray = QSystemTrayIcon()
        self.icon = QIcon(':/sansimera.png')
        self.systray.setIcon(self.icon)
        self.systray.setToolTip('Σαν σήμερα...')
        self.menu = QMenu()
        exitAction = QAction('&Έξοδος', self)
        refreshAction = QAction('&Ανανέωση', self)
        aboutAction = QAction('&Σχετικά', self)
        self.menu.addAction(refreshAction)
        self.menu.addAction(aboutAction)
        self.menu.addAction(exitAction)
        self.connect(exitAction, SIGNAL('triggered()'), exit)
        self.connect(refreshAction, SIGNAL('triggered()'), self.refresh)
        self.connect(aboutAction, SIGNAL('triggered()'), self.about)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.setGeometry(600, 500, 400, 300)
        self.setWindowIcon(self.icon)          
        self.setWindowTitle('Σαν σήμερα...')   
        self.setCentralWidget(self.browser)
        self.systray.show()
        self.systray.activated.connect(self.activate)
        #FIXME: if run with session, wait tray ??
        self.timer.singleShot(10000, self.download)
        self.browser.append('Λήψη...')
        nicon = QIcon(':/next')
        picon = QIcon(':/previous')
        ricon = QIcon(':/refresh')
        iicon = QIcon(':/info')
        qicon = QIcon(':/exit')
        nextAction = QAction('Επόμενο', self)
        nextAction.setIcon(nicon)
        previousAction = QAction('Προηγούμενο', self)
        self.connect(refreshAction, SIGNAL('triggered()'), self.refresh)
        self.connect(nextAction, SIGNAL('triggered()'), self.nextItem)
        self.connect(previousAction, SIGNAL('triggered()'), self.previousItem)
        previousAction.setIcon(picon)
        refreshAction.setIcon(ricon)
        exitAction.setIcon(qicon)
        aboutAction.setIcon(iicon)
        controls = QToolBar()
        self.addToolBar(Qt.BottomToolBarArea, controls)
        controls.addAction(previousAction)
        controls.addAction(nextAction)
        controls.addAction(refreshAction)
    
    def nextItem(self):
        if len(self.lista) >= 1:
            self.browser.clear()
            if self.lista_pos != len(self.lista)-1:
                self.lista_pos += 1
            else:
                self.lista_pos = 0
            self.browser.append(self.lista[self.lista_pos])
        else:
            return

    def previousItem(self):
        if len(self.lista) >= 1:
            self.browser.clear()
            if self.lista_pos == 0:
                self.lista_pos = len(self.lista)-1
            else:
                self.lista_pos -= 1
            self.browser.append(self.lista[self.lista_pos])
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
        self.workThread = WorkThread()
        self.connect(self.workThread, SIGNAL('online(bool)'), self.status)
        self.connect(self.workThread, SIGNAL('finished()'), self.window)
        self.connect(self.workThread, SIGNAL('event(QString)'), self.addlist)
        self.connect(self.workThread, SIGNAL('names(QString)'), self.nameintooltip)
        self.workThread.start()
    
    def addlist(self, text):
        self.lista.append(text)
        
    def status(self, status):
        self.status_online = status

    def nameintooltip(self, text):
        if self.eortazontes_shown:
            return
        self.systray.setToolTip(text)
        notifier_text = text.replace('<br/>', '\n')
        self.systray.showMessage('Εορτάζουν:\n', notifier_text)
        self.eortazontes_shown = True
        
    def window(self):
        if self.status_online:
            self.browser.clear()
            self.browser.append(self.lista[0])
            self.lista_pos=0
            return
        else:
            if self.tentatives == 10:
                return
            self.timer.singleShot(5000, self.refresh)
            self.tentatives += 1
            
    def about(self):
        self.menu.hide()
        QMessageBox.about(self, "Εφαρμογή «Σαν σήμερα...»",
                        """<b>sansimera-qt</b> v{0}
                        <p>Δημήτριος Γλενταδάκης <a href="mailto:dglent@free.fr">dglent@free.fr</a>
                        <p>Εφαρμογή πλαισίου συστήματος για την προβολή
                        <br/>των γεγονότων από την ιστοσελίδα <a href="http://www.sansimera.gr">
                        www.sansimera.gr</a>.
                        <p>Άδεια χρήσης: GPLv3 <br/>Python {1} - Qt {2} - PyQt {3} σε {4}""".format(
                        __version__, platform.python_version(),
                        QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))
                        
                        
class WorkThread(QThread):
    def __init__(self):
        QThread.__init__(self)
        
    def __del__(self):
        self.wait()
 
    def run(self):
        fetch = sansimera_fetch.Sansimera_fetch()
        html = fetch.html()
        eortazontes = fetch.eortologio()
        online = fetch.online
        data = sansimera_data.Sansimera_data()
        lista = data.getAll()
        for i in lista:
            self.emit(SIGNAL('event(QString)'), i)
        self.emit(SIGNAL('online(bool)'), bool(online))
        self.emit(SIGNAL('names(QString)'), eortazontes)
        print('thread', online)
        return      

app = QApplication(sys.argv)
prog = Sansimera()
app.setQuitOnLastWindowClosed(False)
app.exec_()
