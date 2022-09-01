import os
from dotenv import load_dotenv
from web3 import Web3
import requests



def main():
    load_dotenv()
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')
    UNI_FACTORY_V2 = os.getenv('UNI_FACTORY_V2')
    w3 = init_connection()
    token0 = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    token1 = '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984'
    print(ETHERSCAN_TOKEN)
    getAllPoolInfo(token0, token1, w3, UNI_FACTORY_V2, ETHERSCAN_TOKEN)



def getAllPoolInfo(token0, token1, w3, UNI_FACTORY_V2, ETHERSCAN_TOKEN):
    V2PairAddress = getV2PairAddress(token0, token1, w3, UNI_FACTORY_V2, ETHERSCAN_TOKEN)
    print(f"V2 pair address: ", V2PairAddress)
    getPoolData(V2PairAddress, w3, ETHERSCAN_TOKEN)



def getPoolData(poolAddress, w3, ETHERSCAN_TOKEN):
    # get ABI
    poolABI = getABI(poolAddress, ETHERSCAN_TOKEN)
    poolInstance = w3.eth.contract(address = poolAddress, abi = poolABI)
    # call pool instance to get data
    TOKEN0 = poolInstance.functions.token0.__call__().call()
    TOKEN1 = poolInstance.functions.token1.__call__().call()
    PRICE0 = poolInstance.functions.price0CumulativeLast.__call__().call()
    PRICE1 = poolInstance.functions.price1CumulativeLast.__call__().call()
    RESERVES = poolInstance.functions.getReserves.__call__().call()
    RESERVE0 = RESERVES[0]
    RESERVE1 = RESERVES[1]
    print(RESERVES)

def getV2PairAddress(token0, token1, w3, UNI_FACTORY_V2, ETHERSCAN_TOKEN):
    # get contract ABI from etherscan API using V2 address
    V2_ABI = getABI(UNI_FACTORY_V2, ETHERSCAN_TOKEN)
    # use address and ABi to get contract instance
    contract_instance = w3.eth.contract(address = UNI_FACTORY_V2, abi = V2_ABI)
    # get pool address
    poolAddress = contract_instance.functions.getPair(token0, token1).call()
    return poolAddress


def getABI(address, etherscanToken):
    URL = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={etherscanToken}"
    r = requests.get(URL)
    if r.status_code == 200:
        return r.json()["result"]
    else:
        print(f"API request status fault, response: ", r.json())

def init_connection():
    provider_url = "https://mainnet.infura.io/v3/d758f6f480b64b8daf47412f0969392b"
    w3 = Web3(Web3.HTTPProvider(provider_url))
    print(f"connection active? ", w3.isConnected())
    return w3

if __name__ == '__main__':
    main()