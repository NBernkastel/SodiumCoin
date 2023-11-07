import json
from time import time
import requests

from blockchain_utils import elem_hash
from keygen import sign_ecdsa_msg
from config import PUBLIC_KEY, SECRET_KEY, NODES
from validator import Validator


class Blockchain(object):
    obj = None

    def __init__(self):
        self.difficult = 5
        self.reward = 1
        self.one_unit = 0.00000001
        self.emission_address = '0'
        self.current_transactions = []
        self.current_transactions_hashs = set()
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


    def __new__(cls, *args, **kwargs):
        if not cls.obj:
            cls.obj = object.__new__(cls, *args, **kwargs)
        return cls.obj

    def mine(self):
        self.consensus()
        for node in NODES:
            response = requests.get(node + '/transactions/existing')
            if response.status_code == 200:
                transactions = response.json()
                for transaction in transactions:
                    if transaction['hash'] not in self.current_transactions_hashs:
                        if Validator.validate_transaction(self.wallets, transaction, self.reward, self.emission_address,
                                                          self.one_unit):
                            self.current_transactions.append(transaction)
                            self.current_transactions_hashs.add(transaction['hash'])
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
        self.current_transactions_hashs = set()
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
        if Validator.validate_transaction(self.wallets, transaction, self.reward,
                                          self.emission_address,
                                          self.one_unit):
            self.current_transactions.append(transaction)
            self.current_transactions_hashs.add(transaction['hash'])
        return transaction

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while Validator.validate_proof(last_proof, proof, self.difficult) is False:
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
                if (len(chain) > max_length and Validator.validate_chain(chain, self.reward, self.emission_address,
                                                                         self.one_unit, self.difficult,
                                                                         self.wallets)) or (
                        not Validator.validate_chain(self.chain, self.reward, self.emission_address,
                                                     self.one_unit, self.difficult,
                                                     self.wallets) and Validator.validate_chain(chain, self.reward,
                                                                                                self.emission_address,
                                                                                                self.one_unit,
                                                                                                self.difficult,
                                                                                                self.wallets)):
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
