from curses import keyname
from pycoingecko import CoinGeckoAPI
import sqlite3


def main():
    cg = CoinGeckoAPI()
    con = sqlite3.connect("./collection.db")
    cur = con.cursor()
    getTokenPrice(cg, ['0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984'])

def getTokenPrice(cg, contractAddress):
    coinsList = cg.get_token_price(id = 'ethereum',contract_addresses = contractAddress, vs_currencies = 'usd')
    prices = []
    for key in coinsList.keys():
        prices.append(coinsList[key]["usd"])
    print(prices)
    return prices
    # print(coinsList["{coinsList.keys()}"]['usd'])





if __name__ == '__main__':
    main()