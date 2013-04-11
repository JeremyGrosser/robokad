from traceback import format_exc
import logging
import socket

log = logging.getLogger('irc')


class IRC(object):
    def __init__(self, server, nick):
        self.server = server
        self.nick = nick
        self.sock = None

    def connect(self):
        self.sock = socket.socket()
        self.sock.connect(self.server)
        self.send('USER %s %s %s :%s' % (self.nick,
            socket.gethostname(), socket.gethostname(), self.nick))
        self.send('NICK %s' % self.nick)

    def send(self, msg):
        log.debug('>>> %s' % msg)
        self.sock.sendall(msg + '\r\n')

    def readlines(self):
        buf = ''
        while True:
            buf += self.sock.recv(1024)
            while buf.find('\n') != -1:
                line, buf = buf.split('\n', 1)
                line = line.rstrip('\r')
                log.debug('<<< %s' % line)
                yield line


    def run(self):
        for line in self.readlines():
            if line.startswith('PING'):
                self.send('PONG %s' % (line.split(' ', 1)[1]))
                continue
            prefix, command, line = line.split(' ', 2)
            func = getattr(self, 'irc_%s' % command, None)
            prefix = prefix.lstrip(':')
            if func:
                try:
                    func(prefix, line)
                except Exception, e:
                    log.exception('Error handling IRC event')
