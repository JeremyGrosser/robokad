#!/usr/bin/env python
from traceback import format_exc
import random
import os.path
import os
import json
import sys

import irc

#sys.stdout = file('/home/synack/src/robokad/stdout.log', 'a')
#sys.stderr = sys.stdout

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

    def load_config(self, filename='config.json'):
        self.config = json.load(file(filename, 'r'))
    
    def conf(key, default=None):
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
            if channel['key']:
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

            command, args = msg.split(' ', 1)
            command = command.lstrip('!').lower()
            print '%s_%s(%r, %r, %r)' % (actiontype, command, chan, nick, args)

            func = getattr(self, '%s_%s' % (actiontype, command), None)
            if not func and actiontype == 'cmd':
                actiontype = 'any'
                func = getattr(self, '%s_%s' % (actiontype, command), None)

            if func:
                try:
                    func(nick, chan, args)
                except Exception, e:
                    print format_exc()

    def cmd_join(self, nick, chan, args):
        args = args.split(' ', 1)
        if len(args) > 1:
            channel, key = args
            self.send('JOIN %s %s' % (channel, key))
        else:
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
        self.send('PRIVMSG %s :Reloaded config' % chan)

    def cmd_quit(self, nick, chan, args):
        self.send('QUIT :%s' % args)

    def any_quote(self, nick, chan, args):
        args = args.split(' ', 1)
        if not args:
            return
        
        if not os.path.exists('quotes/%s' % args[0]):
            return
        quotes = file('quotes/%s' % args[0], 'r').readlines()
        quote = random.choice(quotes)
        self.send('PRIVMSG %s :%s' % (chan, quote))

    def any_addquote(self, nick, chan, args):
        name, args = args.split(' ', 1)
        if '/' in name or '.' in name:
            self.send('PRIVMSG %s :No' % chan)
            return
        fd = file('quotes/%s' % name, 'a')
        fd.write(args + '\n')
        fd.flush()
        fd.close()
        if chan == self.nick:
            chan = nick
        self.send('PRIVMSG %s :Quote added' % chan)


bot = RoboKad(('irc.freenode.net', 6667), 'robokad')
bot.load_config()
bot.connect()
bot.run()
