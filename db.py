import sqlite3

conn = sqlite3.connect("amazon.db")
c = conn.cursor()


def create_table():
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            threshold_price DECIMAL NOT NULL,
            creator_id TEXT NOT NULL,
            IS_DELETED BOOLEAN DEFAULT FALSE,
            created_at DATE DEFAULT (datetime('now','localtime')),
            updated_at DATE
        )
        """
    )
    # create notification table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price DECIMAL NOT NULL,
            created_at DATE DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """
    )
    conn.commit()


def insert_product(url, title, threshold_price, creator_id):
    c.execute(
        """
        INSERT INTO products (url, title, threshold_price, creator_id)
        VALUES (?, ?, ?, ?)
        """,
        (url, title, threshold_price, creator_id),
    )
    conn.commit()


def update_threshold(id, threshold_price):
    c.execute(
        """
        UPDATE products
        SET threshold_price = ?, updated_at = (datetime('now','localtime'))
        WHERE id = ?
        """,
        (threshold_price, id),
    )
    conn.commit()


def delete_product(id):
    c.execute(
        """
        UPDATE products
        SET IS_DELETED = TRUE, updated_at = (datetime('now','localtime'))
        WHERE id = ?
        """,
        (id,),
    )
    conn.commit()


def get_product(id):
    c.execute(
        """
        SELECT * FROM products
        WHERE id = ? AND IS_DELETED = FALSE
        """,
        (id,),
    )
    return c.fetchone()


def get_all_products():
    c.execute(
        """
        SELECT * FROM products WHERE IS_DELETED = FALSE
        """
    )
    return c.fetchall()


def insert_notification(product_id, price):
    c.execute(
        """
        INSERT INTO notifications (product_id, price)
        VALUES (?, ?)
        """,
        (product_id, price),
    )
    conn.commit()


def get_latest_notification(product_id):
    c.execute(
        """
        SELECT price, created_at FROM notifications
        WHERE product_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (product_id,),
    )
    return c.fetchone()
