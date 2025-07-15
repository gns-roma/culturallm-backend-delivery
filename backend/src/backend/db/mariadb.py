import mariadb
from fastapi import HTTPException

from db.pool import get_pool


def db_connection():
    """Return a connection to the database, and close it when done"""
    conn = get_pool().get_connection()
    try:
        yield conn
    finally:
        conn.close()


def execute_query(
        connection: mariadb.Connection, 
        query: str, 
        params: tuple = (), 
        fetchone: bool = False,
        fetch: bool = True, 
        dict: bool = False
):
    """Execute a query and return the results if there are"""
    try:
        with connection.cursor(dictionary=dict) as cursor:
            cursor.execute(query, params)

            if fetchone:
                results = cursor.fetchone()
            elif fetch:
                results = cursor.fetchall()
            else:
                results = None
            
            if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                connection.commit()

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=f"Errore nell'esecuzione della query: {e}")
    
    return results

