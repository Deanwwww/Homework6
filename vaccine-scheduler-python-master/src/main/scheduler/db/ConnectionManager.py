import pymssql
import os


class ConnectionManager:
    def __init__(self):
        """
        Initializes the ConnectionManager with database credentials from environment variables.
        """
        self.server_name = os.getenv("Server") + ".database.windows.net"
        self.db_name = os.getenv("DBName")
        self.user = os.getenv("UserID")
        self.password = os.getenv("Password")
        self.conn = None

    def create_connection(self):
        """
        Creates and returns a connection to the SQL Server database.
        """
        try:
            self.conn = pymssql.connect(
                server=self.server_name,
                user=self.user,
                password=self.password,
                database=self.db_name
            )
        except pymssql.Error as db_err:
            print("Database Programming Error in SQL connection processing!")
            print(db_err)
            quit()
        return self.conn

    def close_connection(self):
        """
        Closes the database connection.
        """
        try:
            if self.conn:
                self.conn.close()
        except pymssql.Error as db_err:
            print("Database Programming Error in SQL connection processing!")
            print(db_err)
            quit()
