import os
from sys import implementation
from dotenv import load_dotenv
from web3 import Web3, exceptions
import requests
import pandas as pd
import numpy as np
import sqlite3
from pycoingecko import CoinGeckoAPI


def main():
    load_dotenv()
    verabi: '0x8f8EF111B67C04Eb1641f5ff19EE54Cda062f163'
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')
    UNI_FACTORY_V2 = os.getenv('UNI_FACTORY_V2')
    UNI_FACTORY_V3 = os.getenv('UNI_FACTORY_V3')
    w3 = init_connection()
    v3poolexample = '0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640'
    getV3PoolData(v3poolexample, w3, ETHERSCAN_TOKEN)

def getV3PoolData(V3Pool, w3, ETHERSCAN_TOKEN):
    poolABI = getABI('0x8f8EF111B67C04Eb1641f5ff19EE54Cda062f163', ETHERSCAN_TOKEN)
    print(f"pool address: ", V3Pool)
    # print(f"Pool ABI: ", poolABI)
    poolInstance = w3.eth.contract(address = V3Pool, abi = poolABI)
    TOKEN = (poolInstance.functions.token0.__call__().call(), poolInstance.functions.token1.__call__().call())
    print(TOKEN)
    RESERVE = getReserve(TOKEN, V3Pool, ETHERSCAN_TOKEN, w3)
    print(f"RESERVE: ", RESERVE)

def getReserve(TOKEN, poolAddress, ETHERSCAN_TOKEN, w3):
    """call token addresses 'balanceOf' function with pool address to show
    how many tokens of each type in pool
    will include unclaiemd tokens despite them not adding to liquidity
    but gas is low at the moment so maybe rate of claiming is higher"""
    RESERVE = []
    for token in TOKEN:
        implementation_contract = getImplementationContract(token, w3)
        print(f"token: ", token)
        print(f"implementation contract: ", implementation_contract)
        if int(implementation_contract, 16) != 0:
            # token address is a proxy contract, use implementation address for ABI 
            tokenABI = getABI(implementation_contract, ETHERSCAN_TOKEN)
        else:
            tokenABI = getABI(token, ETHERSCAN_TOKEN)
        print(tokenABI)
        # use address and abi to call balance of function
        poolInstance = w3.eth.contract(address = token, abi = tokenABI)
        try:
            RESERVE.append(poolInstance.functions.balanceOf(poolAddress).__call__().call())
        except exceptions.ABIFunctionNotFound:
            RESERVE.append(0)
            print(f"Token uses non-EIP proxy: ", token)
        except TypeError:
            RESERVE.append(0)
            print(f"Token uses non-EIP proxy: ", token)
    return RESERVE

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