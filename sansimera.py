#!/usr/bin/python3
# Purpose: Display the events of the day back in the history
# from the website www.sansimera.gr
# Author: Dimitrios Glentadakis dglent@free.fr
# License: GPLv3

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
import os
import re
import qrc_resources
import sansimera_data
import sansimera_fetch


class Sansimera(QMainWindow):
    def __init__(self, parent=None):
        super(Sansimera, self).__init__(parent)
        self.timer = QTimer(self)
        self.tentatives = 0
        self.gui()
        self.lista=[]
        self.lista_pos = 0
        
    def gui(self):
        self.systray = QSystemTrayIcon()
        self.icon = QIcon(':/sansimera.png')
        self.systray.setIcon(self.icon)
        self.systray.setToolTip('Σαν σήμερα...')
        self.menu = QMenu()
        exitAction = QAction('&Έξοδος', self)
        refreshAction = QAction('&Ανανέωση', self)
        self.menu.addAction(refreshAction)
        self.menu.addAction(exitAction)
        self.connect(exitAction, SIGNAL('triggered()'), exit)
        self.connect(refreshAction, SIGNAL('triggered()'), self.refresh)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.setGeometry(600, 500, 400, 300)
        self.setWindowIcon(self.icon)          
        self.setWindowTitle('Σαν σήμερα...')   
        self.setCentralWidget(self.browser)
        self.systray.show()
        self.systray.activated.connect(self.activate)
        self.menu.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint)
        #FIX: if run with session, wait tray ??
        self.timer.singleShot(10000, self.download)
        self.browser.append('Λήψη...')
        nicon = QIcon(':/next')
        picon = QIcon(':/previous')
        ricon = QIcon(':/refresh')
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
        self.menu.hide()
        self.browser.clear()
        self.lista = []
        self.systray.setToolTip('Σαν σήμερα...')
        self.browser.append('Λήψη...')
        self.tentatives = 0
        self.download()    
        
    def closeEvent(self, event):
        self.hide()
        event.ignore()      
    
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
            if self.menu.isVisible():
                self.menu.hide()
            else:
                self.menu.popup(QCursor.pos())
        
    def exit(self):
        ''' Try to prevent to exit the application
        if cklicked on close button of the window'''
        if not self.app: return
        self.app.started.connect(self.app.quit, type=Qt.QueuedConnection)
        self.app.exec_()
        qApp = None
        self.app = None

    def download(self):
        self.workThread = WorkThread()
        self.connect(self.workThread, SIGNAL('online(bool)'), self.status)
        self.connect(self.workThread, SIGNAL('finished()'), self.window)
        self.connect(self.workThread, SIGNAL('event(QString)'), self.addlist)
        self.workThread.start()
        
    def addlist(self, text):
        self.lista.append(text)
        
    def status(self, status):
        self.status_online = status

    def nameintooltip(self, text):
        names = re.findall(
            '<a href="http://www.sansimera.gr/namedays">([\D]+)</a>', text)
        namedays = ''.join(n for n in names)
        if namedays == '':
            return
        self.systray.setToolTip(namedays)
        self.systray.showMessage('Εορτάζουν:\n', namedays)
        
    def next_try(self):
        self.timer.singleShot(5000, self.refresh)
        
    def window(self):
        # BUG: assign None to the thread to
        # prevent crash if the button
        # refresh is pressed multiple times
        # Is it the right way to do it ???
        self.workThread = None
        if self.status_online:
            self.browser.clear()
            self.browser.append(self.lista[0])
            self.lista_pos=0
            message = 'Δεν υπάρχει κάποια σημαντική εορτή'
            self.systray.setToolTip(message)
            for i in range(0, len(self.lista)):
                if self.lista[i].count('Εορτολόγιο') == 1:
                    self.nameintooltip(self.lista[i])
                    return
                else:
                    self.systray.showMessage('Εορτάζουν:\n', message)
            return
        else:
            if self.tentatives == 10:
                return
            self.next_try()
            self.tentatives += 1
            
class WorkThread(QThread):
    def __init__(self):
        QThread.__init__(self)
        
    def __del__(self):
        self.wait()
 
    def run(self):
        fetch = sansimera_fetch.Sansimera_fetch()
        html = fetch.html()
        online = fetch.online
        data = sansimera_data.Sansimera_data()
        lista = data.getAll()
        for i in lista:
            self.emit(SIGNAL('event(QString)'), i)
        self.emit(SIGNAL('online(bool)'), bool(online))
        print('thread', online)
        return      

app = QApplication(sys.argv)
prog = Sansimera()
app.exec_()
