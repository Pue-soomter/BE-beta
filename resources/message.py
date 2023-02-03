from flask import session, request
from hmac import compare_digest
from flask_restx import Resource, reqparse
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)
from models import day_format, datetime_format, UserModel, ChatModel
from datetime import datetime
from pytz import timezone
from app import api
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session,sessionmaker

cached={}

def save_chat(user_id,sender,message):
    now = datetime.now(timezone('Asia/Seoul')).strftime(datetime_format)
    chat = ChatModel(
        _user_id=user_id,
        _date=now,
        _chatter='USER',
        _sentence=message
    )
    chat.save_to_db()


class HookMessage(Resource):

    engine = create_engine("sqlite:///scenarios")
    metadata_obj = MetaData()

    some_table = Table("시작", metadata_obj, autoload_with=engine)

    conn = engine.connect()

    # s = select([some_table]).where(some_table.columns.name == 'Jane Doe')
    # result = conn.execute(s).first()
    # print(result)

    _parser = reqparse.RequestParser()
    _parser.add_argument('message', type=dict, required=True)
    _parser.add_argument('additional',type=list,required=True)

    # #message
    # ->{
    #     'key'->
    #     'cursor' ->
    #     'table' ->
    #     'sentence' ->
    # }

    #additional (list)
    #type ->
    #data ->
    @jwt_required()
    @api.doc(
        security='JWT',
        description="챗봇의 다음 메세지를 받습니다.",
    )
    def post(self):
        user_id = get_jwt_identity()

        raw_data = HookMessage._parser.parse_args()
        msg = raw_data['message']
        additional=raw_data['additional']

        target_table = Table(msg["table"], HookMessage.metadata_obj, autoload_with=HookMessage.engine)
        if not compare_digest(msg["table"],"시작"):
            save_chat(user_id,'USER',msg['sentence'])
        else :
            return {
                "message":"ok",
                "data":[
                    {
                        "type":"message",
                        "message":"안녕, 오늘 기분은 어때?"
                    },
                    {
                        "type": "message",
                        "message": "너의 기분을 아래에서 표시해줘!"
                    },
                    {
                        "type": "traffic_lights",
                        "payload":[{
                            'key':'1',
                            'cursor':"유저시작",
                            'table':"시작",
                            'sentence':"기분이 좋지 않아",
                        },{
                            'key':'2',
                            'cursor':"유저시작",
                            'table':"시작",
                            'sentence':"그저 그래",
                        },{
                            'key': '3',
                            'cursor': "유저시작",
                            'table': "시작",
                            'sentence': "괜찮은 것 같아",
                        }

                        ]
                    }
                ]
            }


        target_table = Table(msg["table"], HookMessage.metadata_obj, autoload_with=HookMessage.engine)
        s = select([target_table]).where(target_table.columns.구분 == msg_cursor)
        row = conn.execute(s).first()
        print(row['문장1'])

        # if input == "슬픔":
        #     emit(sad_sc[0])
        #
        # #
        # processed_data = main_ai.run("Chanee",data['message'])
        #
        # if processed_data["Emotion"]:
        #    stat= StatisticModel(
        #        user_id=user.id,
        #        date_YMD=now[:8]
        #    )
        #    stat.save_to_db()
        #
        # if processed_data["Flag"]:
        #     user.num_of_counselling += 1
        #
        # user.save_to_db()
        # print(processed_data)
        # if not processed_data["Type"] == 'General':
        #     eventlet.sleep(1)
        # for content in processed_data["System_Corpus"] :
        #     now = datetime.now(timezone('Asia/Seoul')).strftime("%Y%m%d%H%M%S")
        #     emit("RECEIVE_MESSAGE", {"response": content,"day":now[:8],'time':now[8:]})
        #     chat = ChatModel(
        #         user_id=user.id,
        #         date_YMD=now[:8],
        #         date_YMDHMS=now,
        #         direction='BOT',
        #         utterance=content
        #     )
        #     chat.save_to_db()
        #     eventlet.sleep(3)

