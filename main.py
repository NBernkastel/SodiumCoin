import json

import requests
from fastapi import FastAPI, HTTPException
from blockchain import Blockchain
from pydantic import BaseModel

from config import NODES, PUBLIC_KEY, SECRET_KEY

app = FastAPI()

blockchain = Blockchain(True)


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
    blockchain.resolve_conflicts()
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    blockchain.new_transaction(
        sender='0',
        recipient=PUBLIC_KEY,
        amount=1,
        key=SECRET_KEY
    )
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    for node in NODES:
        requests.post(node + '/block/get', json=block)
    with open('blockchain.blk', 'a') as file:
        file.write('\n')
        json.dump(block, file, sort_keys=True)
    return block


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
    if blockchain.validate_transaction(trn):
        blockchain.current_transactions.append(trn)
        return 200
    return HTTPException(422)


@app.get("/transactions/existings")
async def get_transaction():
    return blockchain.current_transactions


@app.post("/block/get")
async def get_block(block: Block):
    blockchain.resolve_conflicts()
    if blockchain.validate_block(block, blockchain.last_block):
        blockchain.chain.append(block)
        return 200
    return HTTPException(422)


@app.get('/nodes/resolve')
async def consensus():
    replaced = blockchain.resolve_conflicts()

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
    return blockchain.check_balance(PUBLIC_KEY)
