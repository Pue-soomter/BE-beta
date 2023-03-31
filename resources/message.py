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
from datetime import datetime, timedelta
from pytz import timezone

import xml.etree.ElementTree as elemTree
from warnings import warn


"""
    최종수정: 2023-03-31
    관리자 : 이병찬
    
    내용:
        1. 현재 아래와 같은 문제들이 있습니다.
        1-1. 00목록 작성, selftalk, 서술형 등 유저가 직접 입력해야 하는 부분에 대해서는 chat DB에 저장하지 않습니다.


"""


tree = elemTree.parse('docs/keys.xml')
secretkey = tree.find('string[@name="secret_key"]').text

db_info = {
    "user": tree.find('string[@name="DB_USER"]').text,
    "password": tree.find('string[@name="DB_PASS"]').text,
    "host": tree.find('string[@name="DB_HOST"]').text,
    "port": tree.find('string[@name="DB_PORT"]').text,
    "database": tree.find('string[@name="DB_SCNAME"]').text
}

cached={}
"""
    1. 유저의 대답을 저장합니다. 이는 "문구변경"에서 주로 활용됩니다.
    2. 유저의 마지막 접속시간(lasttime)을 저장합니다.
    3. list나 selftalk, beta 등에서 처리 후 뒤에 문장들을 임시로 저장해 놓는다.
     {
        "유저2":"1",
        "유저10":"3",
        "lasttime":datetime(~~~),
        "리스트-실천-1":"실천목록을 작성해본 소감이 어때?"
    }
"""

cursor_cached={}
"""
    1. 방금 유저에게 건넨 선택지에 따른 문장이동(이하 커서)을 저장합니다.
    2. 선택지를 보내면 아래와 같은 예시로 저장됩니다.
    {
        "1":"%대인관계-챗봇10-문장2",
        "2":"%공통마무리-챗봇99-문장1"
    }
    3. FE에서 key값으로 보낸 값(예시로 1이라 하면)에 따라서 해당 커서로 이동합니다.(예시로 %대인관계-챗봇10-문장2)
"""

utterance_cached={}
"""
    1. 방금 유저에게 건넨 선택지에 따른 문장의 내용을 저장합니다.
    2. 선택지를 보내면 아래와 같은 예시로 저장됩니다.
    {
        "1":"오늘 밥은 계란말이였어",
        "2":"오늘 너무 더워",
    }
    3. FE에서 Key값으로 보낸 값(예시로 2이라 하면)에 따라서 해당 문장이 db에 저장됩니다.(예시로 "오늘 너무 더워:가 저장된다.)

"""

def proc_params(param,user_table,user_sentence=None):
    """
        목적:
            1.문장0이동, 함수파라미터에 저장된 값을 읽어서
            2. 커서 이동과 그에따른 cursor_cached에 저장될 값을 처리합니다.


        파라미터:
            param -> row에서 함수파라미터 컬럼값, 문장N이동, 문장N함수파라미터
            user_table -> "현재 처리하고 있는" 유저 선택지가 있는 테이블명
            user_sentence -> 문장까지 지정해줘야 하는 경우(특별케이스)

        결과:
            커서가 반환된다.
            "%{테이블명}-{구분명}" 또는 "%{테이블명}-{구분명}-{문장}"

    """

    if param.startswith("%"): #테이블까지 이동해야 하는 경우
        # 1을 붙이기 위해 처리하기
        # 테이블까지 이동하는 경우, param내부의 값이 아래 두가지입니다.
        # (1) 테이블 명만 명시된 경우 -> load_table_and_first를 이후에 호출하여 테이블에서 가장 첫번째 row를 가져온다.
        # (2) 테이블명 + 구분명이 명시된 경우 -> 가장 이상적임
        raw_cursor = param[1:-1].strip().split('-')
        raw_cursor[0] += '1' #테이블 뒤에는 항상 1이 붙어있으므로 1을 붙인다. (예: 대인관계1, 공통마무리1)
        raw_cursor = '-'.join(raw_cursor) #1을 처리했으니 다시 합치기
    else: #테이블 이동은 필요없는 경우
        if user_sentence:
            raw_cursor = user_table + '-' + param + '-' + user_sentence
        else :
            raw_cursor = user_table + '-' + param
    return raw_cursor

