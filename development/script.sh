curl -X POST -H "Content-Type: application/json" -d @sample_add.json localhost:9090/transaction
curl -X POST -H "Content-Type: application/json" -d @new_block_sample.json localhost:9090/newblock
curl -X GET -H "Content-Type: application/json" localhost:9090/checkmining
curl localhost:8080/wallet/839c4e6d6a76ec4a2af86beec09516ef285583c25c7500b69fd38a58daf773d3584c50bab3868f2ed78593753d8588f0
curl localhost:8080/bounty