import logging
import re
import requests
import os
from bs4 import BeautifulSoup

try:
    import Image
except ImportError:
    from PIL import Image

try:
    import sansimera_fetch
except ImportError:
    from sansimera_qt import sansimera_fetch


class Sansimera_data(object):
    def __init__(self):
        logging.debug('Initializing Sansimera_data')
        self.allList = []
        self.addBC = False
        self.error_message = ''
        self.baseurl = 'https://www.sansimera.gr/'
        self.fetch = sansimera_fetch.Sansimera_fetch()
        self.online = True
        try:
            arxeio = open(self.fetch.tmppathname + '/sansimera_html', 'r')
            ss = arxeio.read()
            if ss != '':
                self.online = True
            logging.debug('Read sansimera html bytes=%s online=%s', len(ss), self.online)
            arxeio.close()
        except Exception:
            logging.exception('Cannot read sansimera html')
            self.online = False
        if os.path.exists(self.fetch.error_filename):
            with open(self.fetch.error_filename, 'r', encoding='utf-8') as error_file:
                self.error_message = error_file.read().strip()
            logging.debug('Read sansimera error message: %s', self.error_message)
        else:
            self.error_message = ''
        self.month = self.fetch.monthname()
        self.sanTitle = '&nbsp;' * 10 + self.month
        os.chdir(self.fetch.tmppathname)
        if os.path.exists('sansimera_html'):
            with open('sansimera_html') as html:
                self.soup = BeautifulSoup(html, features="lxml")
                logging.debug('BeautifulSoup initialized for sansimera html')

    def getImage(self, text):
        '''Convert url to local path.
           Download and resize images'''
        yeartoBold = re.findall('href="/reviews/([0-9]+)">', text)
        if len(yeartoBold) == 0:
            yeartoBold = re.findall('>([0-9]+)', text)
        if len(yeartoBold) > 0:
            self.year = yeartoBold[0]
            bC = ''
            if self.bC:
                bC = ' π.Χ.'
            self.year = '<b>' + self.year + bC + ': </b><br/>'
        try:
            # Remove the the url with the year (uneeded)
            year_with_url = re.findall('<a class="text-info" href="https://www.sansimera.gr/reviews/[0-9 "></a]+', text)[0]
            text = text.replace(year_with_url, '')
        except IndexError:
            pass

        iconUrl = 'None'
        iconUrl = ''
        iconUrl = re.findall('<source data-srcset="(https:[/a-z.A-Z0-9-_()]+)" media=', text)
        if len(iconUrl) > 0:
            iconUrl = iconUrl[0]
            iconName = os.path.basename(iconUrl)
            try:
                req = requests.get(
                    iconUrl,
                    stream=True,
                    headers={'User-agent': 'Mozilla/5.0'},
                    timeout=10
                )
                logging.debug('Image request %s status=%s', iconUrl, req.status_code)
                if req.status_code == 200:
                    with open(iconName, 'wb') as iconfile:
                        iconfile.write(req.content)
                    im = Image.open(iconName)
                    size = 128, 128
                    im.thumbnail(size, Image.Resampling.LANCZOS)
                    im.save(iconName)
                    # Convert the url to local name
                    img_source = re.findall('src="[:/a-z.A-Z0-9-_]+"', text)
                    for src in img_source:
                        text = text.replace(src, 'src="{}"'.format(iconName))
            except (requests.exceptions.RequestException, OSError) as err:
                logging.warning('Image download skipped: %s error=%s', iconUrl, err)
        return text

    def events(self):
        ''' Find the events, the births and the deaths '''
        events = self.soup.find_all('li')
        logging.debug('Found li elements: %s', len(events))
        events_keys = [
            'data-fancybox="event', 'data-fancybox="birth', 'data-fancybox="death'
        ]
        for ev in events:
            for key in events_keys:
                if str(ev).count(key) == 1:
                    self.event_parser(ev)

    def event_parser(self, event):
        event = str(event)
        birth_death = ''
        if event.count('π.Χ.</a>') == 1:
            self.bC = True
            event = event.replace('π.Χ.', '')
        else:
            self.bC = False
            event = event.replace('μ.Χ.', '')
        eventText_url_local = self.getImage(event)
        if eventText_url_local.count('data-fancybox="death-') == 1:
            birth_death = '<br/><small><i>Θάνατος</i></small><br/>'
        elif eventText_url_local.count('data-fancybox="birth-') == 1:
            birth_death = '<br/><small><i>Γέννηση</small></i><br/>'
        if eventText_url_local.count('href="https://') >= 1:
            eventText_url_local = eventText_url_local.replace(
                'href="/', 'href="https://www.sansimera.gr/'
            )
            self.allList.append(
                str(
                    '<br/>'
                    + self.sanTitle
                    + self.year
                    + birth_death
                    + eventText_url_local
                )
            )
            logging.debug('Parsed event item; total=%s', len(self.allList))

    def days(self):
        world_days_title = (
            '<br/><b>'
            + '&nbsp;' * 20
            + 'Παγκόσμιες Ημέρες</b><br/>'
        )

        lista = self.soup.find_all('ul', 'arrowlist')
        logging.debug('Found world days lists: %s', len(lista))
        if len(lista) > 0:
            for day in lista:
                world_days_title += str(day)
            worldays = '<b/>' + self.sanTitle + '<br/>' + world_days_title
            self.allList.append(worldays)
            logging.debug('Added world days item')

    def getAll(self):
        self.allList = []
        logging.debug('getAll called online=%s', self.online)
        if self.online:
            self.events()
            self.days()
        if len(self.allList) == 0:
            fallback_message = self.error_message or (
                'Δεν βρέθηκαν γεγονότα, ελέγξτε τη σύνδεσή σας.'
            )
            logging.warning('No sansimera items parsed; fallback=%s', fallback_message)
            self.allList.append(
                '<br/>'
                + self.sanTitle
                + '<br/><br/>'
                + fallback_message
            )
        logging.info('Returning sansimera items: %s', len(self.allList))
        return self.allList


if __name__ == "__main__":
    a1 = Sansimera_data()
    lista = a1.getAll()
    for i in lista:
        print('====================')
        print(i)
        input()
