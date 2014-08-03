# Author: Dimitrios Glentadakis dglent@free.fr
# License: GPLv3

import os
import datetime
import subprocess
import glob
from PyQt4.QtCore import *

class Sansimera_fetch(QObject):
    
    def __init__(self, parent=None):
        super(Sansimera_fetch, self).__init__(parent)
        self.online = False

    def url(self):
        imerominia = str(self.pay()+self.ponth())
        self.url = 'http://www.sansimera.gr/almanac/' + imerominia
        return self.url

    def pay(self):
        imera = str(datetime.date.today()).split('-')
        imera = imera[1:]
        self.pay = imera[1]
        return self.pay

    def ponth(self):
        imera = str(datetime.date.today()).split('-')
        imera = imera[1:]
        self.ponth = imera[0]
        return self.ponth

    def monthname(self):
        dico = {'01': 'Ιανουαρίου', '02': 'Φεβρουαρίου', '03': 'Μαρτίου', \
            '04': 'Απριλίου', '05': 'Μαίου', '06': 'Ιουνίου', '07': 'Ιουλίου', \
                '08': 'Αυγούστου', '09': 'Σεπτεμβρίου', '10': 'Οκτωβρίου', \
                    '11': 'Νοεμβρίου', '12': 'Δεκεμβρίου'}
        month = self.ponth()
        self.im = str(' ' * 10 + '...Σαν σήμερα ' + self.pay() + ' ' + dico[month] + '\n')
        return self.im
    
    @staticmethod
    def removeFiles():
        currentPath = os.path.basename(os.getcwd())
        if currentPath == 'sansimera_cache':
            for _file in glob.glob('*'):
                os.remove(_file)

    def html(self):
        currentpath = os.path.basename(os.getcwd())
        path = ('sansimera_cache')
        if currentpath != path:
            try:
                os.chdir(path)
            except:
                cmd_mkdir = ('mkdir -p ' + path)
                os.system(cmd_mkdir)
                path = ('sansimera_cache')
                os.chdir(path)
        link = self.url()
        filename='sansimera_html'
        comm0 = 'touch ' + filename
        os.system(comm0)
        comm = 'wget --timeout=5 --user-agent="Sansimera PyQt" ' + link + ' -O ' + filename
        self.online = True
        Sansimera_fetch.removeFiles()
        os.system(comm)
        try:
            with open(filename, 'r') as html_file:
                check_line = html_file.read()
                if check_line == '':
                    self.online = False
        except:
            self.online = False
        self.emit(SIGNAL('online(bool)'), self.online)

    def fetchDate(self):
        date = str(datetime.date.today())
        return date

if __name__ == "__main__":
    a1=Sansimera_fetch()
    lista=a1.html()

