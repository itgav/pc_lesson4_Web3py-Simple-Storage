# Terminal output shows "INFO: Could not find files for the given pattern(s)" -> Googled and it's fine, no issues
# ^^^ all the outputs show correctly was just curious why that message appears

import json
import os
from solcx import compile_standard, install_solc  # need a compiler
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()  # loads .env file and its environment variables

# import solcx # if want to show installed or installable solc versions

# open SimpleStorage file and read ('r'), save in a variable, then close file
with open("./SimpleStorage.sol", "r") as file:
    simple_storage_file = file.read()
    # print(simple_storage_file)

# install solidity version that we will compile
install_solc("0.8.17")
# print(solcx.get_installable_solc_versions()) # what versions can be installed with solcx
# print(solcx.get_installed_solc_versions()) # what versions have been installed with solcx

# compile our solidity
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            # outputSelection: {file: {contract: [outputs]}} -> we selected all files and all contracts with '*'
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.8.17",
)

# print(compiled_sol)

# put compiled_sol into json format in 'file'
# creates new file in folder called 'compiled_sol.json'
with open("compiled_sol.json", "w") as file:  # 'w' = write
    json.dump(compiled_sol, file)

# When deploy contract need the bytecode and ABI

# get bytecode
# just indexing compiled_sol to get to the bytecode portion
bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"][
    "bytecode"
]["object"]

# get abi
abi = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["abi"]

# connect to ganache --> can see the info at the top of the ganache client
w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:8545"))
chain_id = 1337
my_address = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"  # grabbed address from one of adrs in ganache

# Infura
# api_key = ""
# w3 = Web3(
#     Web3.HTTPProvider(f"https://goerli.infura.io/v3/{api_key}")
# )
# chain_id = 5  # Goerli chain ID
# my_address =   # from metamask test wallet

# defined in '.env' file
private_key = os.getenv("PRIVATE_KEY")

# create contract object
SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)
# get the latest nonce
nonce = w3.eth.getTransactionCount(my_address)

# 1) build the transaction
# 2) sign the transaction
# 3) send the transaction
transaction = SimpleStorage.constructor().buildTransaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,  # newly required
        "from": my_address,
        "nonce": nonce,
    }  # required parameters
)

signed_tx = w3.eth.account.sign_transaction(transaction, private_key=private_key)
# send signed transaction --> will see transaction populate in Ganache
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
# wait for transaction to be completed before continuing
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# initialize contract (we just signed) and its ABI
simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

# can interact w/ smart contract by a 'call' or 'transact'
# call = no state change; transact = state change
# any 'transact' function can also be called, but not vice versa
print(simple_storage.functions.retrieve().call())
# print(simple_storage.functions.retrieve())

# set value of 'favorite number'
# 1) build transaction
store_transaction = simple_storage.functions.store(15).buildTransaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        # can't use same nonce, must increase by 1 with every transaction
        "nonce": nonce + 1,
    }
)
# 2) sign transaction
signed_store_tx = w3.eth.account.sign_transaction(
    store_transaction, private_key=private_key
)
# 3) send transaction
send_store_tx = w3.eth.send_raw_transaction(signed_store_tx.rawTransaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(send_store_tx)

# now will print out 15 (our value inputted)
print(simple_storage.functions.retrieve().call())
