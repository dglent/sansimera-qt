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
except:
    from sansimera_qt import sansimera_fetch


class Sansimera_data(object):
    def __init__(self):
        self.allList = []
        self.addBC = False
        self.baseurl = 'https://www.sansimera.gr/'
        self.fetch = sansimera_fetch.Sansimera_fetch()
        self.online = True
        try:
            arxeio = open(self.fetch.tmppathname + '/sansimera_html', 'r')
            ss = arxeio.read()
            if ss != '':
                self.online = True
            arxeio.close()
        except:
            self.online = False
        self.month = self.fetch.monthname()
        self.sanTitle = '&nbsp;' * 10 + self.month
        os.chdir(self.fetch.tmppathname)
        if os.path.exists('sansimera_html'):
            with open('sansimera_html') as html:
                self.soup = BeautifulSoup(html)

    def getImage(self, text):
        '''Convert url to local path.
           Download and resize images'''
        relativeUrls = re.findall('href="(/[a-zA-Z./_0-9-]+)', text)
        yeartoBold = re.findall('href="/reviews/([0-9]+)">', text)
        if len(yeartoBold) == 0:
            yeartoBold = re.findall('<div class="time text-primary">([0-9]+)</div>', text)
        if len(relativeUrls) > 0:
            for relurl in relativeUrls:
                text = text.replace(relurl, self.baseurl[:-1] + relurl)
        if len(yeartoBold) > 0:
            self.year = yeartoBold[0]
            bC = ''

            if self.bC:
                bC = ' π.Χ.'
            self.year = '<b>' + self.year + bC + ': </b><br/>'
        iconUrl = 'None'
        try:
            iconUrl = re.findall('src="(https://[a-zA-Z./_0-9-%]+)', text)[0]
            iconName = os.path.basename(iconUrl)
            req = requests.get(iconUrl, stream=True,
                               headers={'User-agent': 'Mozilla/5.0'},
                               timeout=10)
            if req.status_code == 200:
                with open(iconName, 'wb') as iconfile:
                    iconfile.write(req.content)
            im = Image.open(iconName)
            newim = im.resize((82, 64), Image.ANTIALIAS)
            newim.save(iconName)
            # Convert the url to local name
            newText = text.replace(iconUrl, iconName)
            return newText
        except:
            print('getImage failed: ', '- URL: ', iconUrl, ' - Text :', text)
            return text

    def said_know(self):
        listd = self.soup.find_all('div')
        count = 0
        for div in listd:
            tag = div.get('class')
            if isinstance(tag, list):
                if len(tag) > 1:
                    # Find the Did You Know ...
                    if tag[0] == 'widget' and tag[1] == 'col-xs-12':
                        h3 = div.find_all('h3')

                        if len(h3) == 1:
                            h3 = h3[0]
                            h3 = h3.text
                            if h3 == 'ΗΞΕΡΕΣ ΟΤΙ...':
                                didYouKnow = (str(listd[count]))
                                # Convert url to local path
                                didYouKnow_url_local = self.getImage(didYouKnow)
                                self.allList.append(str(didYouKnow_url_local))
                    # Find the He Said ...
                    if tag[0] == 'widget' and tag[1] == 'widget-quotes':
                        said = str(listd[count])
                        # Convert url to local path
                        who_url_local = self.getImage(said)
                        self.allList.append(who_url_local)
            count += 1

    def events(self):
        ''' Find the events, the births and the deaths '''
        events = self.soup.find_all('dl')
        count = 0
        for ev in events:
            self.event_parser(ev, count)
            count += 1

    def remove_year(self, text):
        # Remove the link with the year avbove the image
        # Eg:'<a class="text-primary no-underline" href="https://www.sansimera.gr/reviews/1989">1989</a>'
        url_year_to_delete = re.findall(
            '<a class="text-primary no-underline" [\w=":/.>\d]+</a>',
            text
        )
        px_year_to_delete = re.findall(
            '<div class="time text-primary">[0-9]+</div>',
            text
        )
        try:
            text = text.replace(url_year_to_delete[0], '')
        except:
            print('Couldn\'t remove year url for: ', text)
            pass
        try:
            text = text.replace(px_year_to_delete[0], '')
        except:
            print('Couldn\'t remove year url for: ', text)
            pass
        return text

    def event_parser(self, event, count):
        event = str(event)
        event = event.split('</dd>')
        birth_death = ''
        for ev in event:
            if ev.count('<dt class="text-xs-center">π.Χ.</dt>') == 1:
                self.bC = True
                ev = ev.replace('π.Χ.', '')
            else:
                self.bC = False
                ev = ev.replace('μ.Χ.', '')
            eventText_url_local = self.getImage(ev)
            eventText_url_local = self.remove_year(eventText_url_local)
            if ev.count('<small>(Γεν. ') or count == 2:
                birth_death = '<br/><small><i>Θάνατος</i></small><br/>'
            elif count == 1:
                birth_death = '<br/><small><i>Γέννηση</small></i><br/>'
            if eventText_url_local.count('href="https://') >= 1:
                self.allList.append(
                    str(
                        '<br/>'
                        + self.sanTitle
                        + self.year
                        + birth_death
                        + eventText_url_local
                    )
                )

    def days(self):
        worldlist = [
            str(
                '<br/><b>'
                + '&nbsp;' * 20
                + 'Παγκόσμιες Ημέρες</b><br/>'
            )
        ]
        lista = self.soup.find_all('a')
        for tag in lista:
            url = tag.get('href')
            if isinstance(url, str):
                if 'worldays' in url or 'namedays' in url:
                    if 'worldays' in url:
                        day = 'w'
                    elif 'namedays' in url:
                        day = 'n'
                        title = (
                            self.sanTitle
                            + '<br/>'
                            + '&nbsp;' * 20
                            + '<b>Εορτολόγιο</b><br/>'
                        )
                    tag = str(tag)
                    if 'Εορτολόγιο' in tag or 'Παγκόσμιες Ημέρες' in tag:
                        continue
                    # Parse with getImage() to expand relative urls
                    tag = self.getImage(tag)
                    if day == 'w':
                        worldlist.append('<br/>' + tag + '.')
                    elif day == 'n':
                        tag = '<br>' + title + '<br/>' + tag
                        self.allList.append(tag)
        if len(worldlist) > 1:
            worldays = ' '.join(worldlist)
            worldays = '<b/>' + self.sanTitle + '<br/>' + worldays
            self.allList.append(worldays)

    def getAll(self):
        self.allList = []
        if self.online:
            self.events()
            self.said_know()
            self.days()
        if len(self.allList) == 0:
            self.allList.append(
                '<br/>'
                + self.sanTitle
                + '<br/><br/>Δεν βρέθηκαν γεγονότα,'
                + 'ελέγξτε τη σύνδεσή σας.'
            )
        return self.allList


if __name__ == "__main__":
    a1 = Sansimera_data()
    lista = a1.getAll()
    for i in lista:
        print('====================')
        print(i)
        input()
