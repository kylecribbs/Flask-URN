#!venv/bin/python
import os
import jwt
from flask import Flask, request
from flask_restful import Resource, Api
from datetime import datetime, timedelta

from security import check_dn, check_user, jwt_required

app = Flask(__name__)
if os.environ.get('SECRET_KEY'):
    app.secret_key = os.environ.get('KEY_THAT_MIGHT_EXIST') 
else:
    app.secret_key = "Development"
api = Api(app)

items = [
    {"id": "2", "url": "https://google.com", "urn": "google"},
    {"id": "3", "url": "https://face.com", "urn": "face"},
    {"id": "2", "url": "http://butt.com", "urn": "butt"}
]

class Auth(Resource):
    def post(self):
        data = request.get_json()
        r_dn = request.environ.get('HTTP_SSL_CLIENT_S_DN')
        if r_dn:
            user = check_dn(r_dn)
            return user
        else:
            if ("username" or "password") in data:
                user =  check_user(data['username'], data['password'])
            else:
                return {"error": "Request not properly formatted!"}
        user['expiration'] = str(datetime.now() + timedelta(hours=2))
        encoded_jwt = jwt.encode(user, app.secret_key, algorithm='HS256')
        return {"token": encoded_jwt.decode('utf-8')}
        

class Urn(Resource):
    def get(self):
        data = request.args
        temp_items = items
        if ("id") in request.args:
            r_id = request.args.get("id")
            if r_id.replace(" ", "") != "":
                temp_items = list(filter(lambda x: x['id'] == r_id, items))
        if ("url") in request.args:
            r_url = request.args.get("url")
            if r_url.replace(" ", "") != "":
                temp_items = list(filter(lambda x: x['url'] == r_url, items))
        if ("urn") in request.args:
            r_urn = request.args.get("urn")
            if r_urn.replace(" ", "") != "":
                temp_items = list(filter(lambda x: x['urn'] == r_urn, items))
        
        if len(temp_items) > 0:
            return temp_items, 200
        else:
            return {"error": "No values found!"}, 404
        return temp_items, 200
    
    def post(self):
        data = request.get_json()   
        if ("project_id" or "urn" or "url") in data:
            if next(filter(lambda x: x['urn'] == data['urn'], items), None) is not None:
                return {"error": "Urn '{}' already exist".format(data['urn'])}, 400   
            return data
        else:
            return {"error": "Body is formatted incorrectly!"}, 400

    @jwt_required(app.secret_key, request)
    def patch(self):
        data = request.get_json()
        return {"test"}


class Cert(Resource):
    def get(self):
        r_dn = request.environ.get('HTTP_SSL_CLIENT_S_DN')
        if r_dn:
            return r_dn
        else:
            return {"error": "No Cert Found!"}

    
api.add_resource(Urn, "/urn")
api.add_resource(Cert, "/cert")
api.add_resource(Auth, "/auth")

app.run(host='0.0.0.0', port=5000, debug=True)
