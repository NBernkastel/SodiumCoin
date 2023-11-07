import json

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from blockchain import Blockchain
from config import NODES, PUBLIC_KEY, SECRET_KEY
from validator import Validator

app = FastAPI()

blockchain = Blockchain()


class Transaction(BaseModel):
    sender: str
    recipient: str
    amount: float
    fee: float


class TransactionGet(Transaction):
    timestamp: float
    hash: str
    sign: str


class Block(BaseModel):
    index: int
    timestamp: float
    transactions: list
    proof: int
    previous_hash: str
    difficult: int
    reward: float


@app.get("/block/mine")
async def mine():
    return blockchain.mine()


@app.post("/transactions/new")
async def new_transaction(trn: Transaction):
    blockchain.consensus()
    transaction = (blockchain.new_transaction
                   (trn.sender,
                    trn.recipient,
                    trn.amount,
                    trn.fee,
                    SECRET_KEY)
                   )
    for node in NODES:
        requests.post(node + '/transactions/get', json=transaction)
    return transaction


@app.get('/chain')
async def full_chain():
    return blockchain.chain


@app.post("/transactions/get")
async def get_transaction(trn: TransactionGet):
    if Validator.validate_transaction(blockchain.wallets, dict(trn), blockchain.reward, blockchain.emission_address,
                                      blockchain.one_unit):
        if trn.hash not in blockchain.current_transactions_hashs:
            blockchain.current_transactions.append(dict(trn))
            blockchain.current_transactions_hashs.add(trn.hash)
            return 200
    return HTTPException(422)


@app.get("/transactions/existing")
async def existing_transaction():
    return blockchain.current_transactions


@app.post("/block/get")
async def get_block(block: Block):
    if Validator.validate_block(dict(block), blockchain.last_block, blockchain.wallets, blockchain.reward,
                                blockchain.emission_address, blockchain.one_unit, blockchain.difficult):
        blockchain.chain.append(dict(block))
        with open('../blockchain', 'a') as file:
            file.write('\n')
            json.dump(dict(block), file, sort_keys=True)
            return True
    return HTTPException(422)


@app.get('/nodes/consensus')
async def consensus():
    replaced = blockchain.consensus()

    if replaced:
        return {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    return {
        'message': 'Our chain is authoritative',
        'chain': blockchain.chain
    }


@app.get('/chain/validate')
async def chain_validate():
    return Validator.validate_chain(blockchain.chain, blockchain.reward, blockchain.emission_address,
                                    blockchain.one_unit, blockchain.difficult, blockchain.wallets)


@app.get('/balance')
async def balance():
    blockchain.consensus()
    return blockchain.check_balance(PUBLIC_KEY)
