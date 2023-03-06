from hmac import compare_digest
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required
)
from models import UserModel
from models import day_format, datetime_format
from datetime import datetime, timedelta
from pytz import timezone
from flask import request
from flask_restx import fields, Resource, reqparse
from app import api,expire_duration

class UserRegister(Resource):
    _parser = reqparse.RequestParser()
    _parser.add_argument('nick_name', type=str, required=True)
    # _parser.add_argument('is_member', type=bool, required=True)
    # _parser.add_argument('email', type=str, required=True)
    # _parser.add_argument('location', type=str, required=True)
    # _parser.add_argument('birth', type=str, required=True)
    # _parser.add_argument('job', type=str, required=True)
    # _parser.add_argument('age', type=str, required=True)
    # _parser.add_argument('is_allow', type=bool, required=True)

    @api.doc(
        description="사용자 회원가입을 위한 API"
    )
    @api.expect(api.model('Register', {
        'nick_name': fields.String(example="pue",required=True, description='사용자 별명')
        # 'is_member':fields.Boolean(example=False,required=True, description='비회원-false, 회원-true'),
        # 'email': fields.String(example="abcd1234@gmail.com",required=True, description='이메일(빈칸가능)'),
        # 'location': fields.String(example="경기",required=True, description='사는 지역(문자열)'),
        # 'birth': fields.String(example="1998-11-19",required=True, description='생년월일(%Y-%m-%d)'),
        # 'job': fields.String(example="학생",required=True, description='직업(문자열)'),
        # 'age': fields.String(example="20대",required=True, description='나이대(문자열)'),
        # 'is_allow': fields.Boolean(example=True, required=True, description='개인정보이용 동의여부'),
            }))
    def post(self):
        data = UserRegister._parser.parse_args()

        # if UserModel.find_by_nickname(data['nick_name']):
        #     return {"message": "A user with that nick_name already exists"}, 400

        user = UserModel(
            _nickname=data['nick_name']
            # _is_member=data['is_member'],
            # _birth=datetime.strptime(data['birth'],day_format),
            # _location=data['location'],
            # _job=data['job'],
            # _age=data['age'],
            # _is_allow=data['is_allow'],
            # _email=data['email']
        )
        user.save_to_db()
        access_token = create_access_token(identity=user.id, fresh=True)
        refresh_token = create_refresh_token(user.id)

        return {
            "message": "User created successfully.",
            "data":[{
                "access":access_token,
                "refresh":refresh_token,
                "expiresAt": (datetime.now(timezone('Asia/Seoul')) + timedelta(hours=expire_duration)).strftime(datetime_format)
            }]
        }, 201


class User(Resource):
    @api.doc(
        security='JWT',
        description="유저 정보를 얻기 위한 API, params 추가를 통해 추가 정보 가져오기가 가능함.",
        params={ "params": "추가적으로 제공받을 정보들 email birth gender location job"
    })
    @jwt_required()
    def get(self):

        params = dict(request.args.lists())
        user_id = get_jwt_identity()
        user = UserModel.find_by_id(user_id)
        if not user:
            return {
                'message': f"User's id with {user_id} cannot Find",
                'data':[{}],
            }, 404

        raw_dict = user.json()
        temp={"info":raw_dict["info"],"additional":{}}

        try:
            for key in params['params']:
                temp["additional"][key] = raw_dict["additional"][key]
        except KeyError:
            pass

        return {
            'message': "ok",
            'data':[temp]
        }, 200

    @jwt_required()
    def delete(cls):
        user_id = get_jwt_identity()
        user = UserModel.find_by_id(user_id)

        if not user:
            return {
                'message': 'User Not Found',
                'data':[{}]
                }, 404
        user.delete_from_db()
        return {
                'message': 'User deleted.',
                'data':[{}]
               }, 200

class UserRefresh(Resource):
    @api.doc(
        security='JWT',
        description="refresh token을 통한 access token 재발급, refresh_token을 authorization으로..."
    )
    @jwt_required(refresh=True)
    def get(self):
        user_id = get_jwt_identity()
        user = UserModel.find_by_id(user_id)
        if not user:
            return {
                'message': f"User's id with {user_id} cannot Find",
                'data':[{}],
            }, 404

        access_token = create_access_token(identity=user.id, fresh=True)
        return {
                   "message": "New token created successfully.",
                   "data": [{
                       "access": access_token,
                       "expiresAt": (datetime.now(timezone('Asia/Seoul')) + timedelta(hours=expire_duration)).strftime(datetime_format)
                   }]
               }, 201

class DevelopUserLogin(Resource):
    _parser = reqparse.RequestParser()
    _parser.add_argument('nick_name', type=str,required=True,help="Field named 'nick_name' cannot be blank")

    def post(self):
        data = DevelopUserLogin._parser.parse_args()

        user = UserModel.find_by_nickname(data['nick_name'])

        # this is what the `authenticate()` function did in security.py
        if user :
            # identity= is what the identity() function did in security.py—now stored in the JWT
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(user.id)
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                "expiresAt": (datetime.now(timezone('Asia/Seoul')) + timedelta(hours=expire_duration)).strftime(datetime_format),
                'user_id':user.id
            }, 200

        return {"message": "Invalid Credentials!"}, 401
