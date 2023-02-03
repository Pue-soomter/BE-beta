from flask import session, request
from flask_restx import Resource, reqparse
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)
from models import day_format, datetime_format, UserModel, ChatModel, MessageTemplate
from datetime import datetime
from pytz import timezone
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session,sessionmaker
#from app import api

cached={}

engine = create_engine("sqlite:///scenarios",connect_args={'check_same_thread': False})
metadata_obj = MetaData()

some_table = Table("도입1", metadata_obj, autoload_with=engine)
conn = engine.connect()

def save_chat(user_id,sender,message):
    now = datetime.now(timezone('Asia/Seoul'))
    chat = ChatModel(
        _user_id=user_id,
        _date=now,
        _chatter=sender,
        _utterance=message
    )
    chat.save_to_db()

class HookMessage(Resource):

    # s = select([some_table]).where(some_table.columns.name == 'Jane Doe')
    # result = conn.execute(s).first()
    # print(result)

    _parser = reqparse.RequestParser()
    _parser.add_argument('data', type=dict, required=True)
    _parser.add_argument('additional',type=list,required=True)
    @classmethod
    def load_row(cls,_table,_cursor):
        some_table = Table(_table, metadata_obj, autoload_with=engine)
        s = select([some_table]).where(some_table.columns.구분 ==_cursor)
        return conn.execute(s).first()

    # #message
    # ->{
    #     'key'->
    #     'cursor' ->
    #     'table' ->
    #     'utterance' ->
    #     'postback':{
    #           'cursor':
    #           'table':
    #           'sentence:
    #       }
    # }

    #additional (list)
    #type ->
    #data ->

    # @api.doc(
    #     security='JWT',
    #     description="챗봇의 다음 메세지를 받습니다.",
    # )
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()

        raw_data = HookMessage._parser.parse_args()
        msg = raw_data['data']
        postback = msg['postback']
        additional=raw_data['additional']

        message_template = MessageTemplate("ok")
        if not msg["table"] == "open":
            save_chat(user_id,'user',msg['utterance'])
        else :
            cached[user_id]=dict()
            message_template.add_message("안녕, 오늘 기분은 어때?",user_id,save_chat)
            message_template.add_message("너의 기분을 아래에서 표시해줘!",user_id,save_chat)
            message_template.add_traffic_lights()
            return message_template.json()

        try:
            cached[user_id][msg["cursor"]]=msg["key"]
        except KeyError:
            cached[user_id]=dict()
            cached[user_id][msg["cursor"]] = msg["key"]

        row = HookMessage.load_row(postback['table'],postback['cursor'])

        if not row['문장함수적용'] is None:
            if row['문장함수적용'] == '단일형':
                if row[postback['sentence']+'개별함수'] is None:
                    message_template.add_message(row[postback['sentence']],user_id,save_chat)
                else :
                    if row[postback['sentence']+'개별함수'] == "문구변경":
                        real_sentence = row[postback['sentence']]
                        l_index = real_sentence.find('[')
                        r_index = real_sentence.rfind(']')
                        raw_str_dict = "{" + real_sentence[l_index + 1:r_index] + "}"
                        str_dict = eval(raw_str_dict)
                        message_template.add_message(real_sentence[:l_index] + str_dict[cached[user_id][row[postback['sentence']+'함수파라미터']]] +
                              real_sentence[r_index + 1:],user_id,save_chat)
            else :
                #추후 추가 예정
                message_template.add_message(row[postback['sentence']], user_id, save_chat)
        else :
            for i in range(int(row['문장갯수'])):
                message_template.add_message(row[f'문장{i+1}'], user_id, save_chat)

        if row[postback['sentence']+"이동"] is None:
            cursor = "유저"+postback['cursor'][2:]
        else:
            raw_move = row[postback['sentence'] + "이동"]
            raw_move = raw_move.split('-')
            cursor = raw_move[0]
            if len(raw_move) > 1:
                sentence = raw_move[1]

        user_row = HookMessage.load_row(postback['table'], cursor)
        payloads=[]
        for i in range(int(user_row['문장갯수'])):
            payload=[i+1,cursor,postback['table']]
            if not user_row[f"문장{i+1}개별함수"] is None:
                if user_row[f"문장{i+1}개별함수"] == '문구변경':
                    real_sentence = user_row[f"문장{i+1}"]
                    l_index = real_sentence.find('[')
                    r_index = real_sentence.find(']')
                    raw_str_dict = real_sentence[l_index+1:r_index]
                    raw_str_dict = raw_str_dict.split(':')
                    raw_str_dict[1] = '"'+raw_str_dict[1]+'"'
                    raw_str_dict = "{" + raw_str_dict[0]+':'+raw_str_dict[1] + "}"
                    str_dict = eval(raw_str_dict)
                    try:
                        payload.append(real_sentence[:l_index] + str_dict[
                            cached[user_id][user_row[f"문장{i+1}함수파라미터"]]] + real_sentence[r_index + 1:])
                    except KeyError:
                        payload.append(real_sentence[:l_index])
                else :
                    payload.append(user_row[f'문장{i+1}'])
            else:
                payload.append(user_row[f'문장{i+1}'])
            if user_row["문장함수적용"] is None or user_row["문장함수적용"]=="선택형":
                if user_row[f'문장{i+1}이동'] is None:
                    payload.append(f"챗봇{int(cursor[2:])+1}")
                    payload.append(postback['table'])
                    payload.append("문장1")
                else :
                    raw_move = user_row[f'문장{i+1}이동']
                    if raw_move.startswith('%'):
                        try:
                            payload.append(f"챗봇{int(cursor[2:])+1}")
                        except ValueError:
                            payload.append("챗봇1")
                        payload.append(raw_move[1:-1].strip() + '1')
                        payload.append("문장1")
                    else:
                        raw_move = raw_move.split('-')
                        number_cursor = raw_move[0]
                        payload.append(number_cursor)
                        payload.append(postback['table'])
                        if len(raw_move) > 1:
                            sentence_cursor = raw_move[1]
                            payload.append(sentence_cursor)
                        else :
                            payload.append("문장1")
            else:
                if user_row["문장함수적용"] == '번호벌매칭':
                    number_cursor = user_row['함수파라미터']
                    payload.append(number_cursor)
                    payload.append(postback['table'])
                    sentence_cursor = f'문장{i+1}'
                    payload.append(sentence_cursor)

            payloads.append(payload)

        message_template.add_button(payloads)
        return message_template.json()

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

