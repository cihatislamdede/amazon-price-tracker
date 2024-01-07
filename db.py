import logging
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# print("POSTGRES_PASSWORD:", os.environ["POSTGRES_PASSWORD"])

conn = psycopg2.connect(
    database=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ["POSTGRES_HOST"],
)
c = conn.cursor()


def create_table():
    try:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                threshold_price DECIMAL NOT NULL,
                creator_id TEXT NOT NULL,
                IS_DELETED BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at timestamp 
            )
            """
        )
        # create notification table
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL,
                price DECIMAL NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            """
        )
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()


def insert_product(url, title, threshold_price, creator_id):
    try:
        c.execute(
            "INSERT INTO products (url, title, threshold_price, creator_id) VALUES (%s, %s, %s, %s)",
            (url, title, threshold_price, creator_id),
        )
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()


def update_threshold(id, threshold_price):
    try:
        c.execute(
            "UPDATE products SET threshold_price = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (threshold_price, id),
        )
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()


def delete_product(id):
    try:
        c.execute(
            "UPDATE products SET IS_DELETED = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (id,),
        )
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()


def get_product(id):
    c.execute("SELECT * FROM products WHERE id = %s", (id,))
    return c.fetchone()


def get_all_products():
    c.execute("SELECT * FROM products WHERE IS_DELETED = FALSE")
    return c.fetchall()


def insert_notification(product_id, price):
    try:
        c.execute(
            "INSERT INTO notifications (product_id, price) VALUES (%s, %s)",
            (product_id, price),
        )
        conn.commit()
    except Exception as e:
        logging.error(e)
        conn.rollback()


def get_latest_notification(product_id):
    c.execute(
        "SELECT * FROM notifications WHERE product_id = %s ORDER BY id DESC LIMIT 1",
        (product_id,),
    )
    return c.fetchone()


create_table()
