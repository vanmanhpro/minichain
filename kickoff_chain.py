import datetime
import hashlib
import json
import multiprocessing 
import time
import requests
import os
from flask import Flask, request
from miner.miner import CandidateBlock
from wallet.wallet import Wallet

CHAIN_ENDPOINT = os.environ['CHAIN_ENDPOINT']

if __name__ == '__main__':
    # wallet_manh = Wallet('wallet/manh.json', True, 'vanmanhpro')
    # wallet_miner = Wallet('wallet/miner.json', True, 'miner_x')
    wallet_manh = Wallet('wallet/manh.json')
    wallet_miner = Wallet('wallet/miner.json')
    # kick off a block here
    candidateBlockContent = [wallet_manh.register_wallet_payload(), wallet_miner.register_wallet_payload()]
    candidateBlock = CandidateBlock(0,'xxx',json.dumps(candidateBlockContent),str(datetime.datetime.utcnow()))
    candidateBlock.mine()
    print(json.dumps(candidateBlock.returnBlockData(), indent=2))
    candidateBlockData = candidateBlock.returnBlockData()

    response = requests.post('{}/candidateblock'.format(CHAIN_ENDPOINT), json.dumps(candidateBlockData), 
                headers={'Content-Type': 'application/json'})

    print(response.text)