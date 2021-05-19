from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import sys

attrs = {'class': 'meaning'}


def define(term):
    params = urllib.parse.urlencode({'term': term})
    req = urllib.request.Request('http://www.urbandictionary.com/define.php?%s' % params)
    res = urllib.request.urlopen(req, timeout=5)
    soup = BeautifulSoup(res.read(), from_encoding='utf-8', features='lxml')
    for definition in soup.find_all('div', **attrs):
        yield definition.text.strip('\r\n \t').replace('\n', ' ')
    return


if __name__ == '__main__':
    for d in define(''.join(sys.argv[1:])):
        print(d)
