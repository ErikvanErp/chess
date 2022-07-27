# pymysql connection 
from asyncio import format_helpers
from operator import truediv
import turtle
from flask_app.config.mysqlconnection import connectToMySQL
from flask_app import app
from flask import flash, session
from flask_app.models import user, move
from flask_app.helpers import chess_rules

import math

#
# A Game object represents a single game
#
class Game():
    db= "chess_schema"

    opening_position  = "54312345"
    opening_position += "66666666"
    opening_position += "00000000"
    opening_position += "00000000"
    opening_position += "00000000"
    opening_position += "00000000"
    opening_position += "CCCCCCCC"
    opening_position += "BA9789AB"

    pieces = {
            '0': (None, None, " "),
            '1': ("w", "k", u'\u2654'), 
            '2': ("w", "q", u'\u2655'), 
            '3': ("w", "b", u'\u2657'), 
            '4': ("w", "n", u'\u2658'), 
            '5': ("w", "r", u'\u2656'), 
            '6': ("w", "p", u'\u2659'), 
            '7': ("b", "k", u'\u265A'), 
            '8': ("b", "q", u'\u265B'), 
            '9': ("b", "b", u'\u265D'), 
            'A': ("b", "n", u'\u265E'), 
            'B': ("b", "r", u'\u265C'), 
            'C': ("b", "p", u'\u265F')
        }


    def __init__(self, data):
        self.id = data['id']
        # user_id initiated the invitation
        self.user_id = data['user_id']
        # user_id of the player who accepted the invitation
        self.opponent_id = data['opponent_id']
        # white:  
        # true if user who sent invitation plays white, 
        self.is_white = data['white']
        # status: 
        # 0 = pending invitation
        # 1 = active game
        # 2 = check
        # 3 = draw proposed
        # 4 = draw accepted
        # 5 = resign
        # 6 = check mate
        self.status = data['status']
        # tiles is a string of length 64
        # each character represent one tile of the board
        self.tiles = data['tiles'] 
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']

        # information obtained via JOIN
        # current_player: the user who is currently logged in 
        self.current_player = None  
        self.current_opponent = None  
        self.current_is_white = None # does current_player play white?
        self.is_your_turn = None # is it current_player's turn
        self.moves = []  # list of Move objects

#******************************************************************************
#
#  properties
#
#******************************************************************************

    # convert self.tiles to a 8 x 8 array
    @property
    def tiles_array(self):
        # self.tiles is a char(64) 
        # take the list of 64 characters
        # and store as a 8 x 8 list of lists
        # the value of tiles_array[i][j] 
        # is the piece found on row i, column j on the chess board

        return [list(self.tiles)[i:i+8] for i in range(0, 64, 8)]

    # like tiles_array, but with (color, type) tuples instead of single characters
    @property
    def tiles_array_of_tuples(self):

        new_tiles_array = []
        for row in self.tiles_array:
            new_row = []
            for tile in row:
                new_row.append(Game.pieces[tile])
            new_tiles_array.append(new_row)

        return new_tiles_array

    # number_of_moves: counts each player's move as 1
    @property
    def number_of_moves(self):

        query = ''' SELECT COUNT(*) AS 'count' FROM moves
                    WHERE game_id = %(game_id)s;
                '''
        data = {
            "game_id": self.id
        }
        result = connectToMySQL(Game.db).query_db(query, data)
        row = result[0]

        return row['count']

    # move_number: counts one move by white plus one move by black as 1.
    @property
    def move_number(self):
        return math.floor((self.number_of_moves + 1) / 2)

    # the last move that was made in this game
    @property
    def last_move(self):

        query  = "SELECT * FROM moves "
        query += "WHERE game_id = %(game_id)s "
        query += "ORDER BY created_at DESC "
        query += "LIMIT 1;" 

        result = connectToMySQL(Game.db).query_db(query, {"game_id": self.id})
        last_move = move.Move( result[0] )

        return last_move

