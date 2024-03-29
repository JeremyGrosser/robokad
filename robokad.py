#!/usr/bin/env python3
from traceback import format_exc
import urbandictionary
import logging
import random
import os.path
import os
import json
import sys

import markov
import irc

os.chdir('/home/synack/src/robokad')
root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.FileHandler('/home/synack/src/robokad/stdout.log')
root.addHandler(handler)

log = logging.getLogger('robokad')

# >>> JOIN #synacktest
# <<< :robokad MODE robokad :+i
# <<< :robokad!~robokad@184.72.226.125 JOIN #synacktest
# <<< :morgan.freenode.net 353 robokad @ #synacktest :robokad @synack
# <<< :morgan.freenode.net 366 robokad #synacktest :End of /NAMES list.
# <<< :synack!~synack@pdpc/supporter/active/synack PRIVMSG #synacktest :!join #test2


class RoboKad(irc.IRC):
    def __init__(self, *args, **kwargs):
        irc.IRC.__init__(self, *args, **kwargs)
        self.config = {}
        self.markov = markov.MarkovChain()
        self.preload_markov()
        self.codenames = [
                open('codenames/firstnames.txt', 'r').read().split('\n')[:-1],
                open('codenames/lastnames.txt', 'r').read().split('\n')[:-1],
        ]

    def preload_markov(self):
        count = 0
        for filename in os.listdir('quotes'):
            filename = 'quotes/%s' % filename
            with open(filename, 'r') as fd:
                for line in fd:
                    line = line.rstrip('\r\n\t ')
                    if line.startswith('<'):
                        line = line.split('>', 1)[-1]
                    self.markov.learn(line)
                    count += 1
        log.info('Markov learned %i quotes', count)

    def load_config(self, filename='config.json'):
        try:
            self.config = json.load(open(filename, 'r'))
        except:
            log.exception('Error loading %s' % filename)
    
    def conf(self, key, default=None):
        value = self.config
        for k in key.split('.'):
            try:
                value = value[k]
            except KeyError:
                return default
        #sys.stderr.write('config: %s=%r\n' % (key, value))
        return value

    def irc_376(self, prefix, line):
        for channel in self.conf('autojoin', []):
            if channel.get('key', None):
                self.send('JOIN %(channel)s %(key)s' % channel)
            else:
                self.send('JOIN %(channel)s' % channel)

    def irc_PRIVMSG(self, prefix, msg):
        nick = prefix.split('!', 1)[0]
        chan, msg = msg.split(' ', 1)
        msg = msg.lstrip(':')
        if msg.startswith('!'):
            if nick in self.conf('admins', []):
                actiontype = 'cmd'
            else:
                actiontype = 'any'

            command = msg.split(' ', 1)
            if len(command) > 1:
                command, args = command
            else:
                command = command[0]
                args = []
            command = command.lstrip('!').lower()
            logging.debug('%s_%s(%r, %r, %r)' % (actiontype, command, chan, nick, args))

            func = getattr(self, '%s_%s' % (actiontype, command), None)
            if not func and actiontype == 'cmd':
                actiontype = 'any'
                func = getattr(self, '%s_%s' % (actiontype, command), None)

            if func:
                try:
                    func(nick, chan, args)
                except Exception as e:
                    log.exception('Error handling command: %s_%s %r' % (actiontype, command, func))

        if msg.startswith(self.nick):
            self.send('PRIVMSG %s :%s' % (chan, self.markov.next()))

    def _replyto(self, nick, chan):
        if chan == self.nick:
            return nick
        else:
            return chan

    def cmd_join(self, nick, chan, args):
        args = args.split(' ', 1)
        if len(args) > 1:
            channel, key = args
            self.send('JOIN %s %s' % (channel, key))
        else:
            channel = args[0]
            self.send('JOIN %s' % channel)

    def cmd_part(self, nick, chan, args):
        for channel in args.split(' '):
            self.send('PART %s' % channel)

    def cmd_say(self, nick, chan, args):
        if args.startswith('#'):
            chan, args = args.split(' ', 1)
        self.send('PRIVMSG %s :%s' % (chan, args))

    def cmd_reload(self, nick, chan, args):
        self.load_config()
        replyto = self._replyto(nick, chan)
        self.send('PRIVMSG %s :Reloaded config' % replyto)

    def cmd_quit(self, nick, chan, args):
        self.send('QUIT :%s' % args)

    def any_quote(self, nick, chan, args):
        args = args.split(' ', 1)
        if not args:
            return
        
        if not os.path.exists('quotes/%s' % args[0]):
            return
        quotes = open('quotes/%s' % args[0], 'r').readlines()
        quote = random.choice(quotes)

        replyto = self._replyto(nick, chan)
        self.send('PRIVMSG %s :%s' % (replyto, quote))

    def any_addquote(self, nick, chan, args):
        replyto = self._replyto(nick, chan)
        name, args = args.split(' ', 1)
        if '/' in name or '.' in name:
            self.send('PRIVMSG %s :No' % replyto)
            return
        fd = open('quotes/%s' % name, 'a')
        fd.write(args + '\n')
        fd.flush()
        fd.close()
        if chan == self.nick:
            chan = nick

        self.markov.learn(args)
        self.send('PRIVMSG %s :Quote added' % replyto)

    def any_define(self, nick, chan, args):
        replyto = self._replyto(nick, chan)

        if not self.config.get('define_enabled', True):
            self.send('PRIVMSG %s :no.' % replyto)
            return
        term = args
        definition = list(urbandictionary.define(term))
        if not definition:
            self.send('PRIVMSG %s :%s is undefined' % (replyto, term))
        else:
            d = random.choice(definition)
            self.send('PRIVMSG %s :%s' % (replyto, d))

    def any_codename(self, nick, chan, args):
        codename = ' '.join([random.choice(x) for x in self.codenames]).upper()
        replyto = self._replyto(nick, chan)
        self.send('PRIVMSG %s :%s' % (replyto, codename))


bot = RoboKad(('irc.libera.chat', 6697), 'robokad')
bot.load_config()
bot.connect_ssl()
bot.run()
