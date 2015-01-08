from bs4 import BeautifulSoup
import urllib2
import urllib
import sys

attrs = {'class': 'meaning'}


def define(term):
    params = urllib.urlencode({'term': term})
    req = urllib2.Request('http://www.urbandictionary.com/define.php?%s' % params)
    res = urllib2.urlopen(req, timeout=5)
    soup = BeautifulSoup(res.read())
    for definition in soup.find_all('div', **attrs):
        yield definition.text.strip('\r\n \t').replace('\n', ' ')
    return


if __name__ == '__main__':
    for d in define(''.join(sys.argv[1:])):
        print d
