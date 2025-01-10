#!/usr/bin/env python3

import socket, sys, argparse
import select
import random

from cman_game import *
from cman_utils import *

class Client: 
    
    def __init__(self, server_host_name, server_port, role):
        self.role = role
        self.isFreese = True
        self.server_address = (server_host_name, server_port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.game = Game('map.txt')
        self.read_sockets = [self.client_socket]

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
        self.isFreese = bool(data[0])
        
        self.game.cur_coords[0] = (int(data[1]), int(data[2]))
        self.game.cur_coords[1] = (int(data[3]), int(data[4]))
        self.game.lives = 3 - int(data[5])
        
        byte_data = data[6:]
        bit_list = []
        for byte in byte_data:
            for index in range(8):
                bit_list.append(bool(byte & (1 << index)))
        #consider flippind the list!!!
        for id, point in enumerate(list(self.game.points.keys())):
            self.game.points[point] = int(bit_list[id])
        
        self.print_game()

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
        all_keys = ['q','a', 's', 'd', 'w']
        keys_id = {
            'w':0,
            'a':1,
            's':2,
            'd':3
        }
        while running:
            try:
                inputready, _, _ = select.select(self.read_sockets, [], [], 0.1)
            except select.error as e:
                self.client_socket.close()
            except socket.error as e:
                self.client_socket.close()

            for s in [s for s in inputready]:
                self.print_game()
                #message from server
                if s == self.client_socket:
                    bytes, _ = s.recvfrom(12)
                    handle_action[bytes[0]](bytes[1:])
                    # except: print(f"Illigel request from server {bytes[0]}")
                    continue
                # player moves
            keys = get_pressed_keys(all_keys)
            if(not len(keys)):
                continue
                keys = [all_keys[random.randint(1,4)]]
            if(keys[0] == 'q'):
                self.send_quit()
                continue
            if(keys[0] in ['a', 's', 'd', 'w'] and not self.isFreese):
                self.send_move(keys_id[keys[0]])
                continue
    
    def print_game(self):
        clear_print()
        print(f'lives = {self.game.lives}')
        for i in range(self.game.board_dims[0]):
            for j in range(self.game.board_dims[1]):
                if(self.game.board[i][j] == 'W'):
                    print("#", end ="")
                    continue
                if(self.game.cur_coords[0] == (i,j)):
                    print("C", end ="")
                    continue
                if(self.game.cur_coords[1] == (i,j)):
                    print("S", end ="")
                    continue
                if((i,j) in list(self.game.points.keys()) and self.game.points[(i,j)] == 1):
                    print("*", end ="")
                    continue
                print(" ", end ="")
                continue
            print("")
        
def main():
    parser = argparse.ArgumentParser(prog='Cman client', description='Client for the Cman game')
    parser.add_argument('role', type=str, help='Desired role', choices=['cman', 'spirit', 'watcher'])
    parser.add_argument('addr', type=str, help='IP or hostname of server')
    parser.add_argument('-p', type=int, help='Port to connect to')

    args = parser.parse_args()

    if args.p is None:
        args.p = 1337
    
    role_to_id = {
        'watcher': 0,
        'cman': 1,
        'spirit': 2,
    }

    client = Client(args.addr, args.p, role_to_id[args.role])
    
    client.send_join()
    
    client.run_game()

if __name__ == '__main__':
    main()