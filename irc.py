from traceback import format_exc
import logging
import socket
import ssl

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

    def connect_ssl(self):
        self.sock = ssl.wrap_socket(socket.socket(), ssl_version=ssl.PROTOCOL_TLSv1_2, cert_reqs=ssl.CERT_REQUIRED, ca_certs='/etc/ssl/cert.pem')
        self.sock.connect(self.server)
        self.send('USER %s %s %s :%s' % (self.nick,
            socket.gethostname(), socket.gethostname(), self.nick))
        self.send('NICK %s' % self.nick)

    def send(self, msg):
        log.debug('>>> %s' % msg)
        self.sock.sendall(msg + u'\r\n')

    def readlines(self):
        buf = ''
        while True:
            chunk = self.sock.recv(1024)
            if not chunk:
                break
            buf += chunk
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
        log.critical('Connection lost')
