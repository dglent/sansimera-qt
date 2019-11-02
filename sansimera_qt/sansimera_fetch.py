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
        comm = (
            'mv '
            + pathname
            + ' '
            + os.path.dirname(pathname)
            + '/sansimera-qt'
        )
        os.system(comm)
        self.tmppathname = os.path.dirname(pathname) + '/sansimera-qt'

    def url(self):
        date = str(self.pay() + self.ponth())
        url = 'https://www.sansimera.gr/almanac/' + date
        return url

    def pay(self):
        imera = str(datetime.date.today()).split('-')
        imera = imera[1:]
        day = imera[1]
        return day

    def ponth(self):
        imera = str(datetime.date.today()).split('-')
        imera = imera[1:]
        month = imera[0]
        return month

    def monthname(self):
        dico = {'01': 'Ιανουαρίου', '02': 'Φεβρουαρίου', '03': 'Μαρτίου',
                '04': 'Απριλίου', '05': 'Μαίου', '06': 'Ιουνίου',
                '07': 'Ιουλίου', '08': 'Αυγούστου', '09': 'Σεπτεμβρίου',
                '10': 'Οκτωβρίου', '11': 'Νοεμβρίου', '12': 'Δεκεμβρίου'}
        month = self.ponth()
        im = str(
            ' ' * 10
            + '...Σαν σήμερα '
            + self.pay()
            + ' '
            + dico[month]
            + '\n'
        )
        return im

    def html(self):
        link = self.url()
        filename = self.tmppathname + '/sansimera_html'
        # Create the blank file (needed for the test if data in file)
        comm0 = 'touch ' + filename
        os.system(comm0)
        # FIXME to use urlib.request instead
        comm = (
            'wget --timeout=5 --user-agent="Sansimera PyQt" '
            + link
            + ' -O '
            + filename
        )
        self.online = True
        os.system(comm)
        try:
            with open(filename, 'r') as html_file:
                check_line = html_file.read()
                if check_line == '':
                    self.online = False
        except:
            self.online = False

    def orthodoxos_synarxistis(self):
        req = urllib.request.Request('http://www.saint.gr/index.aspx')
        response = urllib.request.urlopen(req)
        page = response.read()
        html = page.decode()
        eortazontes = re.findall(
            '''<div id="mEortologio" style="float:left;">[';/,()&(:#\\r\\n .<\S\w=">-]+</td></tr></table></div>''',
            html
        )[0]
        image_fname = re.findall('src="http://www.saint.gr/addons/photos/([0-9a-zA-Z.]+)"', html)[0]
        image_url = re.findall('src="(http://www.saint.gr/addons/photos/[0-9a-zA-Z.]+)"', html)[0]
        image_abs_path = re.findall('src="http://www.saint.gr/addons/photos/[0-9a-zA-Z.]+"', html)[0]
        filename = self.tmppathname + '/' + image_fname
        comm = ('wget --timeout=5 {0} -O {1}'.format(image_url, filename))
        os.system(comm)
        eortazontes = eortazontes.replace(image_abs_path, 'src="{0}"'.format(filename))
        # Too big title
        for tag in ['<h1 class="pagetitle">', '</h1>']:
            eortazontes = eortazontes.replace(tag, '')
        return eortazontes

    def fetchDate(self):
        date = str(datetime.date.today())
        return date


if __name__ == "__main__":
    a1 = Sansimera_fetch()
    lista = a1.html()
    eortologio = a1.eortologio()
    orthodox = a1.orthodoxos_synarxistis()
