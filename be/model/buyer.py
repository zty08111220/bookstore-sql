import sqlite3 as sqlite
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
import psycopg2
import time


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def new_order(
        self, user_id: str, store_id: str, id_and_count: tuple[(str, int)]
    ) -> tuple[(int, str, str)]:
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            
            cur_time=str(int(time.time())) #纪元以来的秒数
            self.conn.execute(
                "INSERT INTO new_order(order_id, store_id, user_id, state, order_datetime) "
                "VALUES(%s, %s, %s, %s, %s);",
                (uid, store_id, user_id, "wait for payment", cur_time),
            )
            for book_id, count in id_and_count:
                self.conn.execute(
                    "SELECT book_id, stock_level, book_info FROM store "
                    "WHERE store_id = %s AND book_id = %s;",
                    (store_id, book_id),
                )
                row = self.conn.fetchone()
                if row is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                stock_level = row[1]
                book_info = row[2]
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                self.conn.execute(
                    "UPDATE store set stock_level = stock_level - %s "
                    "WHERE store_id = %s and book_id = %s and stock_level >= %s; ",
                    (count, store_id, book_id, count),
                )
                self.conn.execute(
                    "INSERT INTO new_order_detail(order_id, book_id, count, price) "
                    "VALUES(%s, %s, %s, %s);",
                    (uid, book_id, count, price),
                )


            self.con.commit()
            order_id = uid
        except psycopg2.Error as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    #调用之前需要调用者保证order_id合法
    def order_timeout(self,order_id:str) -> tuple[(int,str)]:
        conn=self.conn
        try:
            conn.execute("INSERT INTO history_order SELECT * FROM new_order WHERE order_id=%s",
                                (order_id,))
            conn.execute("UPDATE history_order SET state = 'cancelled' "
                                "WHERE state='wait for payment' AND order_id=%s",
                                (order_id,))            
            conn.execute("INSERT INTO history_order_detail SELECT * FROM new_order_detail "
                                "WHERE order_id=%s",
                                (order_id,))
            conn.execute("DELETE FROM new_order_detail WHERE order_id=%s",
                                (order_id,))
            conn.execute("DELETE FROM new_order WHERE order_id=%s",
                                (order_id,))
        except psycopg2.Error as e:
            logging.error(str(e))
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))
        return error.error_order_timeout(order_id)

    def payment(self, user_id: str, password: str, order_id: str) -> tuple[int, str]:
        conn = self.conn
        try:
            conn.execute(
                "SELECT order_id, user_id, store_id, order_datetime FROM new_order WHERE order_id = %s",
                (order_id,),
            )
            row = conn.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)

            order_id = row[0]
            buyer_id = row[1]
            store_id = row[2]
            order_datetime=int(row[3])
            if buyer_id != user_id:
                return error.error_authorization_fail()
            
            timeout_limit=10 #这里的超时时间设置为1秒，方便调试
            if order_datetime+timeout_limit<int(time.time()):
                return self.order_timeout(order_id)

            conn.execute(
                "SELECT balance, password FROM user_ WHERE user_id = %s;", (buyer_id,)
            )
            row = conn.fetchone()
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = row[0]
            if password != row[1]:
                return error.error_authorization_fail()

            conn.execute(
                "SELECT store_id, user_id FROM user_store WHERE store_id = %s;",
                (store_id,),
            )
            row = conn.fetchone()
            if row is None:
                return error.error_non_exist_store_id(store_id)

            seller_id = row[1]

            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            conn.execute(
                "SELECT book_id, count, price FROM new_order_detail WHERE order_id = %s;",
                (order_id,),
            )
            rows = conn.fetchall()
            total_price = 0
            for row in rows:
                count = row[1]
                price = row[2]
                total_price = total_price + price * count

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            conn.execute(
                "UPDATE user_ set balance = balance - %s "
                "WHERE user_id = %s AND balance >= %s",
                (total_price, buyer_id, total_price),
            )

            conn.execute(
                "UPDATE user_ set balance = balance + %s WHERE user_id = %s",
                (total_price, seller_id),
            )

            # order从new_order中删除并插入history_order中
            conn.execute(
                "INSERT INTO history_order "
                "SELECT * FROM new_order WHERE order_id = %s",
                (order_id,),
            )
            # 更新state为等待发货
            conn.execute(
                "UPDATE history_order "
                "SET state='wait for delivery' "
                "WHERE order_id = %s",
                (order_id,),
            )


            # order_detail从new_order_detail中删除并插入history_order_detail中
            conn.execute(
                "INSERT INTO history_order_detail "
                "SELECT * FROM new_order_detail WHERE order_id=%s",
                (order_id,),
            )
            self.con.commit()
            conn.execute(
                "DELETE FROM new_order_detail where order_id = %s", (order_id,)
            )
            
            conn.execute(
                "DELETE FROM new_order WHERE order_id = %s", (order_id,)
            )
            self.con.commit()

        except psycopg2.Error as e:
            logging.error(str(e))
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> tuple[int, str]:
        try:
            self.conn.execute(
                "SELECT password from user_ where user_id = %s", (user_id,)
            )
            row = self.conn.fetchone()
            if row is None:
                return error.error_authorization_fail()

            if row[0] != password:
                return error.error_authorization_fail()

            self.conn.execute(
                "UPDATE user_ SET balance = balance + %s WHERE user_id = %s",
                (add_value, user_id),
            )
            self.con.commit()
        except psycopg2.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def cancel_order(
        self, user_id: str, order_id: str
    ) -> tuple[int, str]:
        conn = self.conn
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.new_order_id_exist(order_id):
                return error.error_invalid_order_id(order_id)
            #修改state状态，并将其从new_order移到history_order
            conn.execute(
                "UPDATE new_order set state='cancelled' "
                "WHERE user_id = %s AND order_id = %s AND state='wait for payment'",
                (user_id,order_id)
            )
            
            conn.execute(
                "INSERT INTO history_order "
                "SELECT * FROM new_order WHERE order_id=%s",
                (order_id,)
            )     
            #将new_order_detail做出相应的改动
            conn.execute(
                "INSERT INTO history_order_detail "
                "SELECT * FROM new_order_detail WHERE order_id=%s",
                (order_id,)
            )
            conn.execute(
                "DELETE FROM new_order_detail "
                "WHERE order_id=%s",
                (order_id,)
            )
            
            conn.execute(
                "DELETE FROM new_order "
                "WHERE order_id=%s",
                (order_id,)
            )
            self.con.commit()
        except psycopg2.Error as e:
            logging.error(str(e))
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200,"ok"