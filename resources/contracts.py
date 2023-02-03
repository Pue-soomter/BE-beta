from flask_restx import Resource, reqparse
from models.chat import ChatModel
from flask import request
from flask_jwt_extended import (
    get_jwt_identity,
)
#from app import api

class InfoContract(Resource):
    def get(self):
        params = request.args.to_dict()
        user_id = get_jwt_identity()
        banners = [chat.json() for chat in ChatModel.find_by_number_with_user_id(user_id,params['date'],10)]

        return {
            'message': "ok",
            'data': banners,
        }, 200

class LicenseContract(Resource):
    def get(self):
        params = request.args.to_dict()
        user_id = get_jwt_identity()
        banners = [chat.json() for chat in ChatModel.find_by_number_with_user_id(user_id,params['date'],10)]

        return {
            'message': "ok",
            'data': banners,
        }, 200