#특수 문장들 바꾸기 ex) beta
def change_speical(_name,_message_template,_sentence,user_id):
    """
            목적:
                1. list-~~를 제외한 특수 문장들(selftalk, beta, 상담사 를 처리하기 위함

            파라미터:
                _name -> 특수문장의 종류(selftalk, beta, 상담사)
                _message_template -> FE에 보내기 위해 작성중인 메세지 템플릿
                _sentence -> 현재 처리할 문장
                user_id -> 00을 nickname으로 바꾸기 위해 user_id를 가져옴

            결과:
                커서가 반환된다.
                "selftalk" 또는 "beta", "상담사"

    """

    #아래 두문장은 %를 찾아 특수문장의 종류를 파악하기 위함임
    l_index = _sentence.find(f"%{_name}")
    r_index = _sentence.find(" ", l_index) + 1

    # %가 발견되기 직전까지의 문장은 FE에 보낼 것임
    _message_template.add_message(_sentence[:l_index], user_id, save_chat)


    if _name == 'selftalk': #selftalk은 list과 같이 처리됨
        _message_template.add_list(_name,f"{_name}1",user_id)
    elif _name == 'beta':
        _message_template.add_req_special(_name,f"{_name}1")

    #아래는 cached에 남은 문장을 임시로 저장하기 위함임.
    if r_index <= 0: #예외처리, 남은 문장이 없는 경우
        cached[user_id][f"{_name}1"] = ""
    else :
        cached[user_id][f"{_name}1"] = _sentence[r_index:].strip()

    return f"{_name}1"

#리스트 함수
def change_list(_message_template,_sentence,user_id):
    """
            목적:
                1. list-~~ 형식의 실천목록 작성을 처리하기 위함임.

            파라미터:
                _message_template -> FE에 보내기 위해 작성중인 메세지 템플릿
                _sentence -> 현재 처리할 문장
                user_id -> 00을 nickname으로 바꾸기 위해 user_id를 가져옴

            결과:
                커서가 반환된다.
                "리스트-실천-1", "리스트-이별사유-1"

        """

    #리스트 위치 찾기
    l_index = _sentence.find("%list")
    r_index = _sentence.find(" ",l_index)+1

    #리스트 종류 찾기
    _,name,key = _sentence[l_index:r_index-1].split('-')

    _message_template.add_message(_sentence[:l_index],user_id,save_chat)
    _message_template.add_list(name,"리스트-"+name+key,user_id)

    cached[user_id]["리스트-"+name+key]=_sentence[r_index:] #이후 문장 저장하기임

    return "리스트-"+name+key

#문구변경 함수

def change_sentence(_row,_sentence_cursor,user_id):
    """
            목적:
                1. 문구변경 함수를 처리하기 위함

            파라미터:
                _row -> 처리하고 있는 행
                (혹시나 의문을 가질 수 있어서 말씀드립니다.... 단순 문장이 아닌 row를 받은 이유는 밑에보면 row에 들어있는 함수 파라미터를 확인해야 하기 때문입니다.)
                (위 말이 무슨말인지 모르셔도 전혀 무방합니다.)
                _sentence_cursor -> 어떤 문장에 대한 문구변경 처리인지 (문장1, 문장2 등등..)
                user_id -> 00을 nickname으로 바꾸기 위해 user_id를 가져옴

            결과:
                커서가 반환된다.
                "리스트-실천-1", "리스트-이별사유-1"

        """
    #문장 따온 후 문구변경 구간에 대해 slice
    ret_sentence = _row[_sentence_cursor]
    l_index = ret_sentence.find('[')
    r_index = ret_sentence.rfind(']')
    if r_index == -1:
        r_index = len(ret_sentence)
    raw_target_sentence = ret_sentence[l_index + 1:r_index]


    #1.split
    targets = raw_target_sentence.split("//")
    #ex ["1:1번문장입니다.", "2:2번문장입니다.",...]

    #2.각 문구변경 문장 대해 처리하기
    result=""
    for target in targets:

        #3.키와 문장 나누기
        raw_keys,sample_result = target.split(":")
        raw_keys = raw_keys.strip()
        sample_result = sample_result.strip()

        # 예외처리, 예를 들어 함수파라미터에서 유저1이라 줬는데 유저1을 거치지 않은 경우
        # -> 그냥 아무렇게나 출력하기(지금 같은 경우는 마지막거가 출력되겠죠?)
        if not (_row[_sentence_cursor + '함수파라미터'] in cached[user_id].keys()):
            result = sample_result
        else:
            if raw_keys.startswith('!'): #!는 key들이 없을때
                #4.key split
                keys = raw_keys[1:].split('&') #&로 묶여서 key를 2개 이상 봐야할수도 있으므로
                #이 결과 keys = ['1','2'] 이런식으로 저장됨


                #5.!니까 not을 붙여서 "cached에 없다면"으로...
                if not cached[user_id][_row[_sentence_cursor + '함수파라미터']] in keys :
                    result = sample_result
            else :
                # 4.key split

                keys = raw_keys.split('&')
                # 5.find key
                # 5. "cached에 있다면"으로...
                if cached[user_id][_row[_sentence_cursor + '함수파라미터']] in keys:
                    result = sample_result
    try:
        return ret_sentence[:l_index] + result + ret_sentence[r_index + 1:]
    except Exception :
        return None



