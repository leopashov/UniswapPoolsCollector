from sys import implementation
from web3 import Web3
import os
from dotenv import load_dotenv
import requests

def main():
    load_dotenv()
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')
    UNI_FACTORY_V2 = os.getenv('UNI_FACTORY_V2')
    UNI_FACTORY_V3 = os.getenv('UNI_FACTORY_V3')
    w3 = init_connection()
    print(normalise_decimals('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 14567480000000000000000, w3, ETHERSCAN_TOKEN))

def normalise_decimals(token_address, value, w3, etherscanToken):
    implementationContract = getImplementationContract(token_address, w3)
    if int(implementationContract, 16) != 0:
        ABI = getABI(implementationContract, etherscanToken)
        address = implementationContract
    else:
        ABI = getABI(token_address, etherscanToken)
        address = token_address
    decimals = getDecimals(address, ABI, w3)
    value = value * pow(10,-decimals)
    value = float("{:.3f}".format(value))
    return value

def getDecimals(address, ABI, w3):
    contract_instance = w3.eth.contract(address = address, abi = ABI)
    decimals = contract_instance.functions.decimals.__call__().call()
    return decimals

def getABI(address, etherscanToken):
    URL = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={etherscanToken}"
    r = requests.get(URL)
    if r.status_code == 200:
        return r.json()["result"]
    else:
        print(f"API request status fault, response: ", r.json())


def getImplementationContract(proxyAddress, w3):
    """reads proxy contract with address 'proxyAddress's storage at specific slot as defined in EIP 1967
    to obtain the implementation contract address."""
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