from be.model import store
import os
from fe import conf

class DBConn:
    def __init__(self):
        self.database = store.get_nosql_db_conn()
        self.con = store.get_db_conn()
        self.conn = self.con.cursor()
        if conf.Use_Large_DB:
            self.book_tb = 'book_lx'
            self.col_book = self.database["book_lx"]
        else:
            self.book_tb = 'book'
            self.col_book = self.database["book"]
        '''
        parent_path = os.path.dirname(os.path.dirname(__file__))
        self.db_s = os.path.join(parent_path, "data/book.db")
        self.db_l = os.path.join(parent_path, "data/book_lx.db")
        large = False
        if large:
            self.book_db = self.db_l
        else:
            self.book_db = self.db_s
        '''
    def user_id_exist(self, user_id):
        self.conn.execute(
            "SELECT user_id FROM user_ WHERE user_id = %s;", (user_id,)
        )
        row = self.conn.fetchone()
        if row is None:
            return False
        else:
            return True

    def book_id_exist(self, store_id, book_id):
        self.conn.execute(
            "SELECT book_id FROM store WHERE store_id = %s AND book_id = %s;",
            (store_id, book_id),
        )
        row = self.conn.fetchone()
        if row is None:
            return False
        else:
            return True

    def store_id_exist(self, store_id):
        self.conn.execute(
            "SELECT store_id FROM user_store WHERE store_id = %s;", (store_id,)
        )
        row = self.conn.fetchone()
        if row is None:
            return False
        else:
            return True
        
    def new_order_id_exist(self, order_id):
        self.conn.execute(
            "SELECT order_id FROM new_order WHERE order_id = %s;", (order_id,)
        )
        row = self.conn.fetchone()
        if row is None:
            return False
        else:
            return True
        
    def his_order_id_exist(self, order_id):
        self.conn.execute(
            "SELECT order_id FROM history_order WHERE order_id = %s;", (order_id,)
        )
        row = self.conn.fetchone()
        if row is None:
            return False
        else:
            return True