import socket, sys, argparse
from enum import IntEnum

from cman_game import *
from cman_utils import *

class OPCODE(IntEnum):
    JOIN = 0x00
    MOVEMENT = 0x01
    QUIT = 0x0f
    GAME_STATE_UPDATE = 0x80
    GAME_END = 0x8f
    ERROR = 0xff



def main():
    parser = argparse.ArgumentParser(prog='Cman server', description='Server for the Cman game')
    parser.add_argument('-p', type=int, help='Port to listen on')

    args = parser.parse_args()

    if args.p is None:
        args.p = 1337

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(('', args.p))

    while 1:
        winner, everyone = run_game(server)

        for _ in range(10):
            for s in everyone:
                server.sendto(bytes([OPCODE.GAME_END, winner, 1, 1]), s)

            time.sleep(1)
        


#Runs the game a single time, returns (winner, everyone)
def run_game(server: socket.socket)->tuple[int, list[socket.socket]]:
    game = Game('map.txt')

    cman , spirit = None, None
    watchers = []


    while cman is None or spirit is None:
        bytes, client_addr = server.recvfrom(12)

        if bytes[0] == OPCODE.JOIN:
            if bytes[1] == 0:
                watchers.append(client_addr)

            elif bytes[1] == 1 and cman is None:
                cman = client_addr

            elif bytes[1] == 2 and spirit is None:
                spirit = client_addr

            else:
                server.sendto(bytes([OPCODE.ERROR]), client_addr)
        else:
            server.sendto(bytes([OPCODE.ERROR]), client_addr)

    #Starting values
    c_coords, s_coords = game.get_current_players_coords()
    cur_attempts = 0
    cur_collected = [0,0,0,0,0]

    #Sound "starting gun" to Cman and spirit
    send_update(server, spirit, 1, c_coords, s_coords, cur_attempts, cur_collected)
    send_update(server, cman, 0, c_coords, s_coords, cur_attempts, cur_collected)

    #Now we play game - get commands and update game state accordingly
    game.next_round() #This starts the game
    
    while game.state != State.WIN:
        bytes, client_addr = server.recvfrom(12)

    

        if bytes[0] == OPCODE.JOIN:
            if bytes[1] != 0:
                server.sendto(bytes([OPCODE.ERROR]), client_addr)

            else: #New spectator! 🚀
                watchers.append(client_addr)
                send_update(server, client_addr, 1, c_coords, s_coords, cur_attempts, cur_collected)

        elif bytes[0] == OPCODE.MOVEMENT:
            pass

        elif bytes[0] == OPCODE.QUIT:
            if client_addr == cman:
                return 2, [spirit] + watchers
            elif client_addr == spirit:
                return 1, [cman] + watchers
            elif client_addr in watchers:
                watchers.remove(client_addr)


        #Game state update, game end, and error - don't need any response from the server, these are all server->client messages
        else:
            pass


def send_update(server, player_address, freeze, c_coords, s_coords, attempts, collected:list):
    msg = [OPCODE.GAME_STATE_UPDATE, freeze, c_coords[0], c_coords[1], s_coords[0], s_coords[1], attempts]+collected
    server.sendto(bytes(msg), player_address)

#Converts points dict (from Game class) to the wanted format in send_update
def calc_collected_from_points(points):
    array_of_collected = [0 if points[p] == 1 else 1 for p in points.keys()]
    correct_arr_of_collected = []

    for i in range(5):
        byte = 0
        for j in range(8):
            byte += array_of_collected[i*8 + j]
            if j != 7:
                byte <<= 1
        correct_arr_of_collected.append(byte)

    return correct_arr_of_collected

if __name__ == '__main__':
    main()