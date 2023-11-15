import hashlib
from time import time
import pymongo
import requests
from blockchain_utils import elem_hash
from keygen import sign_ecdsa_msg, validate_signature
from config import PUBLIC_KEY, SECRET_KEY, NODES
from mongo_db import Mongo


class Blockchain:
    def __init__(self):
        self.difficult = 8
        self.reward = 50
        self.one_unit = 0.00000001
        self.emission_address = '0'
        self.current_transactions = []
        self.current_transactions_hashes = set()
        self.nodes = set()
        self.wallets = {}
        self.db = Mongo()
        for node in NODES:
            self.nodes.add(node)

    def mine(self):
        self.validate_chain()
        self.consensus()
        for node in NODES:
            response = requests.get(node + '/transactions/existing')
            if response.status_code == 200:
                transactions = response.json()
                for transaction in transactions:
                    if transaction['hash'] not in self.current_transactions_hashes:
                        if self.validate_transaction(transaction):
                            self.current_transactions.append(transaction)
                            self.current_transactions_hashes.add(transaction['hash'])
        last_block = self.last_block
        last_proof = last_block['proof']
        proof = self.proof_of_work(last_proof)
        self.new_transaction(
            sender=self.emission_address,
            recipient=PUBLIC_KEY,
            amount=self.reward,
            fee=0,
            secret_key=SECRET_KEY
        )
        previous_hash = elem_hash(last_block)
        block = self.new_block(proof, previous_hash)
        for node in self.nodes:
            requests.post(node + '/block/get', json=block)
        return block

    def new_block(self, proof: int, previous_hash=None) -> dict:
        last_block = self.last_block
        block = {
            'index': last_block['index'] + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or elem_hash(last_block),
            'difficult': self.difficult,
            'reward': self.reward
        }
        self.current_transactions = []
        self.current_transactions_hashes = set()
        self.db.block_collection.insert_one(block)
        del block['_id']
        return block

    def new_transaction(
            self, sender: str,
            recipient: str,
            amount: float,
            fee: float,
            secret_key: str) -> dict:
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time(),
            'fee': fee
        }
        transaction['hash'] = elem_hash(transaction)
        transaction["sign"] = sign_ecdsa_msg(secret_key, transaction['hash'])
        if self.validate_transaction(transaction):
            self.current_transactions.append(transaction)
            self.current_transactions_hashes.add(transaction['hash'])
        return transaction

    @property
    def last_block(self):
        block = self.db.block_collection.find_one(sort=[('index', pymongo.DESCENDING)])
        del block['_id']
        return block

    def block_by_index(self, index):
        block = self.db.block_collection.find_one({'index': index})
        del block['_id']
        return block

    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while self.validate_proof(last_proof, proof) is False:
            proof += 1
        return proof

    def check_balance(self, public_key: str) -> float:
        try:
            return self.wallets[public_key]
        except KeyError:
            return 0

    def consensus(self) -> bool:
        """Return True if chain was replaced"""
        height = self.last_block['index']
        max_height = height
        nodes_heights = {}
        for node in self.nodes:
            response = requests.get(node + '/chain/height')
            if response.status_code == 200 and response.json() > height:
                nodes_heights[node] = response.json()
                max_height = response.json()
        if len(nodes_heights) == 0:
            return False
        max_node = max(nodes_heights, key=nodes_heights.get)
        nums_of_req = 1
        additional_chain = []
        req_start = height
        if max_height - height > 10:
            nums_of_req = ((max_height - height) // 10) + 1
        for i in range(nums_of_req):
            resp = requests.get(max_node + f'/get_blocks?start={req_start}&length={11}')
            if resp.status_code == 200:
                additional_chain.extend(resp.json())
                req_start += 10
            else:
                return False
        if self.validate_chain(additional_chain):
            self.db.block_collection.insert_many(additional_chain)
            return True
        return False

    def validate_transaction(self, transaction: dict) -> bool:
        transaction_without_sign = dict(transaction)
        transaction_without_sign.pop('sign')
        if transaction['sender'] == self.emission_address:
            if transaction['amount'] > self.reward:
                return False
            if not validate_signature(public_key=transaction['recipient'], signature=transaction['sign'],
                                      message=transaction['hash']):
                return False
            if transaction['recipient'] not in self.wallets:
                self.wallets[transaction['recipient']] = self.reward
            else:
                self.wallets[transaction['recipient']] += self.reward
            return True
        else:
            if transaction['sender'] not in self.wallets or transaction['fee'] < self.one_unit:
                return False
            if self.wallets[transaction['sender']] < transaction['amount'] + transaction['fee']:
                return False
            if not validate_signature(public_key=transaction['sender'], signature=transaction['sign'],
                                      message=transaction['hash']):
                return False
            self.wallets[transaction['sender']] -= transaction['amount'] + transaction['fee']
            if transaction['recipient'] not in self.wallets:
                self.wallets[transaction['recipient']] = transaction['amount']
            else:
                self.wallets[transaction['recipient']] += transaction['amount']
            return True

    def validate_transactions(self, transactions: list[dict]) -> bool:
        emission_transaction = 0
        transactions_hashes = []
        for transaction in transactions:
            if emission_transaction > 1:
                return False
            if transaction['sender'] == self.emission_address:
                emission_transaction += 1
            if transaction['hash'] in transactions_hashes:
                return False
            if not self.validate_transaction(transaction):
                return False
            transactions_hashes.append(transaction['hash'])
        return True

    def validate_block(self, block: dict, previous_block: dict) -> bool:
        if block['previous_hash'] != elem_hash(previous_block):
            return False
        if not self.validate_proof(previous_block['proof'], block['proof']):
            return False
        if (block['index'] - 1) != previous_block['index']:
            return False
        if block['reward'] != self.reward or block['difficult'] != self.difficult:
            return False
        sum_of_fee = 0
        for trn in block['transactions']:
            sum_of_fee += trn['fee']
        if not self.validate_transactions(block['transactions']):
            return False
        return True

    def validate_proof(self, last_proof: int, proof: int) -> bool:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        if guess_hash[:self.difficult] == '0' * self.difficult:
            print(guess_hash)
            return True
        return False

    def validate_chain(self, chain: list[dict] = None) -> bool:
        if not chain:
            last_index = self.last_block['index']
            last_block = self.db.block_collection.find_one({'index': 1})
            del last_block['_id']
            current_index = 2
            while current_index <= last_index:
                block = self.db.block_collection.find_one({'index': current_index})
                if not block:
                    self.db.block_collection.delete_many({'index': {'$gt': 1}})
                    return False
                del block['_id']
                if not self.validate_block(block, last_block):
                    self.db.block_collection.delete_many({'index': {'$gt': block['index']}})
                    return block['index']
                last_block = block
                current_index += 1
            return True
        else:
            last_block = chain[0]
            current_index = 1
            while current_index < len(chain):
                block = chain[1]
                if not self.validate_block(block, last_block):
                    return block['index']
                last_block = block
                current_index += 1
            return True
