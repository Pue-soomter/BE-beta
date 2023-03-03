from flask_restx import Resource, reqparse
from models.chat import ChatModel
from flask import request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)
from models import day_format, datetime_format
from datetime import datetime
from pytz import timezone
from app import api

class NumberChatList(Resource):
    @api.doc(
        security='JWT',
        description="모든 채팅기록 받아오기",
        # params={"date": "(nullable) 특정 시점 제시 %Y-%m-%d %H:%M:%S"
        #         })
    )
    @jwt_required()
    def get(self):

        user_id = get_jwt_identity()
        chats = [chat.json() for chat in ChatModel.find_all_with_user_id(_user_id=user_id)]

        rets=[]
        lasttime = "1900-01-01"
        for chat in chats :
            current = chat['date'].strftime(day_format)
            if lasttime != current:
                rets.append({
                    "type": "new_day",
                    "utterance":current
                })
            lasttime = current
            chat['date'] = chat['date'].strftime(datetime_format)
            rets.append(chat)

        return {
            'message':"ok",
            'data': rets
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