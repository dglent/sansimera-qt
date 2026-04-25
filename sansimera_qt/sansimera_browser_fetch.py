import os
import sys


os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QTWEBENGINE_DISABLE_SANDBOX', '1')
os.environ.setdefault(
    'QTWEBENGINE_CHROMIUM_FLAGS',
    '--disable-gpu --disable-software-rasterizer --no-sandbox '
    '--disable-crash-reporter --disable-blink-features=AutomationControlled'
)

try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QObject, QTimer, QUrl
    from PyQt5.QtWebEngine import QtWebEngine
    from PyQt5.QtWebEngineWidgets import QWebEnginePage
    QT_WEBENGINE_IMPORT_ERROR = None
except Exception as err:
    QApplication = None
    QObject = object
    QTimer = None
    QUrl = None
    QtWebEngine = None
    QWebEnginePage = None
    QT_WEBENGINE_IMPORT_ERROR = err


CHALLENGE_MARKERS = (
    'Verifying your browser',
    '/cdn-cgi/challenge-platform',
)


def browser_verification_required(html):
    return any(marker in html for marker in CHALLENGE_MARKERS)


def fetch_with_qt_webengine(url, output_filename, timeout_seconds=40):
    if QT_WEBENGINE_IMPORT_ERROR is not None:
        return False, f'Qt WebEngine unavailable: {QT_WEBENGINE_IMPORT_ERROR}'

    class Fetcher(QObject):
        def __init__(self):
            super(Fetcher, self).__init__()
            self.page = QWebEnginePage(self)
            self.page.profile().setHttpUserAgent(
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
            )
            self.page.loadFinished.connect(self.on_load_finished)
            self.poll_timer = QTimer(self)
            self.poll_timer.setInterval(2000)
            self.poll_timer.timeout.connect(self.poll_html)
            self.timeout_timer = QTimer(self)
            self.timeout_timer.setSingleShot(True)
            self.timeout_timer.timeout.connect(self.on_timeout)
            self.html = ''
            self.success = False

        def start(self):
            self.poll_timer.start()
            self.timeout_timer.start(timeout_seconds * 1000)
            self.page.load(QUrl(url))

        def on_load_finished(self, ok):
            self.poll_html()

        def poll_html(self):
            self.page.toHtml(self.on_html_ready)

        def on_html_ready(self, html):
            self.html = html
            if html and not browser_verification_required(html):
                self.success = True
                self.stop()

        def on_timeout(self):
            self.stop()

        def stop(self):
            self.poll_timer.stop()
            self.timeout_timer.stop()
            QApplication.instance().quit()

    QtWebEngine.initialize()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    fetcher = Fetcher()
    fetcher.start()
    app.exec_()

    if fetcher.success:
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            output_file.write(fetcher.html)
        return True, ''

    if browser_verification_required(fetcher.html):
        return False, 'Browser verification did not complete in time.'

    if fetcher.html:
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            output_file.write(fetcher.html)
        return True, ''

    return False, 'Qt WebEngine fetch failed.'


def main():
    if len(sys.argv) != 3:
        print('Usage: sansimera_browser_fetch.py URL OUTPUT', file=sys.stderr)
        return 2

    url = sys.argv[1]
    output_filename = sys.argv[2]
    success, error = fetch_with_qt_webengine(url, output_filename)
    if success:
        return 0

    if error.startswith('Qt WebEngine unavailable:'):
        print('Qt WebEngine was not available.', file=sys.stderr)
        return 3

    if error:
        print(error, file=sys.stderr)
        if 'verification did not complete' in error.lower():
            return 4
        return 3
    return 5


if __name__ == '__main__':
    sys.exit(main())
