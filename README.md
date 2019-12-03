# Minichain Project

## Dependency

- python3 (ecdsa, requests, flask)

## Kickoff chain

### Init Blockchain service

```bash
cp development/fullchain_init.json blockchain/fullchain.json
export CHAIN_ENDPOINT=http://127.0.0.1:8080
export MINER_ENDPOINT=http://127.0.0.1:9090
python3 blockchain/fullchain.py
```

### Create miner wallet

```python
from wallet.wallet import Wallet
wallet = Wallet('<wallet_file_name>', True, '<wallet_name>')
```

### Mine Genesis Block

```bash
```

### Init Miner Service

```bash
cp development/mempool_database_init.json miner/mempool_database.json
export CHAIN_ENDPOINT=http://127.0.0.1:8080
export MINER_ENDPOINT=http://127.0.0.1:9090
export MINER_WALLET_ADDRESS=<wallet_pubKey>
python3 miner/miner.py
```

## Transaction

### Configure chain/miner endpoints

```bash
# published endpoint of chain service
export CHAIN_ENDPOINT=http://ec2-54-169-169-0.ap-southeast-1.compute.amazonaws.com:8080
# published endpoint of miner service
export MINER_ENDPOINT=http://ec2-54-169-169-0.ap-southeast-1.compute.amazonaws.com:9090
```

### Create and Register a wallet

```python
from wallet.wallet import Wallet
wallet = Wallet('<wallet_file_name>', True, '<wallet_name>')
wallet.register_wallet()
```

### Look up wallets

#### Your wallet

```python
from wallet.wallet import Wallet
wallet = Wallet('<wallet_file_name>')
wallet.get_wallet_data()
```

#### All wallets

```bash
# all wallets
curl ${CHAIN_ENDPOINT}/wallets
```

### Send Coin

```python
from wallet.wallet import Wallet
wallet = Wallet('<wallet_file_name>')
wallet.send_coin('<other_wallet_pubKey>', <coin_amount>)
```
