#!/usr/bin/env python

from collections import defaultdict
from bs4 import BeautifulSoup
import json
import random
import re
import sys


class MarkovChain(object):
    def __init__(self):
        self.d = defaultdict(list)

    def learn(self, sentence):
        sent = re.sub('[\.\?\!\",]', ' ', sentence)
        words = [x for x in sent.split(' ') if x]
        for i, word in enumerate(words[:-2]):
            word2 = words[i+1]
            self.d['%s %s' % (word, word2)].append(words[i+2])

    def generate(self, current=[]):
        word = ' '.join(current[-2:])
        if word in self.d:
            nextword = random.choice(self.d[word])
            current += nextword.split(' ')
            return self.generate(current)
        else:
            return ' '.join(current)
    
    def next(self):
        while True:
            try:
                startword = random.choice(list(self.d.keys()))
                startword = startword.split(' ')
                return self.generate(startword)
            except Exception as e:
                print(str(e))
                continue


def learn_html(chain, sourcefile, subject='Aineko'):
    bs = BeautifulSoup(open(sourcefile, 'r').read())
    for p in bs.find_all('p'):
        text = p.get_text()
        text = text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        while text.find(subject) != -1:
            junk, text = text.split(subject, 1)
            text = text.strip(' ')
            sentence, text = re.split('[\.\?\!]', text, 1)
            if not sentence or not sentence[0].isalpha():
                continue
            chain.learn(sentence)
