#!venv/bin/python

import os
from datetime import datetime, timedelta
import sqlite3
import jwt
from flask import Flask, request
from flask_restful import Resource, Api, reqparse

from security import check_dn, jwt_required, update_jwt
from database import Database

app = Flask(__name__) 

if os.environ.get('SECRET_KEY'):
    app.secret_key = os.environ.get('KEY_THAT_MIGHT_EXIST')
else:
    app.secret_key = "Development"

api = Api(app)

# AUTHENTICATION CLASS
class Auth(Resource):
    # POST CREDS FOR JWT TOKEN
    def post(self):
        # SETUP PARSING
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=False)
        parser.add_argument('password', type=str, required=False)
        data = parser.parse_args()

        # GET CLIENT CERT
        r_dn = request.environ.get('HTTP_SSL_CLIENT_S_DN')

        # DEFINE DATABASE
        db = Database()

        if data['username'] and data['password']:
            row = db.execute("SELECT id, username, password from users WHERE username = ?", (data['username'],))
            if len(row) > 0:
                row = row[0]
                if row[0] > 0 and row[2] == data['password']:
                    user = {"id": row[0], "username": row[1]}
                else:
                    return {"error": "Invalid credentials"}  
            else:
                return {"error": "Invalid credentials"} 
        elif r_dn:
            return r_dn
        else:
            return {"error": "Request not properly formatted!"}
        if "error" in user:
            return user
        user['expiration'] = str(datetime.now() + timedelta(hours=2))
        encoded_jwt = jwt.encode(user, app.secret_key, algorithm='HS256')
        update_jwt(row[0], encoded_jwt)
        return {"token": encoded_jwt.decode('utf-8')}
        

class Urn(Resource):
    # GET REQUEST FOR URN
    def get(self):
        # SETUP PARSING
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, required=False, default='')
        parser.add_argument('urn', type=str, required=False, default='')
        parser.add_argument('id', type=int, required=False, default='')
        parser.add_argument('project_id', type=int, required=False, default='')
        parser.add_argument('operator', type=str, required=False, choices=("and", "or"), default='or')
        parser.add_argument('status', type=str, required=False, choices=("complete", "pending"), default='complete')
        data = parser.parse_args()
        
        # DEFINE DATABASE
        db = Database()

        # SETUP NEW DICTIONARY
        new_data = {}
        for d in data:
            if data[d] != "" and d is not "operator" and d is not "status":
                new_data[d] = data[d]
        
        # SETUP QUERY and VALUES
        query = "SELECT id, url, urn, project_id, status FROM urns WHERE status = ? and ("
        values = [data['status']]
        if len(new_data) > 0: 
            for index, d in enumerate(new_data):
                if index == 0:
                    query += d + " = ?"
                else:
                    query += " " + data['operator'] + " " + d + " = ?"
            # if isinstance(new_data[d], int):
            #     new_data[d] = new_data[d].lower()
                values.append(new_data[d])
        query += ")"
        # EXECUTE AND RETURN ROWS
        return_dict = []
        rows = db.execute(query, tuple(values))

        # CHECK IF FILTER RETURNS RESULTS IF NOT DO A BROADER SEARCH
        if len(rows) == 0:
            query = query.replace("=", "LIKE")
            values =  ["%"+x+"%" if isinstance(x, str) else x for x in values]
            rows = db.execute(query, tuple(values))

        # CHECK IF FILTER NOW RETURNS RESULTS IF NOT RETURN ALL VALUES
        if len(rows) == 0:
            query = "SELECT id, url, urn, project_id, status FROM urns WHERE status = ?"
            values = (data['status'],)
            rows = db.execute(query, values)

        # RETURN VALUES IN JSON   
        if "error" in rows:
            return rows 
        for row in rows:
            return_dict.append({
                "id": row[0],
                "url": row[1],
                "urn": row[2],
                "project_id": row[3],
                "status": row[4]
            })
            
        return return_dict

    
    # POST REQUEST FOR URN
    def post(self):
        # SETUP PARSING
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, required=True)
        parser.add_argument('urn', type=str, required=True)
        parser.add_argument('project_id', type=int, required=True)
        data = parser.parse_args()

        # DEFINE DATABASE
        db = Database()

        # CHECK TO SEE IF URN EXIST
        sql = 'SELECT * FROM urns WHERE urn = ?'
        rows = db.execute(sql, (data['urn'],))
        if len(rows) > 0:
            return {"error": "There is already a request for that URN"}

        # POST TO DATABASE
        values = (data['urn'], data['url'], data['project_id'], "pending")
        sql = 'INSERT INTO urns (urn, url, project_id, status) values (?, ?, ?, ?)' 
        return db.execute(sql, values)

        

    @jwt_required(app.secret_key, request)
    # PUT REQUEST FOR URN
    def put(self, **kwargs):
        # SETUP PARSING
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, required=True)
        parser.add_argument('urn', type=str, required=True)
        parser.add_argument('id', type=int, required=True)
        parser.add_argument('project_id', type=int, required=True)
        data = parser.parse_args()

        # DEFINE DATABASE
        db = Database()

        # CHECK IF ID EXIST
        row = db.execute("SELECT id from urns WHERE id = ? and status != 'deleted'", (data['id'],))
        if len(row) == 0:
            return {"error": "ID '{}' does not exist".format(data['id'])}, 400     
        
        # UPDATE ROW IN DATABASE
        values = (data['url'], data['urn'], data['project_id'], data['id'])
        return db.execute("UPDATE urns SET url=?, urn=?, project_id=? WHERE id=?", values), 200
        

    @jwt_required(app.secret_key, request)
    # DELETE REQUEST FOR URN
    def delete(self, **kwargs):
        # SETUP PARSING
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, required=False, default='')
        parser.add_argument('urn', type=int, required=False, default='')
        data = parser.parse_args()

        # DEFINE DATABASE
        db = Database()

        if data['id']:
            # CHECK IF ID EXIST
            row = db.execute("SELECT id from urns WHERE id = ? and status != 'deleted'", (data['id'],))
            if len(row) == 0:
                return {"error": "ID '{}' does not exist".format(data['id'])}, 400    
            return db.execute("UPDATE urns SET status=? WHERE id=?", ("deleted",data['id'],))
        elif data['urn']:
            print()
        else:
            return {"error": "Body is formatted incorrectly!"}, 400

# CLASS FOR APPROVING URNs
class Urn_Approval(Resource):
    @jwt_required(app.secret_key, request)
    def patch(self, **kwargs):
        data = request.get_json()
        if ("id") in request.args:
            if "urn" in data:
                return {"test"}
            if "url" in data:
                return {"test"}
            if "status" in data:
                return {"test"}
        else:
            return {"error": "You must provide an ID!"}

        return {"test"}

# CHECK TO SEE IF USER CERT IS WORKING
class Cert(Resource):
    def get(self, **kwargs):
        r_dn = request.environ.get('HTTP_SSL_CLIENT_S_DN')
        if r_dn:
            return r_dn
        else:
            return {"error": "No Cert Found!"}

api.add_resource(Auth, "/auth")
api.add_resource(Urn, "/urn")
api.add_resource(Urn_Approval, "/urn/approval")
api.add_resource(Cert, "/cert")

app.run(host='0.0.0.0', port=5000, debug=True)
