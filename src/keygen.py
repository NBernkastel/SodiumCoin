import base64
import ecdsa
from ecdsa import BadSignatureError


def generate_ecdsa_keys():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    private_key = sk.to_string().hex()
    vk = sk.get_verifying_key()
    public_key = vk.to_string().hex()
    public_key = base64.b64encode(bytes.fromhex(public_key))
    filename = input("Write the name of your new address: ") + ".txt"
    with open(filename, "w") as f:
        f.write(
            F"Private key: {private_key}\n"
            F"Wallet address / Public key: {public_key.decode()}")
    print(F"Your new address and private key are now in the file {filename}")


def sign_ecdsa_msg(private_key: str, message: str) -> str:
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = base64.b64encode(sk.sign(message.encode()))
    return signature.decode()


def validate_signature(public_key: str, signature: str, message: str) -> bool:
    public_key = (base64.b64decode(public_key)).hex()
    signature = base64.b64decode(signature)
    vk = ecdsa.VerifyingKey.from_string(
        bytes.fromhex(public_key),
        curve=ecdsa.SECP256k1
    )
    try:
        return vk.verify(signature, message.encode())
    except BadSignatureError:
        return False


if __name__ == '__main__':
    result = None
    while result not in [1, 2, 3]:
        result = int(input('1: generate_ecdsa_keys,'
                           ' 2: sign_ecdsa_msg,'
                           ' 3: validate_signature\n'))
        match result:
            case 1:
                generate_ecdsa_keys()
            case 2:
                private_key = input('Input private key\n')
                message = input('Input message\n')
                print(sign_ecdsa_msg(private_key, message))
            case 3:
                public_key = input('Input public key\n')
                signature = input('Input signature\n')
                message = input('Input message\n')
                validate_signature(public_key, signature, message)
