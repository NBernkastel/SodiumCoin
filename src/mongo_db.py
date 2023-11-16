import pymongo


class Mongo:
    def __init__(self):
        self.BLOCKCHAIN = 'blockchain'
        self.FIRST_BLOCK = {
            'index': 1,
            'timestamp': 1696793687.5292575,
            'transactions': [],
            'proof': 100,
            'previous_hash': 1,
            'difficult': 6,
            'reward': 50
        }
        client = pymongo.MongoClient()
        database_names = client.list_database_names()
        if self.BLOCKCHAIN not in database_names:
            self.db = client[self.BLOCKCHAIN]
            self.block_collection = self.db.create_collection('blocks')
            self.state_collection = self.db.create_collection('states')
            self.block_collection.insert_one(self.FIRST_BLOCK)
        else:
            self.db = client[self.BLOCKCHAIN]
            self.block_collection = self.db.get_collection('blocks')
            self.state_collection = self.db.get_collection('states')
