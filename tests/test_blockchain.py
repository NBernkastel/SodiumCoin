import pytest

from src.blockchain import Blockchain

blockchain = Blockchain()

@pytest.mark.parametrize("last_proof, proof, res", [
    (100, 888273, True),
    (100, 1, False)
])
def test_valid_proof(last_proof, proof, res):
    assert blockchain.valid_proof(last_proof, proof) == res


def test_proof():
    assert blockchain.proof_of_work(100) == 888273



if __name__ == '__main__':
    pytest.main()