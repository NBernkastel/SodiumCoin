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


@app.get('chain/height')
async def get_chain_height():
    return blockchain.last_block['index']


@app.get('/block/send')
async def get_part_of_chain(start: int, length: int):
    if length > 10 or start >= blockchain.last_block['index']:
        return False
    res = list(blockchain.db.block_collection.find({'index': {'$gt': start, '$lt': start + length}}))
    for r in res:
        del r['_id']
    return res


@app.post("/transactions/get")
async def get_transaction(trn: TransactionGet):
    if blockchain.validate_transaction(dict(trn)):
        if trn.hash not in blockchain.current_transactions_hashes:
            blockchain.current_transactions.append(dict(trn))
            blockchain.current_transactions_hashes.add(trn.hash)
            return True
    return False


@app.get("/transactions/existing")
async def existing_transaction():
    return blockchain.current_transactions


@app.post("/block/get")
async def get_block(block: Block):
    if blockchain.validate_block(dict(block), blockchain.last_block):
        blockchain.db.block_collection.insert_one(dict(block))
        return True
    return False

