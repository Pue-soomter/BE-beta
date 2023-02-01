from flask import Flask, jsonify
from flask_restx import Api, fields
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from db import db
#from develop import make_mock
from datetime import timedelta

host = "0.0.0.0"
port = 5000

app = Flask(__name__)
app.secret_key = "chan"
db_url = "pue"

app.config['JWT_SECRET_KEY']="chanee"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=180)

api = Api(app) #API FLASK SERVER

#CORS(app)

sock = SocketIO(app,cors_allowed_origins="*")
CORS(app)

#this will be used for login(authenticate users)
jwt = JWTManager(app) #this will make endpoint named '/auth' (username,password)
#JWT will be made based on what authenticate returns(user) and JWT will be sent to identity to identify which user has Vaild JWT
bcrypt = Bcrypt(app)



@jwt.invalid_token_loader
def invalid_token_callback(error):  # we have to keep the argument here, since it's passed in by the caller internally
    return jsonify({
        'message': 'Signature verification failed.',
        'error': 'invalid_token'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "description": "Request does not contain an access token.",
        'error': 'authorization_required'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback():
    return jsonify({
        "description": "The token has been revoked.",
        'error': 'token_revoked'
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "description": "Request does not contain an access token.",
        'error': 'authorization_required'
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
    return "OK"

if __name__ == "__main__":
    from resources import create_api,create_socketio,create_api_models

    create_api_models(api)
    create_api(api)
    create_socketio(sock)


    db.init_app(app)

    print("Now we Run...")
    #app.run(port=5000,debug=False) #debug tells us what is problem
    sock.run(app,host=host,port=port,debug=False)