import glob
import re
import requests
import youtube_dl.utils as ytdl_utils
from bs4 import BeautifulSoup
from time import sleep
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

CIPHERS = 'DEFAULT:@SECLEVEL=2'

dYdlOptions = {'continuedl'         : True,
               'nooverwrites'       : True,
               'ignoreerrors'       : True,
               'restrictfilenames'  : True,
               'writeinfojson'      : True,
               'writeannotations'   : True,
               'nopostoverwrites'   : True,
               'download_archive'   : 'dl_hist_{}.txt',
               'outtmpl'            : None,
               }

dHeaders = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"}

session = requests.Session()
dCookiesParsed = {}


def randomizeHeader():
    dHeaders['User-Agent'] = randomizeUserAgent()


def randomizeUserAgent():
    return ytdl_utils.random_user_agent()


def parseCookieFile(sCookiesTxt):
    """
    Parse a cookies text file and return a dictionary of key-value pairs
    compatible with requests.
    """
    dCookies = {}
    with open(sCookiesTxt, 'r') as fp:
        for line in fp:
            if '#' in line or 'href' in line or len(line) == 1:
                continue
            if not re.match(r'^\#', line):
                lineFields = line.strip().split('\t')
                dCookies[lineFields[5]] = lineFields[6]

    global dCookiesParsed
    dCookiesParsed.update(dCookies)


def parseCookies(sDirectory):
    """
    Scans a directory for cookie text files.

    The cookie file must begin with:

        # Netscape HTTP Cookie File

    If that header line is not seen, the text file will be ignored.
    """
    sRe = '# Netscape HTTP Cookie File'
    lTextFiles = glob.glob(rf"{sDirectory}\*.txt")

    for sTxt in lTextFiles:
        with open(sTxt, 'r') as fp:
            sFirstLine = fp.readline().rstrip()
            if sFirstLine == sRe:
                print(f"Parsing {sTxt} for cookies...")
                parseCookieFile(sTxt)
            else:
                print(f"Skipping {sTxt}...")
        sleep(0.250)
    sleep(1)


def addCipher(sPrefix):
    session.mount(sPrefix, CipherAdapter())


def runYtdl():
    pass


class Page:

    def __init__(self, url):
        self.url = url
        self.content = session.get(url, headers=dHeaders, cookies=dCookiesParsed)
        self.soup = BeautifulSoup(self.content.text, 'html.parser')
        self.videos = []


    def _extract_video_urls(self, sFilter=None):
        """
        Extract video URLs from a single playlist page.
        """
        for a in self.soup.find_all('a', href=True):
            href = a['href']
            if 'http' not in href:
                continue
            if sFilter is not None and sFilter not in href:
                continue
            if href not in self.videos:
                self.videos.append(a['href'])


    def _html_to_text(self, sFileName=None):
        if sFileName is None:
            sFileName = "html_content.txt"
        text_file = open(sFileName, "w", encoding='utf-8')
        text_file.write(self.content.text)
        text_file.close()


class CipherAdapter(HTTPAdapter):
    # Sourced from https://stackoverflow.com/questions/64967706/python-requests-https-code-403-without-but-code-200-when-using-burpsuite

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super(CipherAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super(CipherAdapter, self).proxy_manager_for(*args, **kwargs)
