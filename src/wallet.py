
from src.api import blockchain
from src.keygen import generate_ecdsa_keys
from src.utils import console_clear, get_logo


def wallet():
    response = None
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
            print("=========================================\n\n")
            print("Is everything correct?\n")
            print(F"From: {addr_from}\nPrivate Key: {private_key}\nTo: {addr_to}\nAmount: {amount}\n")
            response = input("y/n\n")
            if response.lower() == 'y':
                pass
            elif response.lower() == 'n':
                response = None
        elif response == '3':
            console_clear()
            pass
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
