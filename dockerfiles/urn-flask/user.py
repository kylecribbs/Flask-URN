class User():
    def __init__(self, _id, username, password, dn):
        self.id = _id
        self.username = username
        self.password = password
        self.dn = dn
    
    def __iter__(self):
        yield 'id', self.id
        yield 'username', self.username
        yield 'password', self.password
        yield 'dn', self.dn