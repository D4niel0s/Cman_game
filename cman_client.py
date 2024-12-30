import socket, sys, argparse

from cman_game import *
from cman_utils import *


def main():
    parser = argparse.ArgumentParser(prog='Cman client', description='Client for the Cman game')
    parser.add_argument('role', type=str, help='Desired role', choices=['cman', 'spirit', 'watcher'])
    parser.add_argument('addr', type=str, help='IP or hostname of server')
    parser.add_argument('-p', type=int, help='Port to connect to')

    args = parser.parse_args()

    if args.p is None:
        args.p = 1337

    

if __name__ == '__main__':
    main()