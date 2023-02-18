from flask import session, request
from flask_restx import Resource, reqparse
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)
from models import day_format, datetime_format, UserModel, ChatModel, MessageTemplate
from datetime import datetime
from pytz import timezone
from sqlalchemy import create_engine, Table, MetaData, select, text
#from packages.AI.models import *
#from app import api

import xml.etree.ElementTree as elemTree
from warnings import warn

tree = elemTree.parse('docs/keys.xml')
secretkey = tree.find('string[@name="secret_key"]').text

#weight_path = os.environ['CHATBOT_ROOT'] + r'/resources/weights/Abuse/'
#model = AbuseModel(weight_path)

db_info = {
    "user": tree.find('string[@name="DB_USER"]').text,
    "password": tree.find('string[@name="DB_PASS"]').text,
    "host": tree.find('string[@name="DB_HOST"]').text,
    "port": tree.find('string[@name="DB_PORT"]').text,
    "database": tree.find('string[@name="DB_SCNAME"]').text
}

#이전 대답 저장
cached={}

#현재 커서를 저장함
cursor_cached={}

#문구변경 테이블, beta, 상담사 매칭 등 특수 테이블로의 이동
def special_table():
    """
    TODO

    """
def change_speical(_name,_message_template,_sentence,user_id):
    l_index = _sentence.find(f"%{_name}")
    r_index = _sentence.find(" ", l_index) + 1
    _message_template.add_message(_sentence[:l_index], user_id, save_chat)
    _message_template.add_special(_name,f"{_name}1")
    cached[user_id][f"{_name}1"] = _sentence[r_index:]
    return f"{_name}1"

#리스트 함수
def change_list(_message_template,_sentence,user_id):
    #리스트 위치 찾기
    l_index = _sentence.find("%list")
    r_index = _sentence.find(" ",l_index)+1
    #리스트 종류 찾기
    _,name,key = _sentence[l_index:r_index-1].split('-')

    _message_template.add_message(_sentence[:l_index],user_id,save_chat)
    _message_template.add_list(name,"리스트-"+name+key)
    cached[user_id][name+key]=_sentence[r_index:]
    return "리스트-"+name+key
    #_message_template.add_message(_sentence[r_index:],user_id,save_chat)

