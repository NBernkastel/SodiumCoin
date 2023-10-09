import hashlib
import json
from time import time
import requests

from keygen import sign_ECDSA_msg, validate_signature
from config import NODES


class Blockchain(object):
    def __init__(self, chain=None):
        self.difficult = 4
        self.current_transactions = []
        self.wallets = {}
        if chain:
            with open('blockchain.blk', 'r') as file:
                self.chain = []
                for line in file:
                    self.chain.append(json.loads(line))
        else:
            self.chain = []
            self.new_block(previous_hash=1, proof=100)
            with open('blockchain.blk', 'w') as file:
                json.dump(self.chain[0], file)

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

    def new_transaction(self, sender: str, recipient: str, amount: int, key: str) -> dict:
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        }
        transaction_hash = self.hash(transaction)
        signature = sign_ECDSA_msg(key, transaction_hash)
        transaction["signature"] = signature.decode()
        self.current_transactions.append(transaction)
        print(transaction_hash)
        return transaction

    @staticmethod
    def hash(block):
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
        return guess_hash[:4] == '0' * self.difficult

    def valid_chain(self, chain: list) -> bool:
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
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
            last_block = block
            current_index += 1
        self.wallets = {}
        return True

    def validate_transaction(self, transaction):
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

    def check_balance(self, public_key):
        balance = 0
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['recipient'] == public_key:
                    balance += transaction['amount']
                if transaction['sender'] == public_key:
                    balance -= transaction['amount']
        return balance

    def resolve_conflicts(self) -> bool:
        neighbours = NODES
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            response = requests.get(f'{node}/chain')

            if response.status_code == 200:
                chain = response.json()
                if len(chain) > max_length and self.valid_chain(chain):
                    max_length = len(chain)
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True

        return False
