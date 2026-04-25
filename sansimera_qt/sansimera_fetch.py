# Author: Dimitrios Glentadakis dglent@free.fr
# License: GPLv3

import os
import datetime
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
import re
from bs4 import BeautifulSoup
from PyQt5.QtCore import QObject, QThread
from multiprocessing.pool import ThreadPool
from socket import timeout

try:
    import Image
except ImportError:
    from PIL import Image


DEFAULT_USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'
)
CHALLENGE_MARKERS = (
    'Verifying your browser',
    '/cdn-cgi/challenge-platform',
)
CHALLENGE_ERROR_MESSAGE = (
    'Η ιστοσελίδα www.sansimera.gr ζήτησε επαλήθευση '
    'φυλλομετρητή και δεν επέστρεψε τα γεγονότα της ημέρας.'
)


def decode_body(body, encoding):
    if not encoding:
        encoding = 'utf-8'
    try:
        return body.decode(encoding)
    except (LookupError, UnicodeDecodeError):
        return body.decode('utf-8', errors='replace')


def download_binary(url, filename, timeout_seconds=10):
    request = urllib.request.Request(
        url,
        headers={'User-Agent': DEFAULT_USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = response.read()
    except (timeout, urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return False

    with open(filename, 'wb') as output_file:
        output_file.write(data)
    return True


def fetch_with_browser_engine(url, filename, timeout_seconds=40):
    helper = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'sansimera_browser_fetch.py'
    )
    #  Run isolated qtwebengine fetch helper to avoid importing Qt WebEngine in the main process
    command = [sys.executable, helper, url, filename]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
    except (OSError, subprocess.SubprocessError) as err:
        return False, str(err)

    if result.returncode == 0:
        try:
            with open(filename, 'r', encoding='utf-8') as html_file:
                html = html_file.read()
        except OSError as err:
            return False, str(err)

        if html and not any(marker in html for marker in CHALLENGE_MARKERS):
            return True, ''
        return False, 'Browser helper returned a verification page.'

    error = (result.stderr or result.stdout).strip()
    if 'Qt WebEngine was not available.' in error:
        return (
            False,
            'Δεν βρέθηκε διαθέσιμο Qt WebEngine '
            'για την επαλήθευση του www.sansimera.gr.'
        )
    if 'Browser verification did not complete in time.' in error:
        return False, CHALLENGE_ERROR_MESSAGE
    return (
        False,
        'Η λήψη μέσω προγράμματος περιήγησης απέτυχε για το '
        'www.sansimera.gr.'
    )


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
        self.last_error = ''
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
        self.error_filename = os.path.join(self.tmppathname, 'sansimera_error')
        self.html_filename = os.path.join(self.tmppathname, 'sansimera_html')

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
        self.online = False
        self.last_error = ''
        with open(self.html_filename, 'w', encoding='utf-8'):
            pass
        if os.path.exists(self.error_filename):
            os.remove(self.error_filename)

        request = urllib.request.Request(
            link,
            headers={'User-Agent': DEFAULT_USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                html = decode_body(
                    response.read(),
                    response.headers.get_content_charset()
                )
        except timeout:
            self.save_error(
                'Η ιστοσελίδα www.sansimera.gr δεν απάντησε έγκαιρα.'
            )
            return
        except urllib.error.HTTPError as err:
            html = decode_body(
                err.read(),
                err.headers.get_content_charset()
            )
            if self.browser_verification_required(html):
                if self.fetch_with_browser(link):
                    return
                self.save_error(self.last_error or CHALLENGE_ERROR_MESSAGE)
            else:
                self.save_error(
                    f'Αποτυχία λήψης δεδομένων από το www.sansimera.gr '
                    f'(HTTP {err.code}).'
                )
            return
        except (urllib.error.URLError, ValueError) as err:
            self.save_error(
                'Αδυναμία σύνδεσης με την ιστοσελίδα www.sansimera.gr: '
                + str(err)
            )
            return

        if self.browser_verification_required(html):
            if self.fetch_with_browser(link):
                return
            self.save_error(self.last_error or CHALLENGE_ERROR_MESSAGE)
            return

        with open(self.html_filename, 'w', encoding='utf-8') as html_file:
            html_file.write(html)
        self.online = True

    def browser_verification_required(self, html):
        return any(marker in html for marker in CHALLENGE_MARKERS)

    def save_error(self, message):
        self.last_error = message
        with open(self.error_filename, 'w', encoding='utf-8') as error_file:
            error_file.write(message)

    def fetch_with_browser(self, link):
        success, browser_error = fetch_with_browser_engine(
            link,
            self.html_filename
        )
        if success:
            self.online = True
            return True
        self.last_error = browser_error
        return False

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
                day = day.replace(image_abs_path, 'img src="{0}"'.format(image_url))
                if download_binary(image_url, filename):
                    day = day.replace(image_url, filename)
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
        header = {'User-Agent': DEFAULT_USER_AGENT}
        try:
            req = urllib.request.Request(url, headers=header)
            response = urllib.request.urlopen(req, timeout=10)
            page = response.read()
            html = decode_body(page, response.headers.get_content_charset())
            return html, False
        except timeout as err:
            return False, str(err)
        except (urllib.error.HTTPError, urllib.error.URLError) as err:
            return False, str(err)


class WorkThread(QThread):

    def __init__(self, images_source, tmppathname):
        QThread.__init__(self)
        self.images_source = images_source
        self.tmppathname = tmppathname
        ThreadPool(10).imap_unordered(self.download, images_source)

    def __del__(self):
        self.wait()

    def download(self, img):
        filename = self.tmppathname + '/' + os.path.basename(img)
        if not download_binary('https://www.gnomikologikon.gr/' + img, filename):
            return
        try:
            im = Image.open(filename)
            size = 80, 80
            im.thumbnail(size, Image.Resampling.LANCZOS)
            im.save(filename)
        except OSError:
            return


if __name__ == "__main__":
    a1 = Sansimera_fetch()
    lista = a1.html()
    orthodox = a1.orthodoxos_synarxistis()
    gnomika = a1.gnomika()
