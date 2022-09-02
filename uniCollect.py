import os
from dotenv import load_dotenv
from web3 import Web3, exceptions
import requests
import pandas as pd
import sqlite3
from pycoingecko import CoinGeckoAPI

def main():
    load_dotenv()
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')
    UNI_FACTORY_V2 = os.getenv('UNI_FACTORY_V2')
    UNI_FACTORY_V3 = os.getenv('UNI_FACTORY_V3')
    w3 = init_connection()
    con = sqlite3.connect("./collection.db")
    cur = con.cursor()
    cur.execute("DELETE FROM pools")
    cg = CoinGeckoAPI()
    token0 = '0x6B175474E89094C44Da98b954EedeAC495271d0F'
    token1 = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'

    getAllPoolInfo(token0, token1, w3, UNI_FACTORY_V2, UNI_FACTORY_V3, ETHERSCAN_TOKEN, cur, cg)
    con.commit()
    writeToCSV(cur)

def writeToCSV(cur):
    f = open('./output.csv', 'w')
    # Execute the query
    cur.execute('select * from pools')
    # Get Header Names (without tuples)
    colnames = [desc[0] for desc in cur.description]
    # Get data in batches
    while True:
        # Read the data
        df = pd.DataFrame(cur.fetchall())
        # We are done if there are no data
        if len(df) == 0:
            break
        # Let us write to the file
        else:
            df.to_csv(f, header=colnames)


def getAllPoolInfo(token0, token1, w3, UNI_FACTORY_V2, UNI_FACTORY_V3, ETHERSCAN_TOKEN, cur, cg):
    V2Pools = getV2PairAddress(token0, token1, w3, UNI_FACTORY_V2, ETHERSCAN_TOKEN)
    (V3Pools, bips) = getV3PairAddresses(token0, token1, w3, UNI_FACTORY_V3, ETHERSCAN_TOKEN)

    getV2PoolData(V2Pools, w3, ETHERSCAN_TOKEN, cur, cg)
    getV3PoolData(V3Pools, bips, w3, ETHERSCAN_TOKEN, cur, cg)

def getV3PoolData(V3Pools, bips, w3, ETHERSCAN_TOKEN, cur, cg):
    etherscan_verified_ABI_address = '0x8f8EF111B67C04Eb1641f5ff19EE54Cda062f163'
    # use hardcoded address which etherscan seems to point to as the 
    # verified version of later v3 pool implementations
    poolABI = getABI(etherscan_verified_ABI_address, ETHERSCAN_TOKEN)
    count = 0
    for V3Pool in V3Pools:
        poolInstance = w3.eth.contract(address = V3Pool, abi = poolABI)
        try:
            TOKEN = (poolInstance.functions.token0.__call__().call(), poolInstance.functions.token1.__call__().call())
        except ValueError:
            # value error raised when contract source not verified on etherscan
            break
        RESERVE = getReserve(TOKEN, V3Pool, ETHERSCAN_TOKEN, w3)
        RESERVE[0] = normalise_decimals(TOKEN[0], RESERVE[0], w3, ETHERSCAN_TOKEN)
        RESERVE[1] = normalise_decimals(TOKEN[1], RESERVE[1], w3, ETHERSCAN_TOKEN)
        try:
            TOKEN0_by_TOKEN1 = RESERVE[1] / RESERVE[0]
        except ZeroDivisionError:
            TOKEN0_by_TOKEN1 = 0
        PRICE = getTokenPrice(cg, [TOKEN[0], TOKEN[1]])
        TVL = (PRICE[0] * RESERVE[0], PRICE[1] * RESERVE[1])
        cur.execute("INSERT INTO pools (pool_address, uni_V_no, token0_address, token1_address, fee_tier, token0_amount, token1_amount, TVL_token0, TVL_token1, Token0_by_Token1, token0_usd_price, token1usd_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (V3Pool, 3, TOKEN[0], TOKEN[1], bips[count], RESERVE[0], RESERVE[1], TVL[0], TVL[1], TOKEN0_by_TOKEN1, PRICE[0], PRICE[1]))
        count += 1

def getReserve(TOKEN, poolAddress, ETHERSCAN_TOKEN, w3):
    """call token addresses 'balanceOf' function with pool address to show
    how many tokens of each type in pool
    will include unclaiemd tokens despite them not adding to liquidity
    but gas is low at the moment so maybe rate of claiming is higher"""
    RESERVE = []
    for token in TOKEN:
        implementation_contract = getImplementationContract(token, w3)
        if int(implementation_contract, 16) != 0:
            # token address is a proxy contract, use implementation address for ABI 
            tokenABI = getABI(implementation_contract, ETHERSCAN_TOKEN)
        else:
            tokenABI = getABI(token, ETHERSCAN_TOKEN)
        # use address and abi to call balance of function
        poolInstance = w3.eth.contract(address = token, abi = tokenABI)
        try:
            call = poolInstance.functions.balanceOf(poolAddress).call()
            RESERVE.append(call)
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


def getV3PairAddresses(token0, token1, w3, UNI_FACTORY_V3, ETHERSCAN_TOKEN):
    bips = [100, 500, 3000, 10000]
    poolAddresses = []
    poolBips = []
    V3_ABI = getABI(UNI_FACTORY_V3, ETHERSCAN_TOKEN)
    contract_instance = w3.eth.contract(address = UNI_FACTORY_V3, abi = V3_ABI)
    for fee in bips:
        poolAddress = contract_instance.functions.getPool(token0, token1, fee).call()
        # getPool returns null address if no pool found
        if int(poolAddress, 16) != 0:
            poolAddresses.append(poolAddress)
            poolBips.append(fee)
    return (poolAddresses, poolBips) 
        
        

def getV2PoolData(poolAddress, w3, ETHERSCAN_TOKEN, cur, cg):
    # get ABI
    poolABI = getABI(poolAddress, ETHERSCAN_TOKEN)
    # print(f"pool address: ", poolAddress)
    poolInstance = w3.eth.contract(address = poolAddress, abi = poolABI)
    # call pool instance to get data
    TOKEN = (poolInstance.functions.token0.__call__().call(), poolInstance.functions.token1.__call__().call())
    RAW_RESERVES = poolInstance.functions.getReserves.__call__().call()
    # customise for decimals!:
    RESERVE = (normalise_decimals(TOKEN[0], int(RAW_RESERVES[0]), w3, ETHERSCAN_TOKEN), normalise_decimals(TOKEN[1], int(RAW_RESERVES[1]), w3, ETHERSCAN_TOKEN))
    TOKEN0_by_TOKEN1 = (RESERVE[1] / RESERVE[0])
    PRICE = getTokenPrice(cg, [TOKEN[0], TOKEN[1]])
    TVL = (PRICE[0] * RESERVE[0], PRICE[1] * RESERVE[1])

    cur.execute("INSERT INTO pools (pool_address, uni_V_no, token0_address, token1_address, fee_tier, token0_amount, token1_amount, TVL_token0, TVL_token1, Token0_by_Token1, token0_usd_price, token1usd_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (poolAddress, 2, TOKEN[0], TOKEN[1], 3000, RESERVE[0], RESERVE[1], TVL[0], TVL[1], TOKEN0_by_TOKEN1, PRICE[0], PRICE[1]))
    
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


def getTokenPrice(cg, contractAddress):
    prices = []
    coinsList = cg.get_token_price(id = 'ethereum',contract_addresses = contractAddress, vs_currencies = 'usd')
    for key in coinsList.keys():
        prices.append(coinsList[key]["usd"])
    return prices


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
    return w3

if __name__ == '__main__':
    main()