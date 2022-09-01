import os
from dotenv import load_dotenv
from web3 import Web3


def main():
    load_dotenv()
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')
    w3 = init_connection()

def init_connection():
    provider_url = "https://mainnet.infura.io/v3/fdb6794f94ae4b26b24a223b75c1f628"
    w3 = Web3(Web3.HTTPProvider(provider_url))
    print(f"connection active? ", w3.isConnected())
    return w3



if __name__ == '__main__':
    main()