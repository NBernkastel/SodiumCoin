import hashlib
import json
from time import time
import requests
from blockchain_utils import elem_hash
from keygen import sign_ecdsa_msg, validate_signature
from config import PUBLIC_KEY, SECRET_KEY, NODES


class Blockchain(object):
    def __init__(self):
        self.difficult = 5
        self.reward = 1
        self.one_unit = 0.00000001
        self.emission_address = '0'
        self.current_transactions = []
        self.current_transactions_hashes = set()
        self.nodes = set()
        self.chain = []
        for node in NODES:
            self.nodes.add(node)
        try:
            with open('../blockhainstate', 'r') as block_state_file:
                self.wallets = json.load(block_state_file)
        except FileNotFoundError:
            self.wallets = {}
        try:
            with open('../blockchain', 'r') as file:
                for line in file:
                    self.chain.append(json.loads(line))
        except FileNotFoundError:
            # exit(0)
            # TODO rewrite this
            if not self.consensus():
                self.new_block(previous_hash=1, proof=100)
                with open('../blockchain', 'w') as file:
                    json.dump(self.chain[0], file)

    def mine(self):
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
            sender='0',
            recipient=PUBLIC_KEY,
            amount=1,
            fee=0,
            secret_key=SECRET_KEY
        )
        previous_hash = elem_hash(last_block)
        block = self.new_block(proof, previous_hash)
        for node in self.nodes:
            requests.post(node + '/block/get', json=block)
        with open('../blockchain', 'a') as file:
            file.write('\n')
            json.dump(block, file, sort_keys=True)
        return block

    def new_block(self, proof: int, previous_hash=None) -> dict:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or elem_hash(self.chain[-1]),
            'difficult': self.difficult,
            'reward': self.reward
        }
        self.current_transactions = []
        self.current_transactions_hashes = set()
        self.chain.append(block)
        return block

    def new_transaction(
            self, sender: str,
            recipient: str,
            amount: int,
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
        return self.chain[-1]

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
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            response = requests.get(f'{node}/chain')

            if response.status_code == 200:
                chain = response.json()
                if (len(chain) > max_length and self.validate_chain(chain)) or (
                        not self.validate_chain(self.chain) and self.validate_chain(chain)):
                    max_length = len(chain)
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            with open('../blockchain', 'w') as file:
                for block in self.chain:
                    json.dump(block, file, sort_keys=True)
                    file.write('\n')
            return True
        return False

    def validate_transaction(self, transaction: dict) -> bool:
        transaction_without_sign = dict(transaction)
        transaction_without_sign.pop('sign')
        if transaction['sender'] == self.emission_address:
            if transaction['amount'] > self.reward:
                return False
            if not validate_signature(public_key=transaction['recipient'],
                                      signature=transaction['sign'],
                                      message=transaction['hash']
                                      ):
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
            if not validate_signature(public_key=transaction['sender'],
                                      signature=transaction['sign'],
                                      message=transaction['hash']
                                      ):
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
            return True
        return False

    def validate_chain(self, chain: list[dict]) -> bool:
        self.wallets.clear()
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if not self.validate_block(block, last_block):
                return False
            last_block = block
            current_index += 1
        return True
