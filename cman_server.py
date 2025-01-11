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
        winner, everyone, s_final_score, c_final_score = run_game(server)

        for _ in range(10):
            for s in everyone:
                try: server.sendto(bytes([OPCODE.GAME_END, winner, s_final_score, c_final_score]), s)
                except: pass

            time.sleep(1)
        everyone = []
        


#Runs the game a single time, returns (winner, , s_score, c_score)
def run_game(server: socket.socket)->tuple[int, list[socket.socket]]:
    game = Game('map.txt')

    cman , spirit = None, None
    watchers = []


    while cman is None or spirit is None:
        try: bytes, client_addr = server.recvfrom(12)
        except: continue

        if bytes[0] == OPCODE.JOIN:
            if bytes[1] == 0:
                watchers.append(client_addr)

            elif bytes[1] == 1 and cman is None:
                cman = client_addr

            elif bytes[1] == 2 and spirit is None:
                spirit = client_addr

            else:
                try: server.sendto(bytes([OPCODE.ERROR]), client_addr)
                except: pass

        elif bytes[0] == OPCODE.QUIT:
            if client_addr == cman:
                cman = None
            elif client_addr == spirit:
                spirit = None
            elif client_addr in watchers:
                watchers.remove(client_addr)
            else: #A new client triss to troll the server by quitting nothing 🤡
                try: server.sendto(bytes([OPCODE.ERROR]), client_addr)
                except: pass

            pass
        
        else:
            try: server.sendto(bytes([OPCODE.ERROR]), client_addr)
            except Exception as e: pass

    print("GAME!")
    #Starting values
    c_coords, s_coords = game.get_current_players_coords()
    cur_attempts = 0
    cur_collected = [0,0,0,0,0]

    #Sound "starting gun" to Cman and spirit
    send_update(server, spirit, 1, c_coords, s_coords, cur_attempts, cur_collected)
    send_update(server, cman, 0, c_coords, s_coords, cur_attempts, cur_collected)

    for w in watchers:
        send_update(server, w, 1, c_coords, s_coords, cur_attempts, cur_collected)
        
    #Now we play game - get commands and update game state accordingly
    game.next_round() #This starts the game

    first_move = True    
    while game.state != State.WIN:
        try: bytes, client_addr = server.recvfrom(12)
        except: continue

    

        if bytes[0] == OPCODE.JOIN:
            if bytes[1] != 0:
                try: server.sendto(bytes([OPCODE.ERROR]), client_addr)
                except: pass

            else: #New spectator! 🚀
                watchers.append(client_addr)
                send_update(server, client_addr, 1, c_coords, s_coords, cur_attempts, cur_collected)

        elif bytes[0] == OPCODE.MOVEMENT:
            direction = bytes[1]

            if client_addr == cman:
                state_change = game.apply_move(0, direction)

                if first_move: first_move = False

            elif not(first_move) and client_addr == spirit:
                state_change = game.apply_move(1, direction)

            if state_change:
                c_coords, s_coords = game.get_current_players_coords()
                cur_collected = calc_collected_from_points(game.points)
                cur_attempts = MAX_ATTEMPTS - game.lives

                try:
                    send_update(server, cman, 0, c_coords, s_coords, cur_attempts, cur_collected)
                    send_update(server, spirit, 0, c_coords, s_coords, cur_attempts, cur_collected)

                    for s in watchers:
                        send_update(server, s, 1, c_coords, s_coords, cur_attempts, cur_collected)
                except: pass

        elif bytes[0] == OPCODE.QUIT:
            if client_addr == cman:
                return 2, [spirit] + watchers, MAX_ATTEMPTS - game.lives, game.score
            elif client_addr == spirit:
                return 1, [cman] + watchers, MAX_ATTEMPTS - game.lives, game.score
            elif client_addr in watchers:
                watchers.remove(client_addr)


        #Game state update, game end, and error - don't need any response from the server, these are all server->client messages
        else:
            pass

    winner = game.get_winner() + 1
    s_final_score, c_final_score = game.get_game_progress()
    s_final_score = MAX_ATTEMPTS - s_final_score

    return winner, [cman, spirit] + watchers, s_final_score, c_final_score

#Sends a game state update to a given client
def send_update(server, player_address, freeze, c_coords:tuple[int,int], s_coords:tuple[int,int], attempts, collected:list[int]):
    msg = [OPCODE.GAME_STATE_UPDATE, freeze, c_coords[0], c_coords[1], s_coords[0], s_coords[1], attempts]+collected

    try: server.sendto(bytes(msg), player_address)
    except: pass

#Converts points dict (from Game class) to the wanted format in send_update
def calc_collected_from_points(points):
    array_of_collected = [0 if points[p] == 1 else 1 for p in points.keys()] #This is an list of length 40, we want a list where each entry is a byte to send
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