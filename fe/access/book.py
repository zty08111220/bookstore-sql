import os
import sqlite3 as sqlite
import random
import base64
import simplejson as json
import pymongo
from be.model import store


class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: [str]
    pictures: [bytes]

    def __init__(self):
        self.tags = []
        self.pictures = []


class BookDB:
    def __init__(self, large: bool = False):
        self.database = store.get_nosql_db_conn()
        '''
        parent_path = os.path.dirname(os.path.dirname(__file__))
        self.db_s = os.path.join(parent_path, "data/book.db")
        self.db_l = os.path.join(parent_path, "data/book_lx.db")
        if large:
            self.book_db = self.db_l
        else:
            self.book_db = self.db_s
        '''
        if large:
            self.book_db = self.database["book_lx"]
        else:
            self.book_db = self.database["book"]

    def get_book_count(self):
        cnt = self.book_db.count_documents({})
        return cnt

    def get_book_info(self, start, size) -> [Book]:
        '''
        print(f"start: {start}, type: {type(start)}")
        print(f"size: {size}, type: {type(size)}")
        print(f"book_db type: {type(self.book_db)}")

        
        rows = self.book_db.find({}, {'_id': 0}).sort({'id': 1}).skip(start).limit(size)
        rows = self.book_db.find({}, {'_id': 0})
        print(f"rows type: {type(rows)}")
        
        sorted_rows = rows.sort({'id': 1})  # 确保这一步没有问题
        print(f"sorted_rows type: {type(sorted_rows)}")
        paginated_rows = sorted_rows.skip(start).limit(size)  # 确保这一步没有问题
        print(f"paginated_rows type: {type(paginated_rows)}")
        '''
        books = []
        rows = self.book_db.find({}, {'_id': 0}).sort({'id': 1}).skip(start).limit(size)


        '''
        conn = sqlite.connect(self.book_db)
        cursor = conn.execute(
            "SELECT id, title, author, "
            "publisher, original_title, "
            "translator, pub_year, pages, "
            "price, currency_unit, binding, "
            "isbn, author_intro, book_intro, "
            "content, tags, picture FROM book ORDER BY id "
            "LIMIT ? OFFSET ?",
            (size, start),
        )
        '''
        for row in rows:
            book = Book()
            book.id = row['id']
            book.title = row['title']
            book.author = row['author']
            book.publisher = row['publisher']
            book.original_title = row['original_title']
            book.translator = row['translator']
            book.pub_year = row['pub_year']
            book.pages = row['pages']
            book.price = row['price']

            book.currency_unit = row['currency_unit']
            book.binding = row['binding']
            book.isbn = row['isbn']
            book.author_intro = row['author_intro']
            book.book_intro = row['book_intro']
            book.content = row['content']
            tags = row['tags']

            picture = row['picture']

            for tag in tags.split("\n"):
                if tag.strip() != "":
                    book.tags.append(tag)
            for i in range(0, random.randint(0, 9)):
                if picture is not None:
                    encode_str = base64.b64encode(picture).decode("utf-8")
                    book.pictures.append(encode_str)
            books.append(book)
            # print(tags.decode('utf-8'))

            # print(book.tags, len(book.picture))
            # print(book)
            # print(tags)

        return books