import datetime
import hashlib
import json
import requests
import os
from ecdsa import SigningKey, VerifyingKey
from flask import Flask, request

DATABASE_FILE = os.path.dirname(os.path.realpath(__file__)) + '/fullchain.json'

class Block():
    def __init__(self, blockData):
        self.blockData = blockData
        self.index = blockData['index']
        self.prevHash = blockData['prevHash']
        self.content = blockData['content']
        self.timestamp = blockData['timestamp']
        self.blockHash = blockData['hash']
        self.nonce = blockData['nonce']

    def verify_hash(self, difficulty):
        if self.blockHash == hashlib.sha256((str(self.index) + self.prevHash + self.content + self.timestamp + self.nonce).encode()).hexdigest() \
        and self.blockHash.startswith(difficulty):
            return True
        return False

    def return_transactions(self):
        return json.loads(self.content)

    def return_block_data(self):
        return self.blockData

class Address():
    def __init__(self, walletData, initWallet=False):
        if initWallet:    
            self.addressName = walletData['addressName']
            self.pubKey = walletData['pubKey']
            self.coin = 0
            self.transactions = []
        else:
            self.load_wallet_data(walletData)

    def load_wallet_data(self, walletData):
        self.addressName = walletData['addressName']
        self.pubKey = walletData['pubKey']
        self.coin = walletData['coin']
        self.transactions = json.loads(walletData['transactions'])

    def verify_tx(self, tx):
        # does the address has enough coin for the transaction
        if tx['amount'] > self.coin:
            print("Address does not have enough money")
            return False
        # verify signature
        txVerifyingKey = VerifyingKey.from_string(bytearray.fromhex(self.pubKey))
        txSignature = bytes.fromhex(tx['signature'])
        txHash = hashlib.sha256((tx['type'] + tx['sender'] + tx['receiver']+ str(tx['amount'])).encode()).hexdigest()
        if not txVerifyingKey.verify(txSignature, txHash.encode()):
            print("Invalid signature")
            return False
        del txVerifyingKey, txSignature, txHash
        return True

    def process_tx(self, transaction):
        if transaction['receiver'] == self.pubKey:
            self.coin += transaction['amount']
        if transaction['sender'] == self.pubKey:
            self.coin -= transaction['amount']
        self.transactions.append(transaction)
        return 
    
    def process_coinbase(self, transaction):
        if transaction['type'] == 'coinbase':
            self.coin += transaction['amount']
        self.transactions.append(transaction)
        return

    def return_wallet_data(self):
        return {
            "addressName": self.addressName,
            "pubKey": self.pubKey,
            "coin": self.coin, 
            "transactions": json.dumps(self.transactions)
        }

