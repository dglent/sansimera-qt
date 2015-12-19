# Author: Dimitrios Glentadakis dglent@free.fr
# License: GPLv3

import os
import datetime
import tempfile
import urllib.request
import re
from PyQt5.QtCore import QObject


class Sansimera_fetch(QObject):

    def __init__(self, parent=None):
        super(Sansimera_fetch, self).__init__(parent)
        self.online = False
        # FIXME Until i find how to creat a named folder with tempfile
        pathname = tempfile.mkdtemp()
        comm = ('mv ' + pathname + ' ' + os.path.dirname(pathname) +
                '/sansimera-qt')
        os.system(comm)
        self.tmppathname = os.path.dirname(pathname) + '/sansimera-qt'

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
        dico = {'01': 'Ιανουαρίου', '02': 'Φεβρουαρίου', '03': 'Μαρτίου',
                '04': 'Απριλίου', '05': 'Μαίου', '06': 'Ιουνίου',
                '07': 'Ιουλίου', '08': 'Αυγούστου', '09': 'Σεπτεμβρίου',
                '10': 'Οκτωβρίου', '11': 'Νοεμβρίου', '12': 'Δεκεμβρίου'}
        month = self.ponth()
        self.im = str(' ' * 10 + '...Σαν σήμερα ' + self.pay() + ' ' +
                      dico[month] + '\n')
        return self.im

    def html(self):
        link = self.url()
        filename = self.tmppathname + '/sansimera_html'
        # Create the blank file (needed for the test if data in file)
        comm0 = 'touch ' + filename
        os.system(comm0)
        # FIXME to use urlib.request instead
        comm = ('wget --timeout=5 --user-agent="Sansimera PyQt" ' + link +
                ' -O ' + filename)
        self.online = True
        os.system(comm)
        try:
            with open(filename, 'r') as html_file:
                check_line = html_file.read()
                if check_line == '':
                    self.online = False
        except:
            self.online = False

    def eortologio(self):
        req = urllib.request.Request('http://www.eortologio.gr/rss/si_el.xml')
        response = urllib.request.urlopen(req)
        page = response.read()
        html = page.decode('cp1253')
        text = 'Δεν υπάρχει κάποια σημαντική εορτή'
        eortazontes = re.findall('<title>(σήμερα[\D0-9]+)</title>', html)
        if len(eortazontes) >= 1:
            text = eortazontes[0]
            list_names = text.split(',')
            # Avoid to create a long line in tooltip
            for i in range(4, len(list_names), 4):
                try:
                    list_names.insert(i, '<br/>')
                    list_names[i+1] = list_names[i+1].lstrip()
                except IndexError:
                    break

            text = (''.join(i for i in list_names))
        return text

    def fetchDate(self):
        date = str(datetime.date.today())
        return date

if __name__ == "__main__":
    a1 = Sansimera_fetch()
    lista = a1.html()
