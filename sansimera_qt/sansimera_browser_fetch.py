import os
import logging
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


def configure_logging():
    log_file = os.environ.get('SANSIMERA_QT_LOG_FILE')
    if not log_file:
        logging.basicConfig(
            format='%(asctime)s %(levelname)s: %(message)s'
            ' - %(lineno)s: %(module)s',
            datefmt='%Y/%m/%d %H:%M:%S',
            level=logging.INFO
        )
        return

    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s'
        ' - %(lineno)s: %(module)s',
        datefmt='%Y/%m/%d %H:%M:%S',
        filename=log_file,
        level=os.environ.get('SANSIMERA_QT_LOG_LEVEL', 'INFO')
    )


def browser_verification_required(html):
    return any(marker in html for marker in CHALLENGE_MARKERS)


def fetch_with_qt_webengine(url, output_filename, timeout_seconds=40):
    logging.info('QtWebEngine helper fetch start: %s', url)
    logging.debug('Helper output file: %s', output_filename)
    logging.debug('QT_QPA_PLATFORM=%s', os.environ.get('QT_QPA_PLATFORM'))
    logging.debug('DISPLAY=%s', os.environ.get('DISPLAY'))
    logging.debug('XDG_RUNTIME_DIR=%s', os.environ.get('XDG_RUNTIME_DIR'))

    if QT_WEBENGINE_IMPORT_ERROR is not None:
        logging.error('Qt WebEngine import failed: %s', QT_WEBENGINE_IMPORT_ERROR)
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
            logging.debug('QtWebEngine page load start')
            self.poll_timer.start()
            self.timeout_timer.start(timeout_seconds * 1000)
            self.page.load(QUrl(url))

        def on_load_finished(self, ok):
            logging.debug('QtWebEngine loadFinished ok=%s', ok)
            self.poll_html()

        def poll_html(self):
            logging.debug('QtWebEngine polling html')
            self.page.toHtml(self.on_html_ready)

        def on_html_ready(self, html):
            self.html = html
            logging.debug('QtWebEngine html callback bytes=%s', len(html or ''))
            if html and not browser_verification_required(html):
                self.success = True
                self.stop()

        def on_timeout(self):
            logging.warning('QtWebEngine helper timed out')
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
        logging.info('QtWebEngine helper fetch succeeded, bytes=%s', len(fetcher.html))
        return True, ''

    if browser_verification_required(fetcher.html):
        logging.warning('QtWebEngine helper still sees browser verification')
        return False, 'Browser verification did not complete in time.'

    if fetcher.html:
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            output_file.write(fetcher.html)
        logging.info('QtWebEngine helper wrote fallback html, bytes=%s', len(fetcher.html))
        return True, ''

    logging.error('QtWebEngine helper returned no html')
    return False, 'Qt WebEngine fetch failed.'


def main():
    configure_logging()
    if len(sys.argv) != 3:
        print('Usage: sansimera_browser_fetch.py URL OUTPUT', file=sys.stderr)
        logging.error('Invalid helper arguments: %s', sys.argv)
        return 2

    url = sys.argv[1]
    output_filename = sys.argv[2]
    success, error = fetch_with_qt_webengine(url, output_filename)
    if success:
        logging.info('QtWebEngine helper finished successfully')
        return 0

    if error.startswith('Qt WebEngine unavailable:'):
        print('Qt WebEngine was not available.', file=sys.stderr)
        logging.error(error)
        return 3

    if error:
        print(error, file=sys.stderr)
        logging.error(error)
        if 'verification did not complete' in error.lower():
            return 4
        return 3
    logging.error('QtWebEngine helper failed without error message')
    return 5


if __name__ == '__main__':
    sys.exit(main())
