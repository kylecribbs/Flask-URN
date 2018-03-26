import os
import jwt
import functools
from datetime import datetime, timedelta
from dateutil import parser
from database import Database

db = Database()
db.init_users_table()
db.init_urns_table()

def remove_key(d, key):
    r = dict(d)
    del r[key]
    return r

def check_dn(dn):
    db = Database()
    row = db.execute("SELECT id, username from users WHERE dn = ?", (dn,))

    if len(row) > 0:
        row = row[0]
        return {"id": row[0], "username": row[1]} 
    else:
        return {"error": "Invalid credentials"}  

def update_jwt(_id, token):
    db = Database()
    token = token.decode("utf-8")
    values = (token, _id,)
    db.execute("UPDATE users SET jwt=? WHERE id=?", values)

# def find_user_by_dn(dn):
#     conn = sqlite3.connect('urn.db')
#     c = conn.cursor()

#     query = "SELECT * from users WHERE dn=?"
#     result = c.execute(query, (dn,))
#     row = result.fetchone()
#     if row:
#         user(row[0], row[1], row[2], row[3])
#     else:
#         user = None
    
#     conn.close()
#     return user

def jwt_required(key, request):
    def jwt_req(func):
        @functools.wraps(func)
        def function_that_runs_func(*args, **kwargs):
            headers = request.headers
            r_dn = request.environ.get('HTTP_SSL_CLIENT_S_DN')
            if "Authorization" in headers:
                encoded = headers['Authorization']
                db = Database()
                values = (encoded,)
                row = db.execute("SELECT id FROM users WHERE jwt=?", values)
                if len(row) <= 0:
                    return {"error": "Invalid token!"}
                decoded = jwt.decode(encoded, key, algorithms='HS256')
                if row[0][0] != decoded['id']:
                    return {"error": "Invalid token!"}
                dt = parser.parse(decoded['expiration'])
                if dt > datetime.now():
                    kwargs['decoded'] = decoded
                else:
                    return {"error": "Your token has expired"}
                return func(*args, **kwargs)
            else:
                return {"error": "Invalid request!"}
        return function_that_runs_func
    return jwt_req

def cert_required(request):
    def cert_req(func):
        @functools.wraps(func)
        def func_that_runs_func(*args, **kwargs):           
            r_dn = request.environ.get('HTTP_SSL_CLIENT_S_DN')
            if r_dn:
                return func(*args, **kwargs)
            else:
                return {"error": "You need a valid certificate"}
        return func_that_runs_func
    return cert_req