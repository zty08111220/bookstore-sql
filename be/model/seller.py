import sqlite3 as sqlite
import psycopg2
import logging
from be.model import error
from be.model import db_conn


class Seller(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            self.conn.execute(
                "INSERT into store(store_id, book_id, book_info, stock_level)"
                "VALUES (%s, %s, %s, %s)",
                (store_id, book_id, book_json_str, stock_level),
            )

            # decoder=json.JSONDecoder()
            # book_info=decoder.decode(book_json_str)
            # self.book_conn.execute(
            #     """INSERT INTO book """
            # )
            self.con.commit()
        except psycopg2.Error as e:
            logging.error(e)
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(
        self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            self.conn.execute(
                "UPDATE store SET stock_level = stock_level + %s "
                "WHERE store_id = %s AND book_id = %s",
                (add_stock_level, store_id, book_id),
            )
            self.con.commit()
        except psycopg2.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> tuple[(int, str)]:
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            self.conn.execute(
                "INSERT into user_store(user_id, store_id) VALUES (%s, %s)",
                (user_id, store_id),
            )
            if self.conn.rowcount != 1:
                logging.error('fail')
                return 528, 'fail'
            self.con.commit()
        except psycopg2.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"