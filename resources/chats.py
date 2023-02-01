from flask_restx import Resource, reqparse
from models.chat import ChatModel
from flask import request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)
from models import day_format, datetime_format
from datetime import datetime
from app import api

class NumberChatList(Resource):
    @jwt_required()
    @api.doc(
        security='JWT',
        description="특정 시점으로부터 이전 10개의 채팅기록 받아오기",
        params={"date": "특정 시점 제시 %Y-%m-%d %H:%M:%S"
                })
    def get(self):
        params = request.args.to_dict()
        user_id = get_jwt_identity()
        chats = [chat.json() for chat in ChatModel.find_by_number_with_user_id(_user_id=user_id,_latest=datetime.strptime(params['date'],datetime_format),number=10)]

        for chat in chats :
            chat['date'] = chat['date'].strftime(datetime_format)

        return {
            'message':"ok",
            'data': chats
               }, 200

class DevelopAllChatList(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        chats = [chat.json() for chat in ChatModel.find_all_with_user_id(user_id)]

        for chat in chats :
            chat['date'] = chat['date'].strftime(datetime_format)

        return {
            'message':"ok",
            'data': chats
               }, 200