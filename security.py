import os
import jwt
import functools
from datetime import datetime, timedelta
from dateutil import parser

users = [ 
    {"id": 1, "username": 'cribbsky', "password": 'cribbsky', "dn": "/C=US/ST=Virginia/CN=Grace Hopper"},
    {"id": 2, "username": 'cribbsky2', "password": 'cribbsky2', "dn": "/C=US/ST=Virginia/CN=Grace"}
]

userdn_mapping = { u['dn']: u for u in users }
username_mapping = { u['username']: u for u in users}
userid_mapping = { u['id']: u for u in users }

def remove_key(d, key):
    r = dict(d)
    del r[key]
    return r

def check_dn(username,password):
    dn = request.environ.get('HTTP_SSL_CLIENT_S_DN')
    user = userdn_mapping.get(dn, None)
    if user:
        return remove_key(user, "password")
    else:
        return {"error": "you do not have authorization"}

def check_user(username,password):
    user = username_mapping.get(username, None)
    if user and user['password'] == password:
        return remove_key(user, "password")
    else:
        return {"error": "you do not have authorization"}  

def jwt_required(key, request):
    def jwt_req(func):
        @functools.wraps(func)
        def function_that_runs_func(*args, **kwargs):
            headers = request.headers
            r_dn = request.environ.get('HTTP_SSL_CLIENT_S_DN')
            if "Authorization" in headers:
                encoded = headers['Authorization']
                decoded = jwt.decode(encoded, key, algorithms='HS256')
                dt = parser.parse(decoded['expiration'])
                if dt > datetime.now():
                    return decoded
                else:
                    return {"error": "Your token has expired"}
                return func(*args, **kwargs)
            else:
                print(jwt)
                return {"error": "You do not have authorization!"}
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