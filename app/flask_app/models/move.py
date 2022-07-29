# pymysql connection 
from flask_app.config.mysqlconnection import connectToMySQL

#
# A Move object represents a single one-player move
#
class Move():
    db= "chess_schema"

    def __init__(self, data):
        self.id = data['id']
        self.game_id = data['game_id']
        self.piece = data["piece"]
        self.from_row = data['from_row']
        self.from_column = data['from_column']
        self.to_row = data['to_row']
        self.to_column = data['to_column']
        self.promote_to = data['promote_to']
        self.captured = data['captured']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']

#
# GameState is an object that has no correspondencei in the database
# It represents the complete state of a game, 
# sufficient to determine whether any given move is allowed.
# It could be the state of the current game,
# or the state of the game after some extra moves have been tried out,
# e.g. when testing for check mate
#
# 
class GameState():

    def __init__(self, color, board, last_from_to, is_check, 
                white_king_moved, white_rook_0_moved, white_rook_7_moved, 
                black_king_moved, black_rook_0_moved, black_rook_7_moved):
        # who will do the next move
        self.color = color
        # board position as 8 x 8 array of single characters (0-9, A-C)
        self.board = board
        # game memory necessary to decide the validity of the next nmove
        self.last_from_to       = last_from_to  # 4-tupel
        self.white_king_moved   = white_king_moved
        self.white_rook_0_moved = white_rook_0_moved
        self.white_rook_7_moved = white_rook_7_moved
        self.black_king_moved   = black_king_moved
        self.black_rook_0_moved = black_rook_0_moved
        self.black_rook_7_moved = black_rook_7_moved
