import os
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def query_db(query, params=None, fetchone=False, commit=False, dict_cursor=True):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=dict_cursor)

    cursor.execute(query, params or ())

    data = None
    
    if query.strip().lower().startswith("select"):
        data = cursor.fetchone() if fetchone else cursor.fetchall()

    if commit:
        conn.commit()

    cursor.close()
    conn.close()
    return data