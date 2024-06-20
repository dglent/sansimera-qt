# Author: Dimitrios Glentadakis dglent@free.fr
# License: GPLv3

import os
import datetime
import tempfile
import urllib.request
import re
from bs4 import BeautifulSoup
from PyQt5.QtCore import QObject, QThread
from multiprocessing.pool import ThreadPool
from socket import timeout

try:
    import Image
except ImportError:
    from PIL import Image


class Sansimera_fetch(QObject):
    dico_days_genitive = {
        '01': 'Ιανουαρίου', '02': 'Φεβρουαρίου', '03': 'Μαρτίου',
        '04': 'Απριλίου', '05': 'Μαίου', '06': 'Ιουνίου',
        '07': 'Ιουλίου', '08': 'Αυγούστου', '09': 'Σεπτεμβρίου',
        '10': 'Οκτωβρίου', '11': 'Νοεμβρίου', '12': 'Δεκεμβρίου'
    }

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
        month = self.ponth()
        im = str(
            ' ' * 10
            + '...Σαν σήμερα '
            + self.pay()
            + ' '
            + self.dico_days_genitive[month]
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
            'wget --timeout=10 --user-agent="Sansimera PyQt" '
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
        except Exception:
            self.online = False

    def orthodoxos_synarxistis(self):
        tries = 0
        while tries < 2:
            html, err = self.getHTML('https://www.saint.gr/calendar.aspx')
            if html:
                break
            else:
                tries += 1
        if not html:
            return False, err
        err = "Error"
        days = html.split('<div class="w3-circle w3-theme-d5 myDayBullet">')
        pay = self.pay()
        first_of_month = False
        for day in days[1:]:
            dd = re.findall('^([0-9]+)<', day)
            if int(dd[0]) == 1:
                first_of_month = True
            if int(pay) == int(dd[0]) and first_of_month:
                image_fname = re.findall(r'img src="/images/calendar/([a-zA-Z0-9\.]+)"', day)[0]
                image_url = f'https://www.saint.gr/images/calendar/{image_fname}'
                image_abs_path = re.findall(r'img src="/images/calendar/[a-zA-Z0-9\.]+"', day)[0]
                filename = self.tmppathname + '/' + image_fname
                comm = ('wget --timeout=10 {0} -O {1}'.format(image_url, filename))
                os.system(comm)
                day = day.replace(image_abs_path, 'img src="{0}"'.format(filename))
                day = day.replace('</div></div>', f' {self.dico_days_genitive[self.ponth()]}', 1)
                perissotera_url = re.findall(r'<a href="([\w\W]+index.aspx)', day, re.U)[0]
                day = day.replace(perissotera_url, fr'https://www.saint.gr/{perissotera_url}')
                day = f'<center>{day}</center>'
                return day, False
        return False, err

    def gnomika(self):
        html, err = self.getHTML('https://www.gnomikologikon.gr/tyxaio.php')
        soup = BeautifulSoup(html, features="lxml")
        quotes = str(soup.find_all('table', 'quotes')[0])
        images_source = re.findall('src="([:/a-z.A-Z0-9-_]+)"', quotes)
        for img in images_source:
            filename = self.tmppathname + '/' + os.path.basename(img)
            quotes = quotes.replace(img, filename)

        self.workThread = WorkThread(images_source, self.tmppathname)
        self.workThread.start()

        end_quote = re.findall('<span style="font-weight:600;">[0-9]+</span>', quotes)
        for end in end_quote:
            end = str(end)
            quotes = quotes.replace(end, end + '<br/>')
        quotes = quotes.replace('href="', 'href="https://www.gnomikologikon.gr/')
        return quotes

    def getHTML(self, url):
        header = {'User-Agent': 'Mozilla/5.0 (X11; Linux)'}
        try:
            req = urllib.request.Request(url, headers=header)
            response = urllib.request.urlopen(req, timeout=10)
            page = response.read()
            html = page.decode()
            return html, False
        except timeout as err:
            return False, str(err)
        except (urllib.request.HTTPError, urllib.error.URLError) as err:
            return False, str(err)


class WorkThread(QThread):

    def __init__(self, images_source, tmppathname):
        QThread.__init__(self)
        self.images_source = images_source
        self.tmppathname = tmppathname
        ThreadPool(10).imap_unordered(self.download, images_source)

    def download(self, img):
        filename = self.tmppathname + '/' + os.path.basename(img)
        comm = ('wget --timeout=10 {0} -O {1}'.format('https://www.gnomikologikon.gr/' + img, filename))
        os.system(comm)
        im = Image.open(filename)
        size = 80, 80
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(filename)


if __name__ == "__main__":
    a1 = Sansimera_fetch()
    lista = a1.html()
    orthodox = a1.orthodoxos_synarxistis()
    gnomika = a1.gnomika()
