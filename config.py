import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY')
PUBLIC_KEY = os.environ.get('PUBLIC_KEY')
NODES = os.environ.get('NODES')
NODES = NODES.split(',')


if __name__ == '__main__':
    print(SECRET_KEY, type(SECRET_KEY))
    print(PUBLIC_KEY, type(PUBLIC_KEY))
    print(NODES, type(NODES))
