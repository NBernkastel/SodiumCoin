import requests
from config import NODES
from api import blockchain
from keygen import generate_ecdsa_keys
from utils import console_clear, get_logo
from validator import Validator


def wallet():
    response = None
    blockchain.consensus()
    if not Validator.validate_chain(blockchain.chain, blockchain.reward, blockchain.emission_address,
                                    blockchain.one_unit, blockchain.difficult, blockchain.wallets):
        raise Exception('No valid chain')
    while response not in ['1', '2', '3']:
        response = input("""What do you want to do?
            1. Generate new wallet
            2. Send coins to another wallet 
            3. Check balance
            4. Main blocks
            5. Quit
            """)
        if response == '1':
            console_clear()
            print("""=========================================\n
            IMPORTANT: save this credentials or you won't be able to recover your wallet\n
            =========================================\n""")
            generate_ecdsa_keys()
        elif response == '2':
            console_clear()
            addr_from = input("From: introduce your wallet address (public key)\n")
            private_key = input("Introduce your private key\n")
            addr_to = input("To: introduce destination wallet address\n")
            amount = input("Amount: number stating how much do you want to send\n")
            fee = input("Fee: reward to miners for adding your transaction\n")
            print("=========================================\n\n")
            print("Is everything correct?\n")
            print(F"From: {addr_from}\nPrivate Key: {private_key}\nTo: {addr_to}\nAmount: {amount}\n")
            response = input("y/n\n")
            if response.lower() == 'y':
                blockchain.consensus()
                transaction = (blockchain.new_transaction
                               (addr_from,
                                addr_to,
                                amount,
                                fee,
                                private_key)
                               )
                for node in NODES:
                    requests.post(node + '/transactions/get', json=transaction)
            elif response.lower() == 'n':
                continue
        elif response == '3':
            console_clear()
            addr_from = input("Introduce your wallet address (public key)\n")
            print(blockchain.check_balance(addr_from))
        elif response == '4':
            console_clear()
            while True:
                blockchain.mine()
        else:
            return
    print('')


if __name__ == '__main__':
    console_clear()
    print(f"""===================================================================\n
{get_logo()}                              
\n
===================================================================\n\n
        Make sure you are using the latest version or you may end in
        a parallel chain.\n\n\n""")
    wallet()
    input("Press ENTER to exit...")