#문구변경 함수
#[2&3:""//!2:""]
def change_sentence(_row,_sentence_cursor,user_id):
    ret_sentence = _row[_sentence_cursor]
    l_index = ret_sentence.find('[')
    r_index = ret_sentence.rfind(']')
    raw_target_sentence = ret_sentence[l_index + 1:r_index]
    #1.split
    targets = raw_target_sentence.split("//")
    #2.loop
    result=""
    for target in targets:
        #3.keys-sentence split
        raw_keys,sample_result = target.split(":")
        sample_result = sample_result[1:-1]
        if raw_keys.startswith('!'):
            #4.key split
            keys = raw_keys[1:].split('&')
            #5.find key
            if not cached[user_id][_row[_sentence_cursor + '함수파라미터']] in keys :
                result = sample_result
        else :
            # 4.key split
            keys = raw_keys.split('&')
            # 5.find key
            if cached[user_id][_row[_sentence_cursor + '함수파라미터']] in keys:
                result = sample_result

    return ret_sentence[:l_index] + result + ret_sentence[r_index + 1:]


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
    #, connect_args={'check_same_thread': False}
    engine = create_engine(f"mysql://{db_info['user']}:{db_info['password']}@{db_info['host']}:{db_info['port']}/{db_info['database']}")
    metadata_obj = MetaData()

    some_table = Table("도입1", metadata_obj, autoload_with=engine)
    conn = engine.connect()

    _parser = reqparse.RequestParser()
    _parser.add_argument('postback', type=dict, required=True)
    _parser.add_argument('additional',type=list,required=True)

    @classmethod
    def load_row(cls,_table,_cursor):
        _cursor = f"'{_cursor}'"
        some_table = Table(_table, cls.metadata_obj, autoload_with=cls.engine)
        #s = select([some_table]).where(some_table.columns.구분 ==_cursor)
        #s = select([some_table]).where(text("'some_table.구분'= :gubun")== _cursor)
        s = f"SELECT * FROM {some_table} WHERE 구분 = {_cursor}"
        return cls.conn.execute(s).first()

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()

        raw_data = HookMessage._parser.parse_args()
        msg = raw_data['postback']
        additional=raw_data['additional']

        """
            메세지 여부 판독하기
            1. 첫메시지 인가?
            2. 리스트 메시지인가?
            3. 그 외인가?
        """
        is_already_set_message=False
        is_already_set_user_cursor=False
        message_template = MessageTemplate("ok")
        if msg["key"] == "open":
            cached[user_id] = dict()
            cursor_cached[user_id] = dict()
            message_template.add_message("안녕, 오늘 기분은 어때?", user_id, save_chat)
            message_template.add_message("너의 기분을 아래에서 표시해줘!", user_id, save_chat)
            message_template.add_traffic_lights(cursor_cached[user_id])
            return message_template.json()
        elif msg["key"].startswith("리스트") :
            _,key = msg["key"].split('-')
            message_template.add_message(cached[user_id][key], user_id, save_chat)
            cached[user_id][key] = msg["list"]
            is_already_set_message = True
        elif msg["key"].startswith("selftalk"):
            message_template.add_message(cached[user_id][msg["key"]], user_id, save_chat)
            is_already_set_message = True
        elif msg["key"].startswith("beta"):
            message_template.add_message(cached[user_id][msg["key"]], user_id, save_chat)
            is_already_set_message = True
        elif msg["key"].startswith("상담사매칭"):
            message_template.add_message(cached[user_id][msg["key"]], user_id, save_chat)
            is_already_set_message = True
        else :
            save_chat(user_id, 'user', msg['utterance'])


        """
           커서따오기 
           원리 설명
           0. 이전 대화가 리스트형, 이 아니었다면
           1. cursor_cached에는 먼저 user_id로 딕셔너리로 저장됨
           2. 그 내부에는 응답 key에 대한 table-gubun-sentence가 저장되어 있음. 
        """
        tag_cursor = cursor_cached[user_id][msg["key"]].strip().split('-')
        table_cursor = tag_cursor[0]
        gubun_cursor = tag_cursor[1]
        sentence_cursor = tag_cursor[2]
        row = HookMessage.load_row(table_cursor, gubun_cursor)

        if not is_already_set_message:
            cached[user_id][cursor_cached[user_id]["current"]]=msg["key"]
        """
        !!current 추후 변경 필요!!
        챗봇부분 문장함수적용 처리하기
        """
        if row['문장함수적용'] == "이동하기":
            raw_user_cursor = row['함수파라미터']
            is_already_set_user_cursor = True
        elif row['문장함수적용'] == "번호별 매칭":
            raw_user_cursor = '-'.join([row['함수파라미터'],sentence_cursor])
            is_already_set_user_cursor = True
        else:
            ##일단 경고
            if not row['문장함수적용'] == "단일형" and not row['문장함수적용'] is None:
                warn(f"table_cursor:{table_cursor} gubun_cursor:{gubun_cursor} sentence_cursor:{sentence_cursor} \n"
                     f"챗봇의 문장함수적용({row['문장함수적용']})이 잘못되었습니다.")


        """
            챗봇부분 개별함수 적용
        """
        if not is_already_set_message:
            if row[sentence_cursor+"개별함수"] == "문구변경":
                message_template.add_message(
                    change_sentence(row,sentence_cursor,user_id), user_id, save_chat)
            elif row[sentence_cursor+"개별함수"] == "리스트":
                list_key = change_list(message_template,row[sentence_cursor],user_id)
                cursor_cached[user_id][list_key]='-'.join(tag_cursor)
                return message_template.json()
            else :
                if "%selftalk" in row[sentence_cursor]:
                    selftalk_name = change_speical("selftalk", message_template,row[sentence_cursor],user_id)
                    cursor_cached[user_id][selftalk_name]='-'.join(tag_cursor)
                    return message_template.json()
                elif "%상담사매칭" in row[sentence_cursor]:
                    selftalk_name = change_speical("상담사매칭", message_template,row[sentence_cursor],user_id)
                    cursor_cached[user_id][selftalk_name]='-'.join(tag_cursor)
                    return message_template.json()
                elif "%beta" in row[sentence_cursor]:
                    selftalk_name = change_speical("beta", message_template,row[sentence_cursor],user_id)
                    cursor_cached[user_id][selftalk_name]='-'.join(tag_cursor)
                    return message_template.json()
                else:
                    message_template.add_message(row[sentence_cursor], user_id, save_chat)

        """
            유저 구분 커서 정하기
        """
        if row[sentence_cursor + "이동"] is None:
            if not is_already_set_user_cursor:
                raw_user_cursor = "유저" + sentence_cursor[2:]
        else :
            raw_user_cursor = row[sentence_cursor + "이동"]
        user_table = table_cursor
        user_only_one = False
        user_sentence = "문장1"
        if raw_user_cursor.startswith("%"):
            user_tag = raw_user_cursor[1:-1].strip().split("-")
            user_table = user_tag[0]
            if len(user_tag)>1 :
                user_gubun = user_tag[1]
            if len(user_tag)>2:
                user_sentence = user_tag[2]
                user_only_one = True
        else :
            user_tag = raw_user_cursor.split("-")
            user_gubun = user_tag[0]
            if len(user_tag) > 1:
                user_sentence = user_tag[1]
                user_only_one = True

        """
            유저대답 따오기
        """

        special_table()
        user_row = HookMessage.load_row(user_table, user_gubun)
        cursor_cached[user_id]["current"] = user_gubun

        """
         def add_button(self,payloads):
        _temp = {
            "type": "button",
            "payload": []
        }
        for content in payloads:
            _content_temp={}
            _content_temp["utterance"] = content["utterance"]
            _content_temp['postback']={}
            _content_temp['postback']["key"] = content["key"]
            _content_temp['postback']["utterance"] = content["utterance"]
            _temp["payload"].append(_content_temp)

        self.data.append(_temp)
        
        """
        """
            한문장만 출력해도 될때
        """
        if user_only_one :
            if user_row["문장함수적용"] == "번호별매칭":
                cursor_cached[user_id]["1"]=user_table+'-'+user_row['함수파라미터']+'-'+user_sentence
            elif user_row["문장함수적용"] == "이동하기":
                cursor_cached[user_id]["1"] = user_table + '-' + user_row['함수파라미터'] + '-' + user_sentence
            else:
                cursor_cached[user_id]["1"] = user_table+'-'+user_row[user_sentence + "이동"]

            if user_row[user_sentence+"개별함수"] == "문구변경":
                _content_temp = {
                    "type":"button",
                    "utterance":change_sentence(user_row,user_sentence,user_id),
                    "key":"1"
                }
                message_template.add_postback([_content_temp])


            elif user_row[user_sentence+"개별함수"] == "서술형":
                _content_temp = {
                    "type": "desc",
                    "utterance": "",
                    "key": "1"
                }
                message_template.add_postback([_content_temp])
            else :
                _content_temp = {
                    "type": "button",
                    "utterance": user_row[user_sentence],
                    "key": "1"
                }
                message_template.add_postback([_content_temp])
            return message_template.json()

        """
            개별함수 선처리(문장넣기)
        """
        payloads=[]
        for i in range(int(user_row['문장갯수'])):
            payloads.append(dict())
            payloads[-1]["key"] = str(i + 1)
            if user_row[f"문장{i+1}개별함수"] == "문구변경":
                raw_sentence = change_sentence(user_row,f"문장{i+1}",user_id).strip()
                payloads[-1]["utterance"] = raw_sentence
                payloads[-1]["type"]="button"
            elif user_row[f"문장{i+1}개별함수"] == "서술형":
                payloads[-1]["utterance"] = ""
                payloads[-1]["type"]="desc"
                payloads=[payloads[-1]]+payloads[:-1]
            else :
                payloads[i]["utterance"] = user_row[f"문장{i+1}"]
                payloads[-1]["type"] = "button"

        """
            커서처리
        """
        if user_row["문장함수적용"] == "번호별매칭":
            for content in payloads:
                cursor_cached[user_id][content["key"]] = f'{user_table}-{user_row["함수파라미터"]}-문장{content["key"]}'
            message_template.add_postback(payloads)
        elif user_row["문장함수적용"] == "서술선택형":
            payloads[0]["type"]="desc"
            payloads[0]["utterance"]=""
            for i,content in enumerate(payloads):
                if not user_row[f"문장{i+1}이동"] is None:
                    cursor_cached[user_id][content["key"]] = f'{user_table}-{user_row[f"문장{i+1}이동"]}'
                else:
                    warn(f"table_cursor:{user_table} gubun_cursor:{user_gubun} sentence_cursor:{user_sentence} \n"
                         f"유저의 문장이동이 존재하지 않아 잘못된 위치를 참조할 수 있습니다.")
                    cursor_cached[user_id][content["key"]] = f'챗봇{int(user_gubun) + 1}'
            message_template.add_postback(payloads)
        elif user_row["문장함수적용"] == "이동하기":
            for content in payloads:
                cursor_cached[user_id][content["key"]] = f'{user_table}-{user_row["함수파라미터"]}'
            message_template.add_postback(payloads)
        else :
            for i,content in enumerate(payloads):
                if not user_row[f"문장{i+1}이동"] is None:
                    cursor_cached[user_id][content["key"]] = f'{user_table}-{user_row[f"문장{i+1}이동"]}'
                else :
                    warn(f"table_cursor:{user_table} gubun_cursor:{user_gubun} sentence_cursor:{user_sentence} \n"
                         f"유저의 문장이동이 존재하지 않아 잘못된 위치를 참조할 수 있습니다.")
                    cursor_cached[user_id][content["key"]] = f'챗봇{int(user_gubun)+1}'
            message_template.add_postback(payloads)
        return message_template.json()


