import sqlite3

class Database():
    def __init__(self, database='urn.db'):
        # THE DATABASE FILENAME
        self.database = database
        self.statement = ''
        self.connected = False
        self.connect()

    def connect(self):
        """Connect to the SQLite3 database."""
        self.connection = sqlite3.connect(self.database)
        self.cursor = self.connection.cursor()
        self.connected = True
        self.statement = ''

    def close(self): 
        """Close the SQLite3 database."""
        self.connection.commit()
        self.connection.close()
        self.connected = False

    def execute(self, statement, tuple_values=""):
        """Execute complete SQL statements.
        Selected data is returned as a list of query results. Example: 
        for result in db.execute(queries):
            for row in result:
                print row
        """
        queries = []
        if not self.connected:
            #open a previously closed connection
            self.connect()
            #mark the connection to be closed once complete

        try:
            statement = statement.strip()
            #reset the test statement
            self.statement = ''
            if isinstance(tuple_values, tuple):
                self.cursor.execute(statement, tuple_values)
            else:
                self.cursor.execute(statement)
            #retrieve selected data
            data = self.cursor.fetchall()
            self.close()
            self.connected = False
            if statement.upper().startswith('SELECT'):
                #append query results
                return data
            return {"message": "SUCCESS"}

        except sqlite3.Error as error:
            print('An error occurred: ' + error.args[0] + ' For the statement: ' + statement)
            return { "error" : 'An error occurred: `' + error.args[0]}


    def init_users_table(self):
        query = 'CREATE TABLE IF NOT EXISTS users' \
        '(id INTEGER PRIMARY KEY, username VARCHAR(10), password VARCHAR(128), dn VARCHAR(123), jwt VARCHAR(123))'
        self.execute(query)

        query = "SELECT COUNT(*) FROM users"
        values = self.execute(query)

        if values[0][0] <= 0:
            insert_user = ("cribbsky", "cribbsky", '/C=US/ST=Virginia/CN=Grace Hopper', 'None')
            sql = 'INSERT INTO users (username, password, dn, jwt) values (?, ?, ?, ?)' 
            self.execute(sql, insert_user)

    def init_urns_table(self):
        query = 'CREATE TABLE IF NOT EXISTS urns' \
        '(id INTEGER PRIMARY KEY, urn VARCHAR(50), url VARCHAR(2083), ' \
        'status VARCHAR(20), project_id INTEGER(16))'
        self.execute(query)

        query = "SELECT COUNT(*) FROM urns"
        values = self.execute(query)

        if values[0][0] <= 0:
            insert_user = ("test", "http://test.local", 000000, "complete")
            sql = 'INSERT INTO urns (urn, url, project_id, status) values (?, ?, ?, ?)'
            self.execute(sql, insert_user)
            insert_user = ("test2", "http://test2.local", 123123, "complete")
            sql = 'INSERT INTO urns (urn, url, project_id, status) values (?, ?, ?, ?)'
            self.execute(sql, insert_user)