#******************************************************************************
#
#  classmethods
#
#******************************************************************************

    # create a new game in the games table
    # when invitation is sent
    @classmethod
    def create(cls, data):

        query  = '''INSERT INTO games 
                    (user_id, opponent_id, white, status, tiles) 
                    VALUES (%(user_id)s, %(opponent_id)s, %(white)s, %(status)s, %(tiles)s)
                    '''
        data['tiles'] = cls.opening_position
        data['status'] = 0 # invitation pending

        new_id  = connectToMySQL(cls.db).query_db(query, data)

        return new_id 

    # get game information by game_id
    @classmethod
    def get_by_game_id(cls, data):
        query  = '''SELECT * from games 
                    JOIN users ON user_id = users.id
                    JOIN (SELECT * FROM users) d ON opponent_id = d.id 
                    WHERE games.id = %(game_id)s
                '''
        
        result = connectToMySQL(cls.db).query_db(query, data)
        row = result[0]

        return cls.construct_from_query_result(row)

    # get game information by user_id 
    # for active games
    @classmethod
    def get_active_games_by_user_id(cls, data):

        query  = '''SELECT * from games 
                    JOIN users ON user_id = users.id
                    JOIN (SELECT * FROM users) d ON opponent_id = d.id 
                    WHERE (user_id = %(user_id)s OR opponent_id = %(user_id)s)
                    AND status = 1 OR status = 2 OR status = 3
                    ORDER BY games.updated_at;
                '''
        result = connectToMySQL(cls.db).query_db(query, data)

        my_games = []
        for row in result:
        
            this_game = cls.construct_from_query_result(row)
            my_games.append(this_game)

        return my_games

    # get game information by user_id 
    # must specify a status in data
    @classmethod
    def get_by_user_id(cls, data):

        query  = '''SELECT * from games 
                    JOIN users ON user_id = users.id
                    JOIN (SELECT * FROM users) d ON opponent_id = d.id 
                    WHERE (user_id = %(user_id)s OR opponent_id = %(user_id)s)
                    AND status = %(status)s
                    ORDER BY games.updated_at;
                '''
        result = connectToMySQL(cls.db).query_db(query, data)

        my_games = []
        for row in result:
        
            this_game = cls.construct_from_query_result(row)
            my_games.append(this_game)

        return my_games

    # construct_from_query_result constructs a Game object 
    # based of the result of SELECT FROM games JOIN to user (2x)
    # called by 
    #    get_by_game_id
    #    get_by_user_id
    #
    @classmethod
    def construct_from_query_result(cls, row):
        
        this_game = cls(row)
        
        user_data = {
            "id": row["users.id"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "email": row["email"],
            "hashed_pwd": row["hashed_pwd"],
            "created_at": row["users.created_at"],
            "updated_at": row["users.updated_at"]
        }
        
        opponent_data = {
            "id": row["d.id"],
            "first_name": row["d.first_name"],
            "last_name": row["d.last_name"],
            "email": row["d.email"],
            "hashed_pwd": row["d.hashed_pwd"],
            "created_at": row["d.created_at"],
            "updated_at": row["d.updated_at"]
        }

        # in the games table, user_id refers to the user who sent the invitation
        # data["user_id"] is the users.id of the current player
        # (i.e. the session user_id)
        # these two may or may not be equal 
        if user_data["id"] == session["user_id"]:
            this_game.current_player = user.User(user_data)
            this_game.current_opponent = user.User(opponent_data)
            this_game.current_is_white = this_game.is_white
        else:
            this_game.current_player = user.User(opponent_data)
            this_game.current_opponent = user.User(user_data)
            this_game.current_is_white = not this_game.is_white

        return this_game

    # accept an invitation:
    # change status to 1 (active game)    
    @classmethod
    def accept_invitation(cls, data):
        query = ''' UPDATE games 
                    SET status = 1
                    WHERE games.id = %(games_id)s
                '''

        connectToMySQL(cls.db).query_db(query, data)
        return

#******************************************************************************
#
#  object methods
#  1. make_move
#  2. is_valid_move
#  3. castling_rules  <- called by is_valid_move
#  4. pawn_rules  <- called by is_valid_move
#                   
#  These methods rely on various helper functions from the chess_rules module
#
#******************************************************************************

    # make_move
    # 1. record captured piece
    #    - extra logic for en passant
    # 2. update board with the move
    #    - extra logic for castling
    # 3. determine if opposing king is check or check mate
    # 4. SQL
    #    - update games 
    #    - insert into moves 
    #
    def make_move(self, *move):
        (from_row, from_col, to_row, to_col) = move

        board = self.tiles_array
        moving_piece = board[from_row][from_col]

        # save the piece that is captured
        # for en passant capture:
        # - the move has already been verified as a valid en passant
        # - remove the captured pawn

        if board[to_row][to_col] == '0':
            if moving_piece == '6' and from_row == 4 and to_col != from_col and board[to_row][to_col] == '0':
                captured = 'C'
                board[from_row][to_col] = '0'
            elif moving_piece == 'C' and from_row == 3 and to_col != from_col and board[to_row][to_col] == '0':
                captured = '6'
                board[from_row][to_col] = '0'
            else: 
                captured = None
        else:
            captured = board[to_row][to_col]

        # make the move on the board as a 2d array 
        board[to_row][to_col] = moving_piece
        board[from_row][from_col] = '0'

        # castling: 
        # the king's move has been taken care off
        # now also move the rook
        if move == (0,3,0,1):
            board[0][0] = '0'
            board[0][2] = '5'
        elif move == (0,3,0,5):
            board[0][7] = '0'
            board[0][4] = '5'
        elif move == (7,3,7,1):
            board[7][0] = '0'
            board[7][2] = 'B'
        elif move == (7,3,7,5):
            board[7][7] = '0'
            board[7][4] = 'B'

        # after the move has been made
        # test if the opponents king is check mate or check
        color, type, ucode = Game.pieces[moving_piece]
        opponent = "b" if color == "w" else "w" 

        if chess_rules.is_check_mate(board, opponent):
            self.status = '6' # check mate
        elif chess_rules.is_check(board, opponent):
            self.status = '2' # check
        else:
            self.status = '1' # active game
        
        # convert the board back to a string to be saved as "tiles"
        tiles_new = ""
        for row in board:
            for tile in row:
                tiles_new += tile

        # make the changes in the database
        # update games
        # insert into moves

        game_query  = "UPDATE games SET tiles = %(tiles)s, status = %(status)s "
        game_query += "WHERE id = %(id)s;"

        game_data = {
            "id": self.id,
            "tiles": tiles_new,
            "status": self.status
        }

        move_query  = "INSERT INTO moves "
        move_query += "(game_id, piece, from_row, from_column, to_row, to_column, captured) "
        move_query += "VALUES "
        move_query += "(%(game_id)s, %(piece)s, %(from_row)s, %(from_column)s, %(to_row)s, %(to_column)s, %(captured)s )"

        move_data = {
            "game_id": self.id,
            "piece": moving_piece,
            "from_row": from_row,
            "from_column": from_col,
            "to_row": to_row,
            "to_column": to_col,
            "captured": captured
        }

        connectToMySQL(Game.db).query_db(game_query, game_data)
        connectToMySQL(Game.db).query_db(move_query, move_data)

        return

    # is_valid_move:
    # checks whether a proposed move is valid,
    # is_valid_move does not care whose turn it is.
    # For Castling and En Passant Capture of a pawn,
    # previous moves need to be considered.

    # this is where most of the rules of chess are coded

    def is_valid_move(self, *move):
        (from_row, from_col, to_row, to_col) = move
        vector = (to_row - from_row, to_col - from_col)

        board = [list(self.tiles)[i:i+8] for i in range(0, 64, 8)]
  
        if not chess_rules.general_rules(board, move):
            return False
        
        color, type, ucode = Game.pieces[board[from_row][from_col]]
        color_to, type_to, ucode_to = Game.pieces[board[to_row][to_col]]

        # status == '2' means check
        if self.status == '2' and type != "k":
            return False       
        # status code greater than 3: game over     
        if int(self.status) > 3:
            return False

        # castling is represented as a move of the king
        if type == "k":
            if move in [(0, 3, 0, 1), (0, 3, 0, 5), (7, 3, 7, 1), (7, 3, 7, 5)] and self.castling_rules(move):
                return True
            elif chess_rules.king_rules(board, move):
                return True
            else:
                return False

        elif type == "n":
            if chess_rules.knight_rules(board, move):
                return True
            else:
                return False

        elif type == "p":
            return self.pawn_rules(move)

        elif type in ["q", "r", "b"]:
            if chess_rules.queen_rook_bishop_rules(board, move, type):
                return True
            else:
                return False

    # validation of castling 
    # represented as a move of the king, but also involves a rook
    # for validation of castling we need to check past moves
    # the king and rook involved in castling may not have moved before
    def castling_rules(self, move):
        from_row, from_col, to_row, to_col = move

        board = [list(self.tiles)[i:i+8] for i in range(0, 64, 8)]

        if (move == (0, 3, 0, 1) and board[0][0:4] == ['5','0','0','1']
                and not self.piece_has_moved(0,3) and not self.piece_has_moved(0,0)):
            return True 
        elif (move == (7, 3, 7, 1) and board[7][0:4] == ['B','0','0','7']
                and not self.piece_has_moved(7,3) and not self.piece_has_moved(7,0)):
            return True 
        elif (move == (0, 3, 0, 5) and board[0][4:8] == ['1','0','0','0','5']
                and not self.piece_has_moved(0,3) and not self.piece_has_moved(0,7)):
            return True 
        elif (move == (7, 4, 7, 2) and board[7][4:8] == ['7','0','0','0','B']
                and not self.piece_has_moved(7,3) and not self.piece_has_moved(7,7)):
            return True 
        else:
            return False

    # helper function for castling_rules
    def piece_has_moved(self, row, col):

        query  = "SELECT id FROM moves "
        query += "WHERE game_id = %(game_id)s and from_column = %(col)s and from_row = %(row)s;"
        data = {
            "game_id": self.id,
            "row": row,
            "col": col
        }
        result = connectToMySQL(Game.db).query_db(query, data)

        if len(result) < 1:
            return False
        else:
            return True

    # validation of moves by the pawn
    # For en passant capture we need to check the previous move
    def pawn_rules(self, move):
        from_row, from_col, to_row, to_col = move
        vector = (to_row - from_row, to_col - from_col)
        
        board = [list(self.tiles)[i:i+8] for i in range(0, 64, 8)]
        color, type, ucode = Game.pieces[board[from_row][from_col]]
        color_to, type_to, ucode_to = Game.pieces[board[to_row][to_col]]

        # vertical direction of motion and starting row depend on color
        forward = 1 if color == "w" else -1
        start_row = 1 if color == "w" else 6

        # for each of 4 possible vectors allowed by a pawn, check if they are valid

        # move 1 forward to an empty spot
        if vector == (forward, 0):
            if board[from_row + forward][from_col] == "0":
                return True
            else:
                return False
        
        # move 2 forward; only allowed from starting position
        elif vector == (2 * forward,0) and from_row == start_row:
            if board[from_row + forward][from_col] == "0" and board[from_row + 2 * forward][from_col] == "0":
                return True
            else: 
                return False

        # capture of a piece
        elif vector in [(forward, 1), (forward, -1)]:
            # an ordinary capture
            if color_to and color != color_to:
                return True
            # en passant capture of pawn
            else:
                previous = self.last_move
                if ((not color_to) and color == "w" 
                        and from_row == 4  
                        and previous.piece == 'C'
                        and previous.from_row == 6
                        and previous.from_col == to_col
                        and previous.to_row == 4):
                    return True
                elif ((not color_to) and color == "b" 
                        and from_row == 3  
                        and previous.piece == '6'
                        and previous.from_row == 1
                        and previous.from_col == to_col
                        and previous.to_row == 3):
                    return True
                else:
                    return False