def save_chat(user_id,sender,message):
    now = datetime.now(timezone('Asia/Seoul'))
    chat = ChatModel(
        _user_id=user_id,
        _date=now,
        _chatter=sender,
        _utterance=message
    )
    chat.save_to_db()

class UserMessage(Resource):
    """
        FE에서 메세지만 보내주는 API 만들어 달라해서 만들어 드렸습니다...
        언제 호출되는지, 어떻게 활용되는지는 FE분과 이야기 하시면..!



    """
    _parser = reqparse.RequestParser()
    _parser.add_argument('postback', type=str, required=True)
    _parser.add_argument('list', type=list, required=False)
    _parser.add_argument('utterance', type=str, required=False)

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()


        raw_data = UserMessage._parser.parse_args()
        msg = dict()

        #FE에서 보낸 postback 값 저장하기
        msg["key"] = raw_data['postback']


        #밑에는 추후 추가를 위해 남겨놓앗으니 무시하셔도 됩니다.
        try:
            msg["list"] = raw_data['list']
        except:
            pass

        try:
            msg["utterance"] = raw_data['utterance']
        except:
            pass

        #target은 FE에게 보낼 유저 선택지의 내용입니다.(ex: "응, 나 우울해", "자꾸 생각나서 힘들어" 등)
        try:
            target = utterance_cached[user_id][msg["key"]]
        except KeyError:
            return {
                       "message": "none"
                   }, 204

        #
        if (target is None or target == "") and not (msg["utterance"] is None):
            target = msg["utterance"]

        return {
            "message":"ok",
            "data":{
                "chatter":"user",
                "utterance":target
            }
        }


