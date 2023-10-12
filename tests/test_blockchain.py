from src.blockchain import Blockchain

blockchain = Blockchain()


def test_proof():
    blockchain.proof_of_work(100)
    assert True
