import re
import urllib.request
import os
import sansimera_fetch
import subprocess
from bs4 import BeautifulSoup

try:
    import Image
except ImportError:
    from PIL import Image


class Sansimera_data(object):
    def __init__(self):
        self.allList = []
        self.addBC = False
        self.baseurl = 'http://www.sansimera.gr/'
        self.fetch = sansimera_fetch.Sansimera_fetch()
        self.online = True
        try:
            arxeio = open('sansimera_html', 'r')
            ss=arxeio.read()
            if ss != '':
                self.online = True
            arxeio.close()
        except:
            self.online = False
        self.month = self.fetch.monthname()
        self.sanTitle = '&nbsp;'*10 + self.month
        try:
            os.chdir('sansimera_cache')
        except:
            pass
        if os.path.exists('sansimera_html'):
            with open('sansimera_html') as html:
                self.soup = BeautifulSoup(html)

    def getImage(self, text):
        relativeUrls = re.findall('href="(/[a-zA-Z./_0-9-]+)', text)
        yeartoBold = re.findall('(<div>[0-9]+</div>)', text)
        if len(relativeUrls) > 0:
            for relurl in relativeUrls:
                text = text.replace(relurl, self.baseurl[:-1]+relurl)
        if len(yeartoBold) > 0:
            self.year = yeartoBold[0]
            if self.bC:
                self.year = yeartoBold[0].replace('</div>', ' π.Χ.</div>', re.UNICODE)
            self.year = '<b>'+self.year[5:-6]+':</b>'
            text = text.replace(yeartoBold[0], '')
        try:
            iconUrl = re.findall('src="(http://[a-zA-Z./_0-9-]+)', text)[0]
            iconName = os.path.basename(iconUrl)
            urllib.request.urlretrieve(iconUrl, iconName)
            im = Image.open(iconName)
            newim = im.resize((82,64), Image.ANTIALIAS)
            newim.save(iconName)
            # Convert the url to local name
            newText = text.replace(iconUrl, iconName)
            return newText
        except:
            return text

    def events(self):
        birthDeath = ''
        listd = self.soup.find_all('div')
        count=0
        for div in listd:
            tag = div.get('class')
            if isinstance(tag, list):
                if len(tag) > 1:
                    # Find the Did You Know ...
                    if tag[0] == 'over' and tag[1] == 'mb10':
                        didYouKnow = (str(listd[count]))
                        # Convert url to local path
                        didYouKnow_url_local = self.getImage(didYouKnow)
                        self.allList.append(str('<br/>' + didYouKnow_url_local))
                    # Find the He Said ...
                    if tag[0] == 'quote' and tag[1] == 'white':
                        said = ('<br/>' + '&nbsp;'*10 + '<b>Είπε:</b>' + str(listd[count]))
                        whoSaid = str(listd[count+3])
                        # Convert url to local path
                        who_url_local = self.getImage(whoSaid)
                        self.allList.append(said + who_url_local)
                if tag[0] == 'timeline-tab-content':
                    event = listd[count].get('id')
                    if event == 'Deaths':
                        event = self.sanTitle
                        birthDeath = '<br/><small><i>Θάνατος</i></small>'
                    elif event == 'Births':
                        event = self.sanTitle
                        birthDeath = '<br/><small><i>Γέννηση</small></i>'
                    else:
                        event = self.sanTitle
                if tag[0] == 'timeline-item' and tag[1] == 'clearfix':
                    eventText = str(listd[count])
                    # Find if before Christ
                    divBC = str(listd[count-1].p)
                    bC = re.findall('<span>[\.π\s\.Χ]+</span>', divBC, re.UNICODE)
                    if len(bC) == 1:
                            self.bC = True
                    else:
                        self.bC = False
                    eventText_url_local = self.getImage(eventText)
                    self.allList.append(str('<br/>' + event+self.year+birthDeath+eventText_url_local))
            count += 1

    def days(self):
        worldlist = [str('<br/><b>' + '&nbsp;' * 20 + 'Παγκόσμιες Ημέρες</b><br/>')]
        lista = self.soup.find_all('a')
        for tag in lista:
            url = tag.get('href')
            if isinstance(url, str):
                if 'worldays' in url or 'namedays' in url:
                    if 'worldays' in url:
                        day = 'w'
                    elif 'namedays' in url:
                        day = 'n'
                        title = self.sanTitle + '<br/>' + '&nbsp;'*20 + '<b>Εορτολόγιο</b><br/>'
                    tag = str(tag)
                    if 'Εορτολόγιο' in tag or 'Παγκόσμιες Ημέρες' in tag:
                        continue
                    # Parse with getImage() to expand relative urls
                    tag = self.getImage(tag)
                    if day == 'w':
                        worldlist.append('<br/>' + tag + '.')
                    elif day == 'n':
                        tag = '<br>'+title+'<br/>' + tag
                        self.allList.append(tag)
        if len(worldlist) > 1:
            worldays = ' '.join(worldlist)
            worldays = '<b/>'+self.sanTitle + '<br/>' + worldays
            self.allList.append(worldays)

    def getAll(self):
        self.allList = []
        print('getall',self.online)
        if self.online:
            self.events()
            self.days()
        if len(self.allList) == 0:
            self.allList.append('<br/>' + self.sanTitle + '<br/><br/>Δεν βρέθηκαν γεγονότα, ελέγξτε τη σύνδεσή σας.')
        return self.allList

if __name__ == "__main__":
    a1=Sansimera_data()
    lista = a1.getAll()
    for i in lista:
        print(i)
        input()
