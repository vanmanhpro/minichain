import datetime
import hashlib
import json
import requests
import os
from ecdsa import SigningKey, VerifyingKey

PRIVATE_KEY_LOCATION = os.path.dirname(os.path.realpath(__file__)) + '/miner.json'

CHAIN_ENDPOINT = os.environ['CHAIN_ENDPOINT']
MINER_ENDPOINT = os.environ['MINER_ENDPOINT']

class Wallet():
    def __init__(self, walletFileLocation, initWallet=False, walletName='default'):
        if initWallet:
            self.privKey = SigningKey.generate()
            self.pubKey = self.privKey.verifying_key
            self.walletName = walletName
            self.dump_wallet(walletFileLocation)
        else:
            self.load_wallet(walletFileLocation)

    def load_wallet(self, walletFileLocation):
        with open(walletFileLocation, "r") as walletFile:
            wallet_data = json.loads(walletFile.read())
            self.privKey = SigningKey.from_string(bytearray.fromhex(wallet_data['privKey']))
            self.pubKey = VerifyingKey.from_string(bytearray.fromhex(wallet_data['pubKey']))
            self.walletName = wallet_data['walletName']

    def dump_wallet(self, walletFileLocation):
        with open(walletFileLocation, "w") as walletFile:
            walletFile.write(json.dumps({
                'privKey': self.privKey.to_string().hex(),
                'pubKey': self.pubKey.to_string().hex(),
                'walletName': self.walletName
            }, indent=2))
        
    def get_wallet_data(self):
        response = requests.get('{}/wallet/{}'.format(CHAIN_ENDPOINT, self.pubKey.to_string().hex()))
        return json.loads(response.text)

    def register_wallet_payload(self):
        walletRegPayload = {
            'type' :  'add',
            'pubKey' : self.pubKey.to_string().hex(),
            'walletName' : self.walletName
        }
        self.pubKey.to_string().hex()
        walletRegPayload['id'] = hashlib.sha256((walletRegPayload['type']
            + walletRegPayload['pubKey'] + walletRegPayload['walletName']).encode()).hexdigest()
        return walletRegPayload

    def register_wallet(self):
        walletRegPayload = {
            'type' :  'add',
            'pubKey' : self.pubKey.to_string().hex(),
            'walletName' : self.walletName
        }
        self.pubKey.to_string().hex()
        walletRegPayload['id'] = hashlib.sha256((walletRegPayload['type']
            + walletRegPayload['pubKey'] + walletRegPayload['walletName']).encode()).hexdigest()
        print(json.dumps(walletRegPayload, indent=2))
        response = requests.post('{}/transaction'.format(MINER_ENDPOINT), json.dumps(walletRegPayload), 
            headers={'Content-Type': 'application/json'})
        print(response.text)

    def send_coin(self, receiverPubKey, amount):
        txPayload = {
            "type": "tx",
            "sender": self.pubKey.to_string().hex(),
            "receiver": receiverPubKey,
            "amount": amount
        }
        txHash = hashlib.sha256((txPayload['type'] 
                                + txPayload['sender'] 
                                + txPayload['receiver']
                                + str(txPayload['amount'])).encode()).hexdigest()
        txSignature = self.privKey.sign(txHash.encode())
        txPayload['signature'] = txSignature.hex()
        txPayload['id'] = hashlib.sha256((txPayload['type'] 
                                        + txPayload['sender'] 
                                        + txPayload['receiver']
                                        + str(txPayload['amount'])
                                        + txPayload['signature']).encode()).hexdigest()
        print(json.dumps(txPayload, indent=2))
        # verifyTransaction = requests.post('{}/verifytransaction'.format(CHAIN_ENDPOINT), , json.dumps(txPayload), 
        #     headers={'Content-Type': 'application/json'})
        # print(verifyTransaction.text)
        response = requests.post('{}/transaction'.format(MINER_ENDPOINT), json.dumps(txPayload), 
            headers={'Content-Type': 'application/json'})
        print(response.text)

if __name__ == '__main__':
    wallet = Wallet(PRIVATE_KEY_LOCATION)
    # wallet.register_wallet()
    # wallet.send_coin('839c4e6d6a76ec4a2af86beec09516ef285583c25c7500b69fd38a58daf773d3584c50bab3868f2ed78593753d8588f0',10)
    # print(json.dumps(wallet.get_wallet_data(), indent=2))

    