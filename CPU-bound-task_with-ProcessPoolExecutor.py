from hashlib import md5
from random import choice
import concurrent.futures


def crypt_miner(i):
    while True:
        s = "".join([choice("0123456789") for j in range(50)])
        h = md5(s.encode('utf8')).hexdigest()

        if h.endswith("00000"):
            return f"{s} {h}"


def main():
    with concurrent.futures.ProcessPoolExecutor(max_workers=100) as executor:
        for coin in executor.map(crypt_miner, range(4)):
            print(coin)


if __name__ == '__main__':
    main()
