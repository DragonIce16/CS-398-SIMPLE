import gym
import numpy as np
from stable_baselines import logger

import pygame

class Player:
    def __init__(self, id, token):
        self.id = id
        self.token = token
        self.stock = {'kitten': 8, 'cat': 0}  # Initial stock of kittens and cats
        self.placed = {'kitten': 0, 'cat': 0} # Tracks kittens and cats that are on the board

class Kitten:
    def __init__(self, player, is_cat=False):
        self.player = player  # Player 1 or 2
        self.is_cat = is_cat  # True if the piece is a cat

    def symbol(self):
        if self.player == 0:
            return 'B' if self.is_cat else 'b'
        else:
            return 'W' if self.is_cat else 'w'

class BoopEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, verbose=False, manual = False):
        super(BoopEnv, self).__init__()

        self.name = "Boop"
        self.manual = manual
        self.verbose = verbose

        self.rows = 6
        self.cols = 6
        self.grid_shape = (self.rows, self.cols)
        self.n_players = 2
        self.letters = 'abcdef'  # Column labels

        self.action_space = gym.spaces.MultiDiscrete([self.rows, self.cols, 2]) # rows, columns and choose kitten/cat
        self.observation_space = gym.spaces.Box(-1, 1, self.grid_shape + (3,)) # dimensions and the three layers

        #self.reset()

    def reset(self):
        self.board = np.full(self.grid_shape, None)
        self.players = [Player(0, 'K'), Player(1, 'O')]
        self.current_player_num = 0
        self.done = False
        self.turns_taken = 0
        logger.debug(f'\n\n---- NEW GAME ----')
        return self.observation
   
    @property
    def observation(self):
        position_1 = np.array([[1 if isinstance(cell, Kitten) and cell.player == 1 else 0 for cell in row] for row in self.board])
        position_2 = np.array([[1 if isinstance(cell, Kitten) and cell.player == 2 else 0 for cell in row] for row in self.board])
        cats = np.array([[1 if isinstance(cell, Kitten) and cell.is_cat else 0 for cell in row] for row in self.board])
        out = np.stack([position_1, position_2, cats], axis=-1)
        return out

    def is_legal(self, action):
        row, col, piece_type = action
        player = self.players[self.current_player_num]
        if piece_type == 0 and player.stock['kitten'] == 0:
            return False  # No kittens left
        if piece_type == 1 and player.stock['cat'] == 0:
            return False  # No cats left
        return self.board[row, col] is None
   
    @property
    def legal_actions(self):
        player = self.players[self.current_player_num]
        return [(row, col, piece_type) for row in range(self.rows) for col in range(self.cols)
                for piece_type in [0, 1] if self.is_legal((row, col, piece_type))]

    def boop_adjacent(self, row, col):
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < self.rows and 0 <= c < self.cols and self.board[r, c]:
                booper = self.board[row, col]
                boopee = self.board[r, c]
                if booper.is_cat or (not boopee.is_cat):  # Cats can boop anything; kittens can only boop kittens
                    new_r, new_c = r + dr, c + dc
                    if 0 <= new_r < self.rows and 0 <= new_c < self.cols:
                        if self.board[new_r, new_c] is None:
                            self.board[new_r, new_c] = self.board[r, c]
                            self.board[r, c] = None
                    else:
                        self.board[r, c] = None  # Booped off the board

    def find_three_in_a_row(self, player, only_cats):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # Horizontal, vertical, diagonal (/ and \)
        winning_positions = []
        for r in range(self.rows):
            for c in range(self.cols):
                if isinstance(self.board[r, c], Kitten) and self.board[r, c].player == player:
                    if only_cats and not self.board[r, c].is_cat:
                        continue  # Ignore kittens if only checking for cats
                    for dr, dc in directions:
                        positions = [(r + i * dr, c + i * dc) for i in range(3)]
                        if all(0 <= r + i * dr < self.rows and 0 <= c + i * dc < self.cols and
                               isinstance(self.board[r + i * dr, c + i * dc], Kitten) and
                               self.board[r + i * dr, c + i * dc].player == player and
                               (not only_cats or self.board[r + i * dr, c + i * dc].is_cat)
                               for i in range(3)):
                            winning_positions.extend(positions)
        return winning_positions if winning_positions else None

    def step(self, action):
        row, col, piece_type = action
        player = self.players[self.current_player_num]

        if not self.is_legal(action):
            return self.observation(), [-1, -1], True, {}

        player.stock['kitten' if piece_type == 0 else 'cat'] -= 1
        player.placed['kitten' if piece_type == 0 else 'cat'] += 1
        self.board[row, col] = Kitten(self.current_player_num, is_cat=(piece_type == 1))

        self.boop_adjacent(row, col)
       
        # check if there are 8 kittens in the board TODO

        # check three in a row
        to_promote = self.find_three_in_a_row(self.current_player_num, False)
        if to_promote:
            for r, c in to_promote:
                if not self.board[r, c].is_cat: # if it is a kitten
                    player.placed['kitten'] -= 1  
                    self.board[r, c] = None
                    player.stock['cat'] += 1
       
        reward = [0, 0]
        winning_positions = self.find_three_in_a_row(self.current_player_num, True)
        if winning_positions:
            reward[self.current_player_num] = 1
            return self.observation, reward, True, {'winning_positions': winning_positions}

        self.current_player_num = 1 - self.current_player_num  # Alternate between 0 and 1
        return self.observation, reward, False, {}

    def render(self, mode='human'):

        


        logger.debug('\n')
        for r in range(self.rows):
            row_str = []
            for c in range(self.cols):
                cell = self.board[r, c]
                if cell is None:
                    row_str.append('.')
                else:
                    row_str.append(cell.symbol())
            logger.debug(' '.join(row_str))
        logger.debug('\nCurrent player:', 'b' if self.current_player_num==0 else 'w')
        player = self.players[self.current_player_num]
        logger.debug(f"Stock - kittens: {player.stock['kitten']}, cats: {player.stock['cat']}")
        logger.debug(f"Placed - kittens: {player.placed['kitten']}, cats: {player.placed['cat']}")
       
        legal_moves = self.legal_actions
        logger.debug('\nLegal actions:')
        move_string = ""
        for move in legal_moves:
            row, col, piece_type = move
            move_string += f'({row}, {col}, {piece_type}),'
        logger.debug(move_string)
