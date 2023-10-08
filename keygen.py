import base64
import time

import ecdsa


def generate_ECDSA_keys():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    private_key = sk.to_string().hex()
    vk = sk.get_verifying_key()
    public_key = vk.to_string().hex()
    public_key = base64.b64encode(bytes.fromhex(public_key))
    filename = input("Write the name of your new address: ") + ".txt"
    with open(filename, "w") as f:
        f.write(F"Private key: {private_key}\nWallet address / Public key: {public_key.decode()}")
    print(F"Your new address and private key are now in the file {filename}")


def sign_ECDSA_msg(private_key):
    message = str(round(time.time()))
    bmessage = message.encode()
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = base64.b64encode(sk.sign(bmessage))
    return signature, message
