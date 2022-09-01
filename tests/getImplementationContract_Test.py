import os
from web3 import Web3
from dotenv import load_dotenv

def main():
    load_dotenv()
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')
    UNI_FACTORY_V2 = os.getenv('UNI_FACTORY_V2')
    UNI_FACTORY_V3 = os.getenv('UNI_FACTORY_V3')
    w3 = init_connection()
    print(getImplementationContract('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', w3))

def getImplementationContract(proxyAddress, w3):
    """reads proxy contract with address 'proxyAddress's storage at specific slot as defined in EIP 1967
    to obtain the implementation contract address."""
    # DOESNT WORK FOR CONTRACTS USING OpenZeppelin's Unstructured Storage proxy pattern
    # have not found a solution for open zeppelin

    impl_contract = Web3.toHex(
        w3.eth.get_storage_at(
            proxyAddress,
            "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
        )
    )
    return impl_contract

def init_connection():
    provider_url = "https://mainnet.infura.io/v3/d758f6f480b64b8daf47412f0969392b"
    w3 = Web3(Web3.HTTPProvider(provider_url))
    print(f"connection active? ", w3.isConnected())
    return w3



if __name__ == '__main__':
    main()