class Blockchain():
    def __init__(self):
        self.chain = []
        self.totalCoin = 0
        self.addresses = {}
        self.ledger = []

    def load_database(self):
        with open(DATABASE_FILE, "r") as databaseFile:
            data = json.loads(databaseFile.read())
            # load the chain
            for blockData in data['chain']:
                self.chain.append(Block(blockData))
            self.totalCoin = data['totalCoin']
            # load the addresses
            for address in data['addresses'].keys():
                self.addresses[address] = Address(data['addresses'][address])
            self.ledger = data['ledger']

    def dump_database(self):
        data = {}
        # dump the chain
        data['chain'] = []
        for block in self.chain:
            data['chain'].append(block.return_block_data())
        data['totalCoin'] = self.totalCoin
        # dump the address
        data['addresses'] = {}
        for address in self.addresses.keys():
             data['addresses'][address] = self.addresses[address].return_wallet_data()
        data['ledger'] = self.ledger
        with open(DATABASE_FILE, "w") as databaseFile:
            databaseFile.write(json.dumps(data, indent=2))

    def process_coinbase_transaction(self, transaction):
        self.addresses[transaction['receiver']].process_coinbase(transaction)
        self.totalCoin += transaction['amount']
        return
    
    def process_add_transaction(self, transaction):
        self.addresses[transaction['pubKey']] = Address({'pubKey': transaction['pubKey'],
                                          'addressName': transaction['walletName']}, True)
        return "New address added to the ledger"

    def process_tx_transaction(self, transaction):
        self.addresses[transaction['receiver']].process_tx(transaction)
        self.addresses[transaction['sender']].process_tx(transaction)
        return

    def verify_coinbase_transaction(self, candidateTransaction):
        if  len(candidateTransaction.keys()) != 4 or \
            'type' not in candidateTransaction or \
            'receiver' not in candidateTransaction or \
            'amount' not in candidateTransaction or \
            'id' not in candidateTransaction:
            return False
        if candidateTransaction['type'] != 'coinbase':
            return False
        if candidateTransaction['id'] != hashlib.sha256((candidateTransaction['type'] 
                                                        + candidateTransaction['receiver'] 
                                                        + str(candidateTransaction['amount'])).encode()).hexdigest():
            return False                                        
        if not candidateTransaction['receiver'] in self.addresses:
            return False
        if candidateTransaction['amount'] != self.return_current_bounty():
            return False
        return True

    def verify_add_transaction(self, candidateTransaction):
        if  len(candidateTransaction.keys()) != 4 or \
            'type' not in candidateTransaction or \
            'pubKey' not in candidateTransaction or \
            'walletName' not in candidateTransaction or \
            'id' not in candidateTransaction:
            return False
        if candidateTransaction['id'] != hashlib.sha256((candidateTransaction['type'] 
                                                        + candidateTransaction['pubKey'] 
                                                        + str(candidateTransaction['walletName'])).encode()).hexdigest():
            return False                                                        
        if candidateTransaction['pubKey'] in self.addresses:
            return False
        return True

    def verify_tx_transaction(self, candidateTransaction):
        if  len(candidateTransaction.keys()) != 6 or \
            'id' not in candidateTransaction or \
            'type' not in candidateTransaction or \
            'sender' not in candidateTransaction or \
            'receiver' not in candidateTransaction or \
            'amount' not in candidateTransaction or \
            'signature' not in candidateTransaction:
            print("Transaction keys are invalid")
            return False
        if candidateTransaction['id'] != hashlib.sha256((candidateTransaction['type'] 
                                                        + candidateTransaction['sender'] 
                                                        + candidateTransaction['receiver']
                                                        + str(candidateTransaction['amount'])
                                                        + candidateTransaction['signature']).encode()).hexdigest():
            print("Transaction id is invalid")
            return False
        if candidateTransaction['sender'] not in self.addresses or \
           candidateTransaction['receiver'] not in self.addresses:
            print("Transaction addresses are invalid")
            return False
        if not self.addresses[candidateTransaction['sender']].verify_tx(candidateTransaction):
            print("Transaction logic is invalid")
            return False
        return True

    def verify_transaction(self, transaction):
        if transaction['type'] == 'coinbase' and not self.verify_coinbase_transaction(transaction):
            return False
        if transaction['type'] == 'add' and not self.verify_add_transaction(transaction):
            return False
        if transaction['type'] == 'tx' and not self.verify_tx_transaction(transaction):
            return False
        return True

    def verify_candidate_transactions(self, candidateTransactions):
        # if it's not genesis block, then verify the coinbase transaction
        if len(self.chain) != 0 and not self.verify_coinbase_transaction(candidateTransactions[0]):
            return False
        
        for i in range(1, len(candidateTransactions) - 1):
            candidateTransaction = candidateTransactions[i]
            if candidateTransaction['type'] == 'coinbase':
                return False
            if candidateTransaction['type'] == 'add' and not self.verify_add_transaction(candidateTransaction):
                return False
            if candidateTransaction['type'] == 'tx' and not self.verify_tx_transaction(candidateTransaction):
                return False

        return True

    def process_transaction(self, transaction):
        if transaction['type'] == 'add':
            self.process_add_transaction(transaction)
            return "Added another address"
        elif transaction['type'] == 'tx':
            self.process_tx_transaction(transaction)
            return "Transaction made"
        elif transaction['type'] == 'coinbase':
            self.process_coinbase_transaction(transaction)
            return "Rewarded the miner"

    def process_candidate_block(self, candidateBlockData):
        candidateBlock = Block(candidateBlockData)

        if len(self.chain) != 0 and \
            self.return_latest_block()['hash'] != candidateBlockData['prevHash']:
            return "Block prevHash is invalid"

        if not candidateBlock.verify_hash(self.return_current_difficulty()):
            return "Block hash is invalid!"
        
        candidateTransactions = candidateBlock.return_transactions()
        # verify candidate transactions
        if not self.verify_candidate_transactions(candidateTransactions):
            return "Block transactions are invalid"
        
        # process transactions
        for transaction in candidateTransactions:
            self.process_transaction(transaction)
            self.ledger.append(transaction)
        
        self.chain.append(candidateBlock)
        # broadcast new block event
        try:
            response = requests.post('http://127.0.0.1:9090/newblock', json.dumps(candidateBlock.return_block_data()), 
                headers={'Content-Type': 'application/json'})
        except:
            pass

        return "Block added"

    def return_chain(self):
        return self.chain

    def return_latest_block(self):
        if len(self.chain) == 0:
            return None
        return self.chain[-1].return_block_data()
    
    def return_current_bounty(self):
        chainLength = len(self.chain)
        interval = 10
        mileStone = 0
        bounty = 2048
        while bounty > 1:
            mileStone += 10
            if chainLength >= mileStone:
                bounty /= 2
            else:
                break
        return bounty

    def return_current_difficulty(self):
        return (int((len(self.chain))/10) + 5) * '0'
    
    def return_address(self, address):
        return self.addresses[address].return_wallet_data()


