import os
from dotenv import load_dotenv
from web3 import Web3
import requests



def main():
    load_dotenv()
    ETHERSCAN_TOKEN = os.getenv('ETHERSCAN_TOKEN')
    poolAddress = '0xfaA318479b7755b2dBfDD34dC306cb28B420Ad12'
    poolABI = getABI(poolAddress, ETHERSCAN_TOKEN)
    print(poolABI)

def getABI(address, etherscanToken):
    print(etherscanToken)
    URL = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={etherscanToken}"
    r = requests.get(URL)
    print(r.status_code)
    if r.status_code == 200:
        return r.json()
        # return r.json()["result"]
    else:
        print(f"API request status fault, response: ", r.json())

if __name__ == '__main__':
    main()