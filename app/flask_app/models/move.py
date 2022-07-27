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