class HookMessage(Resource):
    engine = create_engine(f"mysql://{db_info['user']}:{db_info['password']}@{db_info['host']}:{db_info['port']}/{db_info['database']}")
    metadata_obj = MetaData()

    some_table = Table("도입1", metadata_obj, autoload_with=engine)
    conn = engine.connect()

    _parser = reqparse.RequestParser()
    _parser.add_argument('postback', type=str, required=True)
    _parser.add_argument('list', type=list, required=False)
    _parser.add_argument('utterance', type=str, required=False)

    @classmethod
    def load_row(cls,_table,_cursor):
        """

        하나의 행(이하 row)를 불러옵니다. 구분명이 필요합니다.

        """
        _cursor = f"'{_cursor}'"
        some_table = Table(_table, cls.metadata_obj, autoload_with=cls.engine)
        s = text(f"SELECT * FROM {some_table} WHERE 구분 = {_cursor}")
        return cls.conn.execute(s).first()

    @classmethod
    def load_next_row(cls, _table, index):
        """

                에러 발생을 최대한 회피하기 위해(...) 문장 이동 또는 함수 파라미터에 의한 커서가 없는 경우 호출되며 다음 row를 가져 옵니다.

                """
        some_table = Table(_table, cls.metadata_obj, autoload_with=cls.engine)
        s = select([some_table]).where(some_table.columns.index >index)

        return cls.conn.execute(s).first()

    @classmethod
    def load_table_and_first(cls, _table):
        """
            커서가 테이블명만 있는 경우가장 맨 처음 row를 가져옵니다. (에러 회피를 위해..)

        """
        some_table = Table(_table, cls.metadata_obj, autoload_with=cls.engine)
        s = text(f"SELECT * FROM {some_table} LIMIT 1")
        return cls.conn.execute(s).first()

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        message_template = MessageTemplate("ok")


        #첫 접속시 캐시 생성
        if not user_id in cached.keys():
            cached[user_id] = dict()
        if not user_id in cursor_cached.keys():
            cursor_cached[user_id] = dict()
        if not user_id in utterance_cached.keys():
            utterance_cached[user_id] = dict()

        #이것이 True이면 신호등 메세지가 보내집니다.
        is_traffic_light = False

        #오늘 처음 접속여부 파악 및 traffic_ligt 플래그 변경
        today = datetime.now(timezone('Asia/Seoul'))
        if 'lasttime' in cached[user_id].keys():
            diff = today - cached[user_id]['lasttime']
            if today.strftime(day_format) != cached[user_id]['lasttime'].strftime(day_format) :
                message_template.add_time(today.strftime(datetime_format))
            if (diff.seconds/3600) > 1 :
                is_traffic_light = True
        else :
            message_template.add_time(today.strftime(datetime_format))
            is_traffic_light = True

        #오늘 날짜를 저장합니다. 따라서 다음접속때는 traffic_light 플래그 설정에 활용됩니다/
        cached[user_id]['lasttime'] = today


        raw_data = HookMessage._parser.parse_args()
        msg = dict()

        #FE에서 보낸 값을 저장합니다.
        msg["key"] = raw_data['postback']

        #아래 2개의 try는 추후 활용을 위해 남겨놨습니다. 무시하면 됩니다.
        try:
            msg["list"] = raw_data['list']
        except :
            pass

        try:
            msg["utterance"] = raw_data['utterance']
        except:
            pass

        """
        ########################################################################
            메세지 여부 판독하기
            1. FE에서 보낸 메세지의 종류를 파악합니다.
            2. 첫메세지인가
            3. 리스트 메세지인가
            4. special 메세지인가
        """
        is_already_set_message=False
        is_already_set_user_cursor=False

        next_sentence="dummy"


        #첫 채팅을 시작할때는 open으로 받습니다.
        if msg["key"] == "open":
            if is_traffic_light :
                message_template.add_message("안녕, 오늘 기분은 어때?", user_id, save_chat)
                message_template.add_message("너의 기분을 아래에서 표시해줘!", user_id, save_chat)
                message_template.add_traffic_lights(cursor_cached[user_id],utterance_cached[user_id])
                return message_template.json()
            else :
                #traffic light가 아니라면 바로 다음 문장으로 간다.
                cursor_cached[user_id][msg["key"]] = "도입1-챗봇도입-문장2"

            #current가 필요한 이유는 cached에 저장할 key를 찾기 위함입니다.
            # (즉, 유저1에서 1을 선택했을때 cached에 "유저1":"1"로 저장하기 위해서는
            # cached[user_id][cursor_cached[user_id]["current"]]=1 이라고 저장해야함(추후에 나옴))
            cursor_cached[user_id]["current"]="유저시작"

        elif msg["key"].startswith("리스트") :
            _,key = msg["key"].split('-')

            #리스트(목록작성)의 경우 change_list(176번줄)에서 보았듯이, cached에 이후 문장이 저장되어있음
            #따라서 테이블로 부터 별도로 출력할 문장을 따올 필요가 없기 때문에 플래그 설정과 더불어 문장을 가져온다.
            #이는 밑의 special 함수들도 마찬가지
            next_sentence = cached[user_id][msg["key"]]
            is_already_set_message = True

        elif msg["key"].startswith("selftalk"):
            next_sentence=cached[user_id][msg["key"]]

            is_already_set_message = True
        elif msg["key"].startswith("beta"):
            next_sentence = cached[user_id][msg["key"]]
            is_already_set_message = True
        elif msg["key"].startswith("상담사"):
            save_chat(user_id, 'user', utterance_cached[user_id][msg["key"]])
            message_template.add_req_special("상담사매칭","open")
            is_already_set_message = True
            return message_template.json()
        else :
            #사용자가 선택한 문장을 DB에 저장하기, 지금같은 경우 서술형이라면 None으로 오기 때문에 예외로 처리해주었습니다.
            try:
                target = utterance_cached[user_id][msg["key"]]

                if (target is None or target == "") and not (msg["utterance"] is None):
                    target = msg["utterance"]

                save_chat(user_id, 'user', target)
            except KeyError:
                target = msg["utterance"]

                save_chat(user_id, 'user', target)


        """
           커서따오기 
           tag_cursor는 cursor_cached에 있는 커서를 저장합니다.  tag_cursor = cursor_cached[user_id][msg["key"]]
           그리고 split을 하면 1개인지, 2개인지, 3개인지에 따라서 테이블만 있는지, 구분명까지 있는지, 문장까지 있는지를 확인할 수 있습니다.
        """

        tag_cursor = cursor_cached[user_id][msg["key"]].strip().split('-')
        print(tag_cursor)
        table_cursor = tag_cursor[0]
        if len(tag_cursor)==1:
            gubun_cursor =  HookMessage.load_table_and_first(table_cursor)["구분"]
            sentence_cursor = "문장1"
        elif len(tag_cursor)==2:
            gubun_cursor = tag_cursor[1]
            sentence_cursor = "문장1"
        else:
            gubun_cursor = tag_cursor[1]
            sentence_cursor = tag_cursor[2]


        """
        챗봇 문장 따오기
        tag_cursor로 부터 아래 커서들이 만들어 졌습니다.
        table_cursor -> 문장이 있는 테이블 명
        gubun_cursor -> 테이블의 구분 명
        sentence_cursor -> 문장 명(문장1, 문장2 등...)
        이제 이를 SQL에 query 하여
        "챗봇이 말할 문장"의 row를 따옵니다.
        단, list나 special 함수들은 "챗봇이 말할 문장" 을 이미 next_sentence에 저장된 상태입니다.
        따라서 이는 별도로 처리합니다.
        
        """
        row = HookMessage.load_row(table_cursor, gubun_cursor)


        #유저가 대답한 것을 cached에 저장하는 곳(아까 440번줄에서 말한 부분)
        #미리 정해진 상황이다?(is_already_set_message이 true)-> list나 special이었다 -> 선택지가 아니었다 -> cached에 저장할 필요가 없다.
        #미리 정해지지 않은 상황이다? -> list나 special가 아니었다 -> 선택지가 였다 -> cached에 대답을 저장할 필요가 있다.
        if not is_already_set_message:
            cached[user_id][cursor_cached[user_id]["current"]]=msg["key"]
        """
        챗봇부분 문장함수적용 처리하기
        함수파라미터로 부터 유저커서(후술)이 정해진 경우 is_already_set_user_cursor가 true가 됩니다.
        """
        if row['문장함수적용'] == "이동하기":
            raw_user_cursor = row['함수파라미터']
            is_already_set_user_cursor = True
        elif row['문장함수적용'] == "번호별 매칭":
            #번호별 매칭은 문장번호(문장1,문장2 등...), 즉, sentence_cursor에 맞추면 되므로...
            raw_user_cursor = '-'.join([row['함수파라미터'],sentence_cursor])
            is_already_set_user_cursor = True
        else:
            ##일단 경고, 문장함수 적용에 오타가 있음
            if not row['문장함수적용'] == "단일형" and not row['문장함수적용'] is None:
                warn(f"table_cursor:{table_cursor} gubun_cursor:{gubun_cursor} sentence_cursor:{sentence_cursor} \n"
                     f"챗봇의 문장함수적용({row['문장함수적용']})이 잘못되었습니다.")


        """
            챗봇부분 개별함수 적용과 문장 생성
        """
        """
        1. 리스트가 있으면 다음문장을 utterance cached 다 넣은채로 일단 보냄
        2. 보낸 후에 받은 key로 utterance cached에 있는것을 가져오기
        3. 이 cached에 또 list가 있는지 확인함
        3-1 있으면 1 반복, 기존에 어떻게 key가 되었는지?
        3-2 없으면 원래 동작대로 ㄱ
        """
        # 미리 정해지지 않은 상황이다? -> list나 special가 아니었다 -> 새롭게 query한 row에서 문장을 가져오자
        if not is_already_set_message:

            if row[sentence_cursor+"개별함수"] == "문구변경":
                message_template.add_message(
                    change_sentence(row,sentence_cursor,user_id), user_id, save_chat)
            else :
                #아래는 list, special 함수 처리 과정입니다.
                l_index = row[sentence_cursor].find("%")
                if row[sentence_cursor][l_index:].startswith("%selftalk"):
                    selftalk_name = change_speical("selftalk", message_template, row[sentence_cursor], user_id)
                    cursor_cached[user_id][selftalk_name] = '-'.join(tag_cursor)
                    return message_template.json()
                elif row[sentence_cursor][l_index:].startswith("%beta"):
                    beta_name = change_speical("beta", message_template, row[sentence_cursor], user_id)
                    cursor_cached[user_id][beta_name] = '-'.join(tag_cursor)
                    return message_template.json()
                elif row[sentence_cursor][l_index:].startswith("%list"):
                    list_key = change_list(message_template, row[sentence_cursor], user_id)
                    cursor_cached[user_id][list_key] = '-'.join(tag_cursor)
                    return message_template.json()
                else:
                    message_template.add_message(row[sentence_cursor], user_id, save_chat)
        else : # 미리 정해진 상황이다?(is_already_set_message이 true)-> list나 special이었다 ->
            # 새롭게 query한 row는 무시하고 이전에 저장했던 next_sentence에서 문장을 가져오자.
            if next_sentence != "":
                l_index = next_sentence.find("%")
                if next_sentence[l_index:].startswith("%selftalk"):
                    selftalk_name = change_speical("selftalk", message_template, next_sentence, user_id)
                    cursor_cached[user_id][selftalk_name] = cursor_cached[user_id][msg["key"]]
                    return message_template.json()
                elif next_sentence[l_index:].startswith("%beta"):
                    beta_name = change_speical("beta", message_template, next_sentence, user_id)
                    cursor_cached[user_id][beta_name] = cursor_cached[user_id][msg["key"]]
                    return message_template.json()
                elif next_sentence[l_index:].startswith("%list"):
                    list_key = change_list(message_template,next_sentence, user_id)
                    cursor_cached[user_id][list_key] = cursor_cached[user_id][msg["key"]]
                    return message_template.json()
                else:
                    message_template.add_message(next_sentence, user_id, save_chat)

        """
            여기까지는 챗봇이 말할 문장을 처리하는 과정이었습니다.
            
            아래부터는 이제 유저가 선택해야할 선택지가 어떤것인지를 찾아나가야 합니다.
        """

        #문장이동으로부터(또는 함수파라미터로 부터) 유저 구분에 대한 위치(이하 유저 커서)를 가져옵니다.
        #한편, 함수파라미터로 부터 정해진 경우는 is_already_set_user_cursor이 true가 된 상태입니다.
        if row[sentence_cursor + "이동"] is None:
            if not is_already_set_user_cursor:
                warn("이동이 정해지지 않았습니다! 오류 발생가능!")
                raw_user_cursor = f"유저0"
        else :
            raw_user_cursor = row[sentence_cursor + "이동"]

        #아까 tag_cursor와 비슷하게 user_cursor를 만드는 과정입니다.
        #이때, 위에서 raw_user_cursor가 sentence까지 지정한것이라면 해당 문장만 출력하기(user_only_one)
        #아니라면 해당 유저 커서의 row의 모든 문장을 출력하기 로 나뉩니다.

        user_table = table_cursor
        user_only_one = False
        user_sentence = "문장1"
        print("cursor",raw_user_cursor)
        if raw_user_cursor.startswith("%"):
            user_tag = raw_user_cursor[1:-1].strip().split("-")
            user_table = user_tag[0]+'1'

            #상담사는 특이케이스입니다. 유저 선택지가 없기 때문에...
            if user_table.startswith("상담사"):
                message_template.add_counselor(cursor_cached[user_id],utterance_cached[user_id])
                return message_template.json()

            if len(user_tag)==2 :
                user_gubun = user_tag[1]
            if len(user_tag)==3:
                user_sentence = user_tag[2]
                user_only_one = True
            else :
                user_gubun = HookMessage.load_table_and_first(user_table)["구분"]
        else :
            user_tag = raw_user_cursor.split("-")
            user_gubun = user_tag[0]
            if len(user_tag) > 1:
                user_sentence = user_tag[1]
                user_only_one = True


        #원래는 챗봇-유저-챗봇-유저의 티키타카
        #즉,(FE요청1시점)챗봇-유저, (FE요청2시점)챗봇-유저 식의 교환이 이뤄져야 하지만
        #어떤 시나리오상에는 챗봇-챗봇-유저 식의 변형이 있습니다.
        #FE측과의 타협 끝에 user의 선택지 대신에 req라는 별도의 메세지 타입을 보내어
        #FE에게 다시한번 요청을 해달라고 요구하기로 했습니다.
        #이렇게 되면 처리 과정은
        # (FE요청1시점)챗봇 - req, (FE요청2시점)챗봇-유저 로써
        # 챗봇-챗봇-유저가 가능해집니다.
        if user_gubun.startswith("챗봇"):
            raw_key = '-'.join([user_table,user_gubun])
            message_template.add_req("1")
            cursor_cached[user_id]["1"]=raw_key
            return message_template.json()

        print("유저커서",user_table,user_gubun,user_sentence)

        """
            이제 어떤 유저 커서와 row를 가져와야 할지 알겠으니 query를 해옵니다.
            user_only_once와 각종 함수들을 잘 처리하여 마무리합시다.
             """
        user_row = HookMessage.load_row(user_table, user_gubun)

        #예외처리입니다. 유저커서가 잘못되어 임시적으로 다음 row를 가져왔습니다.
        # 이경우는 다음 row가 챗봇이 될지 유저가 될지 모르는 심각한 상황입니다.
        # 발생시 시나리오 기입 담당자한테 말씀하세요
        if user_row == None:
            warn("이동이 없어 다음 인덱스의 문장을 가져왔습니다. 이는 심각한 오류를 초래할 수 있습니다.")
            user_row = HookMessage.load_next_row(user_table,row['index'])
            user_gubun = user_row["구분"]
        cursor_cached[user_id]["current"] = user_gubun


        #한문장만 출력해도 될때
        if user_only_one :
            #먼저 선택지에 대한 다음 커서를 cursor_cached에 지정해야합니다. {"1":"%대인관계`~~"}
            #일단 전체 문장에 걸려있는 함수에 대해서 처리합니다.
            if user_row["문장함수적용"] == "번호별매칭":
                raw_cursor = proc_params(user_row['함수파라미터'],user_table,user_sentence)
                cursor_cached[user_id]["1"] = raw_cursor+'-' + user_sentence
            elif user_row["문장함수적용"] == "이동하기":
                raw_cursor = proc_params(user_row['함수파라미터'],user_table)
                cursor_cached[user_id]["1"] = raw_cursor
            elif user_row["문장함수적용"] == "서술형":
                raw_cursor = proc_params(user_row['함수파라미터'],user_table)
                cursor_cached[user_id]["1"] = raw_cursor
            else:
                #이제 문장에 걸린 문장이동을가지고 cursor_cahced를 지정합니다.
                if not user_row[user_sentence + "이동"] is None:
                    raw_cursor = proc_params(user_row[user_sentence + "이동"], user_table)
                else : #예외처리, 어떤 커서를 지정해야될지 아무런 단서가 없습니다. 시나리오 기입 담당자한테 문의하세요.

                    warn(f"{user_table}, {user_gubun}, {user_sentence}에 문장이동이 없습니다! 이는 심각한 오류를 초래할 수 있습니다.")
                    next_row = HookMessage.load_next_row(user_table,user_row['index'])
                    raw_cursor = user_table + '-' +next_row['구분']
                cursor_cached[user_id]["1"] = raw_cursor


            #문장을 바꾸는 함수들을 처리합니다.
            if user_row[user_sentence+"개별함수"] == "문구변경":
                _content_temp = {
                    "type":"button",
                    "utterance":change_sentence(user_row,user_sentence,user_id),
                    "key":"1"
                }
                message_template.add_postback([_content_temp],utterance_cached[user_id])
            elif user_row[user_sentence+"개별함수"] == "서술형" or user_row["문장함수적용"]=="서술형" :
                _content_temp = {
                    "type": "desc",
                    "utterance": "",
                    "key": "1"
                }
                if user_row[user_sentence+"함수파라미터"] is not None:
                    """
                    """
                message_template.add_postback([_content_temp],utterance_cached[user_id])
            else :
                _content_temp = {
                    "type": "button",
                    "utterance": user_row[user_sentence],
                    "key": "1"
                }
                message_template.add_postback([_content_temp],utterance_cached[user_id])
            return message_template.json()

        """
            User only once가 아닌 경우 
            앞에서는 커서부터 처리했다면, 이번에는 문장부터 처리한다.
        """
        payloads=[] #message_template.add_postback 메서드에 필요한 payload입니다.
        """
            문장을 처리한 후(커서 처리 전) payload 예시는 아래와 같습니다.
            [
            {
                "key":1,
                "utterance":"1번문장입니다.",
                "type":"button"
            },
            {
                "key":2,
                "utterance":"",
                "type":"desc"
            
            },
            {
                "key":3,
                "utterance":"",
                "type":"blank"
            }
            ]
        
        """

        for i in range(int(user_row['문장갯수'])):
            payloads.append(dict())
            payloads[-1]["key"] = str(i + 1)
            if user_row[f"문장{i+1}개별함수"] == "문구변경":
                raw_sentence = change_sentence(user_row,f"문장{i+1}",user_id).strip()
                #print("문구변경 결과",raw_sentence, raw_sentence=='')
                payloads[-1]["utterance"] = raw_sentence
                payloads[-1]["type"]="button"
            elif user_row[f"문장{i+1}개별함수"] == "서술형" :
                payloads[-1]["utterance"] = ""
                payloads[-1]["type"]="desc"
                payloads=[payloads[-1]]+payloads[:-1]
            elif user_row[f"문장{i+1}"] is None or user_row[f"문장{i+1}"] == "":
                #예외처리입니다. 안이 비어있는 경우 서술형이 아닌이상 blank로 바꿉니다. 이는 추후에 처리됩니다.
                payloads[-1]["utterance"]=""
                payloads[-1]["type"] = "blank"
            else:
                payloads[-1]["utterance"] = user_row[f"문장{i+1}"]
                payloads[-1]["type"] = "button"

        """
         커서를 처리합니다. 방법은 아래와 같습니다.
         그 결과는 ret에 저장됩니다.
        1. 문장함수적용에 따라 처리 방법이 달라집니다.
        2. payload를 순회합니다. payload에 담긴 key번호에 맞춰서 cursor_cached에 저장합니다.
        3. 만약 type이 blank거나 문장(utterance)이 없다면(문구변경에 의해서 출력할 문장이 없음) ret에 추가하지 '않습니다'
        4. ret의 결과 예시는 아래 같습니다. (726번줄의 payload가 처리된다면)
        [
            {
                "key":1,
                "utterance":"1번문장입니다.",
                "type":"button"
            },
            {
                "key":2,
                "utterance":"",
                "type":"desc"
            
            }
            ]
        """
        if user_row["문장함수적용"] == "번호별매칭":
            raw_cursor = proc_params(user_row['함수파라미터'], user_table)

            for content in payloads:
                cursor_cached[user_id][content["key"]] = f'{raw_cursor}-문장{content["key"]}'

            rets =[]
            for content in payloads:
                if not(content['type'] == "blank" or content['utterance'] == ""):
                    rets.append(content)
            message_template.add_postback(rets,utterance_cached[user_id])
        elif user_row["문장함수적용"] == "서술선택형":
            for i,content in enumerate(payloads):
                if content['type']=='blank':
                    payloads[i]['type'] = 'desc'
                    payloads[i]["utterance"] = ""

                if not user_row[f"문장{i+1}이동"] is None:
                    raw_cursor = proc_params(user_row[f"문장{i+1}이동"], user_table)
                    cursor_cached[user_id][content["key"]] = f'{raw_cursor}'
                else:
                    warn(f"table_cursor:{user_table} gubun_cursor:{user_gubun} sentence_cursor:{user_sentence} \n"
                         f"유저의 문장이동이 존재하지 않아 잘못된 위치를 참조할 수 있습니다.")
                    next_row = HookMessage.load_next_row(user_table,user_row['index'])
                    cursor_cached[user_id][content["key"]] = f"{user_table}-{next_row['구분']}"
            message_template.add_postback(payloads,utterance_cached[user_id])
        elif user_row["문장함수적용"] == "이동하기":
            raw_cursor = proc_params(user_row['함수파라미터'], user_table)
            for content in payloads:
                cursor_cached[user_id][content["key"]] = f'{raw_cursor}'

            rets = []

            for content in payloads:
                if not (content['type'] == "blank" or content['utterance'] == ""):
                    rets.append(content)

            message_template.add_postback(rets,utterance_cached[user_id])
        elif user_row["문장함수적용"] == "서술형":
            raw_cursor = proc_params(user_row['함수파라미터'], user_table)

            for i, content in enumerate(payloads):
                payloads[i]['type']='desc'
                cursor_cached[user_id][content["key"]] = f'{raw_cursor}'

            message_template.add_postback(payloads,utterance_cached[user_id])
        else :
            #print(user_row)
            for i,content in enumerate(payloads):
                if user_row[f"문장{i+1}이동"] is None and user_row[f"문장{i+1}"] is None and user_row[f"문장{i+1}개별함수"] != "서술형":
                    continue
                if not user_row[f"문장{i+1}이동"] is None:
                    raw_cursor = proc_params(user_row[f"문장{i+1}이동"], user_table)
                    cursor_cached[user_id][content["key"]] = f'{raw_cursor}'
                elif user_row[f"문장{i+1}개별함수"] == "서술형":
                    raw_cursor = proc_params(user_row[f"문장{i + 1}함수파라미터"], user_table)
                    cursor_cached[user_id][content["key"]] = f'{raw_cursor}'
                else :
                    warn(f"table_cursor:{user_table} gubun_cursor:{user_gubun} sentence_cursor:{i+1} \n"
                         f"유저의 문장이동이 존재하지 않아 잘못된 위치를 참조할 수 있습니다.")
                    next_row = HookMessage.load_next_row(user_table, user_row['index'])
                    cursor_cached[user_id][content["key"]] = f"{user_table}-{next_row['구분']}"

            rets = []

            for content in payloads:
                if not (content['type'] != "desc" and content['utterance'] == ""):
                    rets.append(content)
            message_template.add_postback(rets,utterance_cached[user_id])

        return message_template.json()


