from flask import Flask, jsonify
from flask_restx import Api, fields
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from db import db
from develop import make_mock
#from develop import make_mock
from datetime import timedelta
import xml.etree.ElementTree as elemTree

tree = elemTree.parse('docs/keys.xml')
secretkey = tree.find('string[@name="secret_key"]').text

host = "0.0.0.0"
port = 5000
expire_duration = 1

app = Flask(__name__)
app.secret_key = secretkey
db_info = {
    "user": tree.find('string[@name="DB_USER"]').text,
    "password": tree.find('string[@name="DB_PASS"]').text,
    "host": tree.find('string[@name="DB_HOST"]').text,
    "port": tree.find('string[@name="DB_PORT"]').text,
    "database": tree.find('string[@name="DB_DBNAME"]').text
}


app.config['JWT_SECRET_KEY']="chanee"
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{db_info['user']}:{db_info['password']}@{db_info['host']}:{db_info['port']}/{db_info['database']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 499
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20

app.config['PROPAGATE_EXCEPTIONS'] = True
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=expire_duration)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=180)


api = Api(app) #API FLASK SERVER

#CORS(app)
CORS(app)

#this will be used for login(authenticate users)
jwt = JWTManager(app) #this will make endpoint named '/auth' (username,password)
#JWT will be made based on what authenticate returns(user) and JWT will be sent to identity to identify which user has Vaild JWT
bcrypt = Bcrypt(app)

@jwt.invalid_token_loader
def invalid_token_callback(error):  # we have to keep the argument here, since it's passed in by the caller internally
    return jsonify({
        'message': 'Signature verification failed.',
        "data":[{}]

    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "message": "Request does not contain an access token.",
        "data":[{}]
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback():
    return jsonify({
        "message": "The token has been revoked.",
        "data":[{}]
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "message": "Request does not contain an access token.",
        "data":[{}]
    }), 401

@app.before_first_request
def create_tables():
    db.create_all()

##only for development
@app.route('/health')
def health():
    return "OK"

@app.route('/mock')
def mock():
    make_mock()
    return "OK"

if __name__ == "__main__":
    from resources import create_api,create_api_models

    create_api_models(api)
    create_api(api)
    #create_socketio(sock)

    db.init_app(app)

    print("Now we Run...")
    app.run(host=host,port=port,debug=False) #debug tells us what is problem
    #sock.run(app,host=host,port=port,debug=False)