import datetime
import hashlib
import json
import multiprocessing 
import time
import requests
import os

CHAIN_ENDPOINT = os.environ['CHAIN_ENDPOINT']

def charToNum(char):
    if ord(char) >= ord('a') and ord(char) <= ord('z'):
        return ord(char) - ord('a') + 10
    if ord(char) >= ord('0') and ord(char) <= ord('9'): 
        return ord(char) - ord('0')
    return None

def numToChar(num):
    if num <= 9:
        return chr(num + ord('0'))
    if num >= 10 and num <= 35:
        return chr(num + ord('a') - 10)
    return None

def stringIncrease(nonce):
    newNonce = ''
    leftOver = 1
    for c in reversed(nonce):
        if charToNum(c) + leftOver > 35:
            newNonce = numToChar(0) + newNonce
            leftOver = 1
        else:
            newNonce = numToChar(charToNum(c) + leftOver) + newNonce
            leftOver = 0
    if leftOver:
        newNonce = numToChar(1) + newNonce
    return newNonce

class CandidateBlock():
    def __init__(self, index, prevHash, content, timestamp):
        self.index = index
        self.prevHash = prevHash
        self.content = content
        self.timestamp = timestamp
        self.hash = ''

    def mine(self):
        currentDifficulty = json.loads(requests.get('{}/difficulty'.format(CHAIN_ENDPOINT)).text)['currentDifficulty']
        iNonce = '0'
        iHash = None
        while True:
            iHash = hashlib.sha256((str(self.index) 
                                    + self.prevHash 
                                    + self.content 
                                    + self.timestamp 
                                    + iNonce).encode()).hexdigest()
            if iHash.startswith(currentDifficulty):
                break
            iNonce = stringIncrease(iNonce)
        self.hash = iHash
        self.nonce = iNonce
        return iHash

    def returnBlockData(self):
        return {
            'index': self.index,
            'prevHash': self.prevHash,
            'content': self.content,
            'timestamp': self.timestamp,
            'hash': self.hash,
            'nonce': self.nonce
        }