curl -X POST -H "Content-Type: application/json" -d @sample_add.json localhost:9090/transaction
curl -X POST -H "Content-Type: application/json" -d @new_block_sample.json localhost:9090/newblock
curl -X GET -H "Content-Type: application/json" localhost:9090/checkmining
curl localhost:8080/wallet/839c4e6d6a76ec4a2af86beec09516ef285583c25c7500b69fd38a58daf773d3584c50bab3868f2ed78593753d8588f0
curl localhost:8080/bounty
curl localhost:8080/chain
curl localhost:8080/ledger
curl localhost:8080/wallets
export CHAIN_ENDPOINT=http://127.0.0.1:8080
export MINER_ENDPOINT=http://127.0.0.1:9090
export MINER_WALLET_ADDRESS=21e8bca257607c7cff2ea0d41af2653ca0e8533732d8b6f980c1e2eca4bcf40dfe0da775969f9335ee64eedf72ae0ea2

git clone https://github.com/vanmanhpro/minichain.git

export CHAIN_ENDPOINT=http://ec2-54-169-169-0.ap-southeast-1.compute.amazonaws.com:8080
export MINER_ENDPOINT=http://ec2-54-169-169-0.ap-southeast-1.compute.amazonaws.com:9090

# get chain
curl http://ec2-54-169-169-0.ap-southeast-1.compute.amazonaws.com:8080/chain

# init miner
cp development/mempool_database_init.json miner/mempool_database.json
export CHAIN_ENDPOINT=http://127.0.0.1:8080
export MINER_ENDPOINT=http://127.0.0.1:9090
export MINER_WALLET_ADDRESS=21e8bca257607c7cff2ea0d41af2653ca0e8533732d8b6f980c1e2eca4bcf40dfe0da775969f9335ee64eedf72ae0ea2