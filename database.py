import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
from flask import current_app
from config import Config

class Database:
    _connection_pool = None
    
    @classmethod
    def init_pool(cls):
        try:
            cls._connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=Config.DB_DSN
            )
            current_app.logger.info("Database connection pool initialized")
        except Exception as e:
            current_app.logger.error(f"Error initializing connection pool: {e}")
            raise
    
    @classmethod
    def get_connection(cls):
        if cls._connection_pool is None:
            cls.init_pool()
        try:
            conn = cls._connection_pool.getconn()
            current_app.logger.debug("Got connection from pool")
            return conn
        except Exception as e:
            current_app.logger.error(f"Error getting connection: {e}")
            raise
    
    @classmethod
    def return_connection(cls, conn):
        if cls._connection_pool and conn:
            cls._connection_pool.putconn(conn)
            current_app.logger.debug("Returned connection to pool")
    
    @classmethod
    def close_pool(cls):
        if cls._connection_pool:
            cls._connection_pool.closeall()
            cls._connection_pool = None
            current_app.logger.info("Database connection pool closed")