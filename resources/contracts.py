from flask_restx import Resource, reqparse
from models.chat import ChatModel
from flask import request
from flask_jwt_extended import (
    get_jwt_identity,
)
from app import api

class InfoContract(Resource):
    @api.doc(
        security='JWT',
        description="유저 개인정보 동의서.")
    def get(self):
        params = request.args.to_dict()
        user_id = get_jwt_identity()
        return {
            'message': "ok",
            'data': [],
        }, 200

class LicenseContract(Resource):
    @api.doc(
        security='JWT',
        description="사용된 라이센스 목록.")
    def get(self):
        params = request.args.to_dict()
        user_id = get_jwt_identity()

        return {
            'message': "ok",
            'data': [],
        }, 200