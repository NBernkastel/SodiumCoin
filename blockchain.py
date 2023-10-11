import hashlib
import json
from time import time
import requests

from keygen import sign_ecdsa_msg, validate_signature
from config import NODES, PUBLIC_KEY, SECRET_KEY


class Blockchain(object):
    obj = None

    def __init__(self):
        self.difficult = 5
        self.current_transactions = []
        self.wallets = {}
        try:
            with open('blockchain.blk', 'r') as file:
                self.chain = []
                for line in file:
                    self.chain.append(json.loads(line))
        except FileNotFoundError:
            if not self.consensus():
                self.chain = []
                self.new_block(previous_hash=1, proof=100)
                with open('blockchain.blk', 'w') as file:
                    json.dump(self.chain[0], file)

    def __call__(cls, *args, **kwargs):
        if not cls.obj:
            super().__call__(*args, **kwargs)
        else:
            raise TypeError('Object already exist')

    def mine(self):
        self.consensus()
        last_block = self.last_block
        last_proof = last_block['proof']
        proof = self.proof_of_work(last_proof)
        self.new_transaction(
            sender='0',
            recipient=PUBLIC_KEY,
            amount=1,
            secret_key=SECRET_KEY
        )
        previous_hash = self.hash(last_block)
        block = self.new_block(proof, previous_hash)
        for node in NODES:
            requests.post(node + '/block/get', json=block)
        with open('blockchain.blk', 'a') as file:
            file.write('\n')
            json.dump(block, file, sort_keys=True)
        return block

    def new_block(self, proof: int, previous_hash=None) -> dict:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: int, secret_key: str) -> dict:
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        }
        transaction_hash = self.hash(transaction)
        transaction["signature"] = sign_ecdsa_msg(secret_key, transaction_hash)
        self.current_transactions.append(transaction)
        return transaction

    @staticmethod
    def hash(block: dict) -> str:
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    def valid_proof(self, last_proof: int, proof: int) -> bool:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        if guess_hash[:self.difficult] == '0' * self.difficult:
            print(guess_hash)
            return True
        return False

    def validate_chain(self, chain: list) -> bool:
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if not self.validate_block(block, last_block):
                return False
            last_block = block
            current_index += 1
        self.wallets = {}
        return True

    def validate_block(self, block: dict, last_block: dict) -> bool:
        if block['previous_hash'] != self.hash(last_block):
            return False
        if not self.valid_proof(last_block['proof'], block['proof']):
            return False
        for transaction in block['transactions']:
            if not self.validate_transaction(transaction):
                return False
            if transaction['sender'] == '0':
                if transaction['recipient'] in self.wallets:
                    self.wallets[transaction['recipient']] += 1
                else:
                    self.wallets[transaction['recipient']] = 1
                continue
            elif transaction['sender'] in self.wallets:
                if self.wallets[transaction['sender']] - transaction['amount'] < 0:
                    return False
                else:
                    self.wallets[transaction['sender']] -= transaction['amount']
                    if transaction['recipient'] in self.wallets:
                        self.wallets[transaction['recipient']] += transaction['amount']
                    else:
                        self.wallets[transaction['recipient']] = transaction['amount']
        return True

    def validate_transaction(self, transaction: dict) -> bool:
        transaction_without_sign = dict(transaction)
        transaction_without_sign.pop('signature')
        if not transaction['sender'] == '0':
            if validate_signature(transaction['sender'], transaction['signature'], self.hash(transaction_without_sign)):
                return True
        else:
            if validate_signature(transaction['recipient'], transaction['signature'],
                                  self.hash(transaction_without_sign)):
                if transaction['amount'] == 1:
                    return True
        if transaction['amount < 0.000001']:
            return False
        return False

    def check_balance(self, public_key: str) -> float:
        balance = 0
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['recipient'] == public_key:
                    balance += transaction['amount']
                if transaction['sender'] == public_key:
                    balance -= transaction['amount']
        return balance

    def consensus(self) -> bool:
        """Return True if chain was replaced"""
        neighbours = NODES
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            response = requests.get(f'{node}/chain')

            if response.status_code == 200:
                chain = response.json()
                if len(chain) > max_length and self.validate_chain(chain):
                    max_length = len(chain)
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False
