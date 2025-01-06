#!/usr/bin/env python3

import socket, sys, argparse
import select

from cman_game import *
from cman_utils import *

class Client: 
    def __init__(self, server_host_name, server_port, role):
        self.role = role
        self.isFreese = True
        self.server_address = (server_host_name, server_port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.client_socket.bind()
        self.read_sockets = [sys.stdin, self.client_socket]

    def send_join(self):
        msg = [OPCODE.JOIN, self.role]
        try: 
            self.client_socket.sendto(bytes(msg), self.server_address)
            print("joined!")
        except: print("error")
    
    def send_move(self, direction):
        msg = [OPCODE.MOVEMENT, direction]
        try: self.client_socket.sendto(bytes(msg), self.server_address)
        except: pass
    
    def send_quit(self):
        msg = [OPCODE.QUIT]
        try: self.client_socket.sendto(bytes(msg), self.server_address)
        except: pass

    def handle_game_update(self, data):
        print(data)
        pass

    def handle_game_end(data):
        print(data)
        exit()

    def handle_error(data):
        exit()

    def run_game(self):
        running = True
        handle_action = {
            OPCODE.GAME_STATE_UPDATE: self.handle_game_update,
            OPCODE.GAME_END: self.handle_game_end,
            OPCODE.ERROR: self.handle_error
        }
        data_size = {
            OPCODE.GAME_STATE_UPDATE: 11,
            OPCODE.GAME_END: 3,
            OPCODE.ERROR: 11 
        }
        while running:
            try:
                inputready, _, _ = select.select(self.read_sockets, [], [])
            except select.error as e:
                self.client_socket.close()
            except socket.error as e:
                self.client_socket.close()

            for s in [s for s in inputready]:
                client = None
                #message from server
                if s == self.client_socket:
                    bytes = client.recvfrom(1)
                    try: handle_action[bytes[0]](client.recvfrom(data_size[bytes[0]]))
                    except: print("Illigel request from server")
            # player moves
            keys = get_pressed_keys()
            print(keys)
            if(keys[0] == 'Q'):
                self.send_quit()
                continue
            if(keys[0] in ['a', 's', 'd', 'w'] and not self.isFreese):
                self.send_move(keys[0])
                continue

def main():
    parser = argparse.ArgumentParser(prog='Cman client', description='Client for the Cman game')
    parser.add_argument('role', type=str, help='Desired role', choices=['cman', 'spirit', 'watcher'])
    parser.add_argument('addr', type=str, help='IP or hostname of server')
    parser.add_argument('-p', type=int, help='Port to connect to')

    args = parser.parse_args()

    if args.p is None:
        args.p = 1337

    client = Client(args.addr, args.p, args.role)
    
    client.send_join()
    
    client.run_game()

if __name__ == '__main__':
    main()