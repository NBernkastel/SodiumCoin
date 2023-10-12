import json

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from blockchain import Blockchain
from config import NODES, PUBLIC_KEY, SECRET_KEY

app = FastAPI()

blockchain = Blockchain()


class Transaction(BaseModel):
    sender: str
    recipient: str
    amount: int


class TransactionGet(Transaction):
    signature: str


class Block(BaseModel):
    index: int
    timestamp: float
    transactions: list
    proof: int
    previous_hash: str


@app.get("/block/mine")
async def mine():
    return blockchain.mine()


@app.post("/transactions/new")
async def new_transaction(trn: Transaction):
    transaction = blockchain.new_transaction(trn.sender, trn.recipient, trn.amount, SECRET_KEY)
    for node in NODES:
        requests.post(node + '/transactions/get', json=transaction)
    return transaction


@app.get('/chain')
async def full_chain():
    return blockchain.chain


@app.post("/transactions/get")
async def get_transaction(trn: TransactionGet):
    transaction = dict(trn)
    if blockchain.validate_transaction(transaction):
        blockchain.current_transactions.append(transaction)
        return 200
    return HTTPException(422)


@app.get("/transactions/existings")
async def get_transaction():
    return blockchain.current_transactions


@app.post("/block/get")
async def get_block(block: Block):
    if blockchain.validate_block(dict(block), blockchain.last_block):
        blockchain.chain.append(dict(block))
        return 200
    with open('blockchain.blk', 'a') as file:
        file.write('\n')
        json.dump(dict(block), file, sort_keys=True)
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
    return blockchain.validate_chain(blockchain.chain)


@app.get('/balance')
async def balance():
    blockchain.consensus()
    return blockchain.check_balance(PUBLIC_KEY)


@app.get('/nodes/get')
async def get_nodes():
    return blockchain.get_nodes()
