import hashlib
import json

from blockchain_utils import elem_hash
from keygen import validate_signature


class Validator:
    @staticmethod
    def validate_transaction(wallets: dict, transaction: dict, reward: float, emission_address: str,
                             one_unit: float) -> bool:
        transaction_without_sign = dict(transaction)
        transaction_without_sign.pop('sign')
        if transaction['sender'] == emission_address:
            if transaction['amount'] > reward:
                return False
            if not validate_signature(public_key=transaction['recipient'],
                                      signature=transaction['sign'],
                                      message=transaction['hash']
                                      ):
                return False
            if transaction['recipient'] not in wallets:
                wallets[transaction['recipient']] = reward
            else:
                wallets[transaction['recipient']] += reward
            return True
        else:
            if transaction['sender'] not in wallets or transaction['fee'] < one_unit:
                return False
            if wallets[transaction['sender']] < transaction['amount'] + transaction['fee']:
                return False
            if not validate_signature(public_key=transaction['sender'],
                                      signature=transaction['sign'],
                                      message=transaction['hash']
                                      ):
                return False
            wallets[transaction['sender']] -= transaction['amount'] + transaction['fee']
            if transaction['recipient'] not in wallets:
                wallets[transaction['recipient']] = transaction['amount']
            else:
                wallets[transaction['recipient']] += transaction['amount']
            return True

    @staticmethod
    def validate_transactions(transactions: list[dict], wallets: dict, reward: float, emission_address: str,
                              one_unit: float) -> bool:
        emission_transaction = 0
        transactions_hashs = []
        for transaction in transactions:
            if emission_transaction > 1:
                return False
            if transaction['sender'] == emission_address:
                emission_transaction += 1
            if transaction['hash'] in transactions_hashs:
                return False
            if not Validator.validate_transaction(wallets, transaction, reward, emission_address, one_unit):
                return False
            transactions_hashs.append(transaction['hash'])
        return True

    @staticmethod
    def validate_block(block: dict, previous_block, wallets: dict, reward: float, emission_address: str,
                       one_unit: float, difficult: int) -> bool:
        if block['previous_hash'] != elem_hash(previous_block):
            return False
        if not Validator.validate_proof(previous_block['proof'], block['proof'], difficult):
            return False
        if (block['index'] - 1) != previous_block['index']:
            return False
        if block['reward'] != reward or block['difficult'] != difficult:
            return False
        sum_of_fee = 0
        for trn in block['transactions']:
            sum_of_fee += trn['fee']
        if not Validator.validate_transactions(block['transactions'], wallets, reward + sum_of_fee, emission_address,
                                               one_unit):
            return False
        return True

    @staticmethod
    def validate_proof(last_proof: int, proof: int, difficult: int) -> bool:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        if guess_hash[:difficult] == '0' * difficult:
            return True
        return False

    @staticmethod
    def validate_chain(chain: list[dict], reward: float, emission_address: str, one_unit: float,
                       difficult: int, wallets: dict) -> bool:
        wallets.clear()
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if not Validator.validate_block(block, last_block, wallets, reward, emission_address, one_unit,
                                            difficult):
                return False
            last_block = block
            current_index += 1
        return True
