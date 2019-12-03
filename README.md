# Minichain Project

## Dependency

```bash
```

## Kickoff chain

### Init Blockchain service

```bash
cp development/fullchain_init.json blockchain/fullchain.json
export CHAIN_ENDPOINT=http://127.0.0.1:8080
export MINER_ENDPOINT=http://127.0.0.1:9090
python3 blockchain/fullchain.py
```

### Create miner wallet

```bash

```

### Mine Genesis Block

```bash
```

### Init Miner Service

```bash
cp development/mempool_database_init.json miner/mempool_database.json
export CHAIN_ENDPOINT=http://127.0.0.1:8080
export MINER_ENDPOINT=http://127.0.0.1:9090
export MINER_WALLET_ADDRESS=21e8bca257607c7cff2ea0d41af2653ca0e8533732d8b6f980c1e2eca4bcf40dfe0da775969f9335ee64eedf72ae0ea2
```
