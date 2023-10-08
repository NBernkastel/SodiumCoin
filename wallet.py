from keygen import generate_ECDSA_keys

def wallet():
    response = None
    while response not in ['1', '2', '3']:
        response = input("""What do you want to do?
            1. Generate new wallet
            2. Send coins to another wallet 
            3. Check balance
            4. Quit
            """)
        if response == '1':
            print("""=========================================\n
            IMPORTANT: save this credentials or you won't be able to recover your wallet\n
            =========================================\n""")
            generate_ECDSA_keys()
        elif response == '2':
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
                pass
        elif response == '3':
            pass
        else:
            quit()
    print('')


if __name__ == '__main__':
    print("""       =========================================\n
        SIMPLE COIN v1.0.0 - BLOCKCHAIN SYSTEM\n
       =========================================\n\n
        Make sure you are using the latest version or you may end in
        a parallel chain.\n\n\n""")
    wallet()
    input("Press ENTER to exit...")