import datetime
import hashlib
import json
import multiprocessing 
import time
import requests
import os
from flask import Flask, request
from candidate_block import CandidateBlock

MEMPOOL_DATABASE = os.path.dirname(os.path.realpath(__file__)) + "/mempool_database.json"

MINER_WALLET_ADDRESS = os.environ['MINER_WALLET_ADDRESS']

CHAIN_ENDPOINT = os.environ['CHAIN_ENDPOINT']


class Miner():
    def __init__(self):
        self.mempool = []

    def load_mempool_database(self):
        with open(MEMPOOL_DATABASE, "r") as mempoolDatabaseFile:
            self.mempool = json.loads(mempoolDatabaseFile.read())
    
    def dump_mempool_database(self):
        with open(MEMPOOL_DATABASE, "w") as mempoolDatabaseFile:
            mempoolDatabaseFile.write(json.dumps(self.mempool, indent=2))
    
    def verify_transaction(self, transaction):
        # transaction verification
        verifyTransaction = requests.post('{}/verifytransaction'.format(CHAIN_ENDPOINT), json.dumps(transaction), 
            headers={'Content-Type': 'application/json'})
        return json.loads(verifyTransaction.text)['transactionValid']

    def add_transaction(self, transaction):
        self.load_mempool_database()
        # check if transaction exists
        for tx in self.mempool:
            if tx['id'] == transaction['id']: 
                return "Transaction exists"
        # check if transaction valid
        if self.verify_transaction(transaction):
            self.mempool.append(transaction)
            self.dump_mempool_database()
            return "Transaction submitted to mempool"
        else:
            return "Transaction invalid"

    def clean_mempool(self, latestBlock=None):
        self.load_mempool_database()
        latestBlockContent = json.loads(latestBlock['content'])
        newMempool = []
        for mempoolTx in self.mempool:
            discard = False
            for latestTx in latestBlockContent:
                if mempoolTx['id'] == latestTx['id']:
                    discard = True
                    break
            if not discard:
                newMempool.append(mempoolTx)
        self.mempool = newMempool
        self.dump_mempool_database()

    def get_candidate_block_data(self, latestBlock=None):
        self.load_mempool_database()
        candidateBlockContent = []
        
        if latestBlock == None:
            candidateBlockContent = self.mempool
        else:
            latestBlockContent = json.loads(latestBlock['content'])
            for candidateTx in self.mempool:
                repeated = False
                for latestTx in latestBlockContent:
                    if candidateTx['id'] == latestTx['id']:
                        repeated = True
                        break
                if not repeated:
                    candidateBlockContent.append(candidateTx)
        
        return candidateBlockContent

    def get_latest_block(self):
        response = requests.get('{}/latestblock'.format(CHAIN_ENDPOINT))
        if response.text == 'None':
            return None
        return json.loads(response.text)

    def get_current_bounty(self):
        response = requests.get('{}/bounty'.format(CHAIN_ENDPOINT))
        return json.loads(response.text)['currentBounty']

    def craft_coinbase_transaction(self):
        coinbaseTransaction = {
            "type": "coinbase",
            "receiver": MINER_WALLET_ADDRESS,
            "amount": self.get_current_bounty()
        }
        coinbaseTransaction['id'] = hashlib.sha256((coinbaseTransaction['type'] 
                                                    + coinbaseTransaction['receiver'] 
                                                    + str(coinbaseTransaction['amount'])).encode()).hexdigest()
        return coinbaseTransaction

    def mine(self, latestBlock=None):
        # get latest block
        if latestBlock == None:
            latestBlock = self.get_latest_block()

        # take data from mempool
        candidateBlockContent = self.get_candidate_block_data(latestBlock)
        if len(candidateBlockContent) == 0:
            print("No transaction left in mempool :)")
            return

        # append coinbase transaction
        candidateBlockContent = [self.craft_coinbase_transaction()] + candidateBlockContent

        # craft new block and mine
        print("Hi, I'm mining over here")
        if latestBlock == None:
            candidateBlockIndex = 0
            candidateBlockPrevHash = 'NoHash'
        else:
            candidateBlockIndex = latestBlock['index'] + 1
            candidateBlockPrevHash = latestBlock['hash']
        
        candidateBlock = CandidateBlock(
            candidateBlockIndex, candidateBlockPrevHash, 
            json.dumps(candidateBlockContent), str(datetime.datetime.utcnow())
        )
        candidateBlock.mine()
        minedBlock = candidateBlock.returnBlockData()
        print("Here's the mined block")
        print(json.dumps(minedBlock, indent=2))
        print("Done")
        # submit mined block to server
        response = requests.post('{}/candidateblock'.format(CHAIN_ENDPOINT), json.dumps(minedBlock), 
            headers={'Content-Type': 'application/json'})
        print(response.text)
        

def start_mining(latestBlock=None):
    miner = Miner()
    miner.mine(latestBlock)
    del miner

miner_node = Flask(__name__)

# Add new wallet
@miner_node.route('/wallet', methods = ['POST'])
def wallet():
    if request.method == 'POST':
        print(request.json)
        return "This will be used to get the blockchain's wallet \n"

# Add new transaction to the pool
@miner_node.route('/transaction', methods = ['POST'])
def transaction():
    if request.method == 'POST':
        print(request.json)
        transaction = request.get_json()
        miner = Miner()
        addTransactionMessage = miner.add_transaction(transaction)
        del miner
        if addTransactionMessage == "Transaction submitted to mempool":
            # if there's a mining going on, keep going, otherwise start mining
            global miningProcess
            if not miningProcess.is_alive():
                miningProcess = multiprocessing.Process(target=start_mining)
                miningProcess.start()
        
        return {
            "transaction_message": addTransactionMessage
        }

# Event new block mined/verified
@miner_node.route('/newblock', methods = ['POST'])
def newblock():
    if request.method == 'POST':
        latestBlock = request.get_json()
        miner = Miner()
        miner.clean_mempool(latestBlock)
        del miner
        # if there's a mining going on, stop mining
        global miningProcess
        if miningProcess.is_alive():
            miningProcess.terminate()
        # trigger mining
        miningProcess = multiprocessing.Process(target=start_mining, args=([latestBlock]))
        miningProcess.start()
        
        return "This will be used to stop mining a current block and start a new block \n"

@miner_node.route('/checkmining', methods = ['GET'])
def checkmining():
    if request.method == 'GET':
        # if there's a mining going on, keep going, otherwise start mining
        if miningProcess.isAlive():
            return "Still mining\n"
        else:
            return "Mining stopped\n"

if __name__ == '__main__':
    miningProcess = multiprocessing.Process()
    miner_node.run(host='0.0.0.0', port=9090, debug=True)