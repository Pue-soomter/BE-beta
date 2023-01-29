from flask_restful import Resource, reqparse
from models.chat import ChatModel
from flask import request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)

class NumberChatList(Resource):

    @jwt_required()
    def get(self):
        params = request.args.to_dict()
        user_id = get_jwt_identity()
        chats = [chat.json() for chat in ChatModel.find_by_number_with_user_id(user_id,params['date'],10)]
        return {'chats': chats}, 200

class AllChatList(Resource):

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        chats = [chat.json() for chat in ChatModel.find_all_by_user_id(user_id)]
        return {'chats': chats},200