fullchain_node = Flask(__name__)

blockchain = Blockchain()
blockchain.load_database()

@fullchain_node.route('/wallet/<wallet_address>', methods = ['GET'])
def wallet(wallet_address):
    if request.method == 'GET':
        return json.dumps(blockchain.return_address(wallet_address))

@fullchain_node.route('/candidateblock', methods = ['POST'])
def candidateblock():
    if request.method == 'POST':
        print(request.json)
        candidateBlockData = request.get_json()
        processMessage = blockchain.process_candidate_block(candidateBlockData)
        blockchain.dump_database()
        return json.dumps({
            'message': processMessage
        })

@fullchain_node.route('/latestblock', methods = ['GET'])
def latestblock():
    if request.method == 'GET':
        latestBlock = blockchain.return_latest_block()
        if latestBlock == None:
            latestBlockPayload = 'None'
        else:
            latestBlockPayload = json.dumps(latestBlock)
        return latestBlockPayload

@fullchain_node.route('/bounty', methods = ['GET'])
def bounty():
    if request.method == 'GET':
        global blockchain
        currentBountyPayload = {
            'currentBounty': blockchain.return_current_bounty()
        }
        return json.dumps(currentBountyPayload)

@fullchain_node.route('/difficulty', methods = ['GET'])
def difficulty():
    if request.method == 'GET':
        global blockchain
        currentBountyPayload = {
            'currentDifficulty': blockchain.return_current_difficulty()
        }
        return json.dumps(currentBountyPayload)

@fullchain_node.route('/verifytransaction', methods = ['POST'])
def verifytransaction():
    if request.method == 'POST':
        global blockchain
        transaction = request.get_json()
        verifyTransactionPayload = {
            'transactionValid': blockchain.verify_transaction(transaction)
        }
        return json.dumps(verifyTransactionPayload)

if __name__ == '__main__':
    fullchain_node.run(port=8080, debug=True)