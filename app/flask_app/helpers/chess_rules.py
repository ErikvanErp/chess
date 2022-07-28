#******************************************************************************
# 
# This module contains pure functions that encode the rules of the game
# - validation of moves by various pieces
# - verification of check and check-mate
#
# Note: 
# validation of en passant capture of a pawn and castling of the king
# are not handled here
# validation of these 2 moves depends on previous moves in the game
# therefore they are handled by methods of a Game object
#
#******************************************************************************

# a global variable that is CONSTANT
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
#  
#  The rules for moving various pieces (excl pawn)
#  All these functions call general_rules
#  

def king_rules(board, move):
        from_row, from_col, to_row, to_col = move
        vector = (to_row - from_row, to_col - from_col)

        if not general_rules(board, move):
            return False

        if vector in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1, -1), (1, 0), (1, 1)]:
            # make a copy of board and move king on new_board
            color = pieces[board[from_row][from_col]][0]

            new_board = [[tile for tile in row] for row in board]
            new_board[to_row][to_col] = '1' if color == 'w' else '7'
            new_board[from_row][from_col] = '0'

            # make sure king is not check-mate after proposed move
            if is_check(new_board, color):
                return False
            else:
                return True
        else:
            return False
    
def knight_rules(board, move):
    from_row, from_col, to_row, to_col = move
    vector = (to_row - from_row, to_col - from_col)

    if not general_rules(board, move):
        return False

    if vector in [(1,2), (1,-2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2,-1)]:
        return True
    else:
        return False

# rules for queen, rook, bishop
# the pieces with simple straight or diagonal motion
def queen_rook_bishop_rules(board, move, type):
    from_row, from_col, to_row, to_col = move
    vector = (to_row - from_row, to_col - from_col)

    if not general_rules(board, move):
        return False

    # queen, bishop, rook follow the rules of diagonal or straight motion
    # the move is allowed if 
    # 1. it is in the right direction for the piece
    # 2. there are no obstacles between "from" and "to"

    # 1. check that the piece moves in the right direction
    is_straight = True if vector[0] == 0 or vector[1] == 0 else False
    is_diagonal = True if vector[0] == vector[1] or vector[0] == - vector[1] else False

    if type == "q" and not (is_straight or is_diagonal):
        return False
    if type == "r" and not is_straight:
        return False
    if type == "b" and not is_diagonal:
        return False

    # 2. check for obstacles

    # how many steps are we moving?
    # if only 1 step, we are done.
    how_many = max(abs(vector[0]), abs(vector[1]))
    if how_many < 2:
        return True

    # in which direction are we moving?
    unit = [0,0]

    if vector[0] > 0:
        unit[0] = +1
    elif vector[0] < 0:
        unit[0] = -1
    else:
        unit[0] = 0

    if vector[1] > 0:
        unit[1] = +1
    elif vector[1] < 0:
        unit[1] = -1
    else:
        unit[1] = 0

    # now check all intermediate positions
    # if any piece is in the way, the move is invalid
    for i in range(1, how_many):
        if not board[from_row + unit[0] * i][from_col + unit[1] * i] == "0":
            return False 

    # if the direction is correct, and no obstacles are found, the move is valid
    return True

# general_rules is called by all rules for moving a piece
def general_rules(board, move):
    from_row, from_col, to_row, to_col = move

    # is the move in range
    if from_row not in range(8):
        return False 
    if from_col not in range(8):
        return False 
    if to_row not in range(8):
        return False 
    if to_col not in range(8):
        return False 
    
    # the "from" position is not empty
    if board[from_row][from_col] == '0':
        return False

    # you cannot capture your own piece
    color, type, ucode = pieces[board[from_row][from_col]]
    color_to, type_to, ucode_to = pieces[board[to_row][to_col]]

    if color == color_to:
        return False

    return True

#
#  Functions for check and check-mate
#  These functions rely on the rules for moving pieces
#

# is king with color check
# i.e. is the king under attack by opponent
def is_check(board, color):

    # find the king
    for i in range(8):
        for j in range(8):
            if ((color == "w" and board[i][j] == '1') 
                or (color == "b" and board[i][j] == '7')):
                king = (i, j)
    
    # print(f"king {king[0]}, {king[1]}")
    # return True from the loop as soon as 
    # an opponent's piece is found that attacks the king
    opponent = "b" if color == "w" else "w"
    # print(f"opponent {opponent}")

    # check all 64 tiles
    for i in range(8):
        for j in range(8):
            print(f"tile: i {i} j {j}")
            if (i, j) == king:
                continue
            tile = board[i][j]
            # print(f"piece {board[i][j]}")
            # if the tile contains a piece with the opponent's color
            if pieces[tile][0] == opponent: 
                # check whether it can move to king
                move = (i, j, king[0], king[1])
                type = pieces[tile][1]
                # print(f"type {type}")
                # don't use king_rules to avoid circularity
                # king_rules needs to call is_check
                # note that a king can not be "checked" by another king
                # but we need to test this for the purpose of check_mate
                if type == "k" and i - king[0] in [-1,0,1] and j - king[j] in [-1,0,1]:
                    return True
                elif type == "n" and knight_rules(board, move):
                    return True
                #  The simple rules for capture of the king by pawns are hard coded here
                elif type == "p":
                    forward = 1 if opponent == "w" else -1
                    if king[0] == i + forward and (king[1] == j + 1 or king[1] == j - 1):
                        return True
                elif type in ["q", "r", "b"] and queen_rook_bishop_rules(board, move, type):
                    return True

    # if no attackers were found, return False
    return False


# is king with color check mate 
# relies on is_check
# Junly 27: this function is incomplete
# still need to test whether a move of a piece that is not the king
# can prevent the attack on the king 
def is_check_mate(board, color):

    if not is_check(board, color):
        return False

    # find the king
    for i in range(8):
        for j in range(8):
            if ((color == "w" and board[i][j] == '1') # white king 
                or (color == "b" and board[i][j] == '7')): # black king
                king = (i, j)

    # create list of tiles surrounding the king
    king_nbhd = []
    for i in [king[0] - 1, king[0], king[0] + 1]:
        for j in [king[1] - 1, king[1], king[1] + 1]:
            if i >= 0 and i <= 7 and j >= 0  and j <= 7 and not king == (i,j):
                king_nbhd.append((i,j))

    # test whether the king has at least one tile 
    # in its neighborhood it can move to without being check after that move
    # if such a tile is found, return False (not check-mate)
    for row, col in king_nbhd:
        # if occupied by own piece: skip
        if pieces[board[row][col]][0] == color:
            continue
        else:
            # make a copy of board and move king on new_board
            new_board = [[tile for tile in row] for row in board]
            new_board[row][col] = '1' if color == 'w' else '7'
            new_board[king[0]][king[1]] = '0'

            # as soon as 1 safe move is found, it is not check-mate
            if not is_check(new_board, color):
                return False

    # if no safe tile is found, return True (check-mate)
    return True


