from .user import UserModel
from datetime import datetime
from pytz import timezone
from pyjosa.josa import Josa, Jongsung
import re

day_format = "%Y-%m-%d"
datetime_format = "%Y-%m-%d %H:%M:%S"

def process_josa(target,msg):

    target = target[-2:]
    raw_target = msg.replace("00", "")
    result = re.sub(r'\((.*?)\)', r'\1', raw_target).strip()

    try:
        if result == "이":
            output = target + '이' * Jongsung.has_jongsung(target)
        else:
            if Jongsung.has_jongsung(target) and not result.startswith("이"):
                target += "이"
            output = Josa.get_full_string(target, result)
    except Exception as e:
        if not Jongsung.is_hangle(target):
            output = target + result[-1]
        elif result.startswith("이는"):
            if Jongsung.has_jongsung(target):
                output = target + "이는"
            else:
                output = target + "는"
        elif result == "":
            output = target
        else:
            try:
                output = Josa.get_full_string(target, result[-1])
            except:
                output = target + result

    return output

class MessageTemplate():
    quoted_substring_re = re.compile(r'"[^"]*"|\'[^\']*\'', re.DOTALL)
    pattern = r"(?<=[.?!])\s+|\s+(?=[.?!])|\s+(?=\.\.\.)|\s+(?=\.\.)|\s+(?=\.\?)"

    def __init__(self,_message):
        self.message = _message
        self.data=[]

    def add_req(self,_key):
        _temp = {
            "type": "request",
            "postback":_key
        }
        self.data.append(_temp)

    def add_time(self,time):
        _temp = {
            "type": "new_day",
            "utterance":time
        }
        self.data.append(_temp)

    def add_message(self,_message,_userid,_save_chat):
        user = UserModel.find_by_id(_userid)
        print("raw",_message)
        #_temp["utterance"]=_message.replace("00",user.nickname)
        quoted_substrings = MessageTemplate.quoted_substring_re.findall(_message)
        output_list = MessageTemplate.quoted_substring_re.split(_message)

        output_list = [i.strip() for i in output_list if i != '']
        raw_output = []
        for out in output_list:
            raw_output += re.split(MessageTemplate.pattern, out)

        output_list = raw_output
        output_list_with_quotes = []
        for i in range(len(output_list)):
            output_list_with_quotes.append(output_list[i])
            if i < len(quoted_substrings):
                output_list_with_quotes.append(quoted_substrings[i])

        messages = output_list_with_quotes

        # Find all occurrences of the substrings

        target = user.nickname
        print(messages)
        for message in messages :
            msg_list = message.split(" ")

            for i in range(len(msg_list)):
                if '00' in msg_list[i]:
                    output = process_josa(target,msg_list[i])
                    msg_list[i] = output


            _temp = {"type": "message"}
            _temp["chatter"] = 'bot'
            _temp["utterance"] = ' '.join(msg_list)

            _save_chat(_userid,"bot",_temp["utterance"])
            self.data.append(_temp)

    def add_traffic_lights(self,cursor_cache,utterance_cache):

        _temp={
            "type": "traffic_lights",
            "chatter":'user',

            "payload": [{
                'utterance': "기분이 너무 안좋아",
                'postback':'1',
            }, {
                'utterance': "평소랑 다를 거 없어",
                'postback': '2',

            }, {
                'utterance': "오늘은 기분이 좋아",
                'postback': '3'
            }
            ]
        }
        self.data.append(_temp)
        cursor_cache["1"] = "도입1-챗봇도입-문장1"
        cursor_cache["2"] = "도입1-챗봇도입-문장1"
        cursor_cache["3"] = "도입1-챗봇도입-문장1"
        utterance_cache["1"] = "기분이 너무 안좋아"
        utterance_cache["2"] = "평소랑 다를 거 없어"
        utterance_cache["3"] = "오늘은 기분이 좋아"
        cursor_cache["current"] = "유저시작"

    def add_counselor(self,cursor_cache,utterance_cache):

        payloads = []
        _temp={
            "type":"button",
            "utterance":"상담사와 얘기하기",
            "key":"상담사매칭"
        }
        cursor_cache["상담사매칭"]="도입1-챗봇도입-문장2"
        payloads.append(_temp)
        _temp = {
            "type": "button",
            "utterance": "숨터에서 계속 이야기하기",
            "key": "2"
        }
        payloads.append(_temp)
        cursor_cache["2"] = "도입1-챗봇도입-문장2"
        self.add_postback(payloads,utterance_cache)

    def add_req_special(self,_name,_key):
        _temp = {
            "type": _name,
            "payload": []
        }
        _content_temp = {
            "postback": _key
        }
        _temp["payload"].append(_content_temp)
        self.data.append(_temp)

    def add_postback(self,payloads,utterance_cache):

        counter = {"desc":0,"button":0}
        _temp = {
            "type": "postback",
            "default" : payloads[0]["key"],
            "chatter":"user",
            "payload": []
        }
        for content in payloads:
            if content["utterance"] is None and content["type"] == 'button':
                continue
            _content_temp={}
            counter[content["type"]]+=1
            #_content_temp["type"]=content["type"]
            utterance_cache[content["key"]]=content["utterance"]
            _content_temp["utterance"] = content["utterance"]
            _content_temp['postback']=content["key"]
            _temp["payload"].append(_content_temp)

        if counter["desc"] * counter["button"] == 0:
            _temp["type"] = "desc" if counter["desc"]>counter["button"] else "button"
            if _temp["type"] == "desc":
                _temp["payload"].pop()
            else:
                _temp.pop("default")
        else :
            _temp["type"] = "mixture"
            _temp["payload"] = _temp["payload"][1:]

        self.data.append(_temp)

    def add_list(self,_list_name,_key,_userid):
        user = UserModel.find_by_id(_userid)
        _target = user.nickname
        now = datetime.now(timezone('Asia/Seoul'))
        _pre_button ={
            "type":"button_list",
            "utterance":"",
            "chatter": 'bot',
        }
        _temp = {
            "type": "list_select",
            "chatter": 'bot',
            #"date": now.strftime(datetime_format),
            "payload": []
        }
        if _list_name == "실천":
            _content_temp={
                "title":"실천목록 작성",
                "placeholder":"나만의 실천목록을 채워보세요(ex_ 하루 10분 산책하기)",
                "utterance":f"{process_josa(_target,'00이가')} 한번 실천목록을 작성해볼까?",
                "select_utterance":"이제 실천할 수 있는 일을 우선순위에 따라 선택해보자!",
                "postback":_key,
            }

            _temp["payload"].append(_content_temp)
        elif _list_name == "목표":
            _content_temp={
                "title":"삶의 목표 탐색",
                "placeholder": "이루고 싶은 목표를 적어보세요(ex_ 혼자서 일본 여행가기)",
                "utterance":f"{process_josa(_target,'00이의')} 삶에서 원하는 목표가 있다면 뭐가 있을까?",
                "select_utterance":"이제 할 수 있는 일들을 우선순위에 따라 선택해보자!",
                "postback":_key,
            }
            _temp["payload"].append(_content_temp)
        elif _list_name == "나의모습":
            _content_temp = {
                "title": "내가 원하는 나",
                "placeholder": "내가 원하는 모습을 채워보세요(ex_ 사람들에게 먼저 인사하기)",
                "utterance": f"{process_josa(_target,'00이가')} 원했던 자신의 모습은 어떤 모습이었을까?",
                "select_utterance": "가장 먼저 되고 싶은 모습이나, 쉽게 해볼 수 있는 건 어떤 걸까?",
                "postback": _key,
            }
            _temp["payload"].append(_content_temp)
        elif _list_name == "이별사유":
            _temp["type"]="list"
            _content_temp = {
                "title": "헤어짐의 이유",
                "placeholder": "연인과 만나며 힘들었던 점을 적어보세요(ex_ 데이트 중 잦은 싸움)",
                "utterance": f"{process_josa(_target,'00이가')} 연인과 만나면서 힘들었던 이유에 대해 적어볼래?",
                "postback": _key,
            }
            _temp["payload"].append(_content_temp)
        elif _list_name == "이별못함":
            _temp["type"]="list"
            _content_temp = {
                "title": "이별 못하는 이유",
                "placeholder": "내가 헤어지지 못하는 이유를 적어보세요(ex_ 그 동안의 정 때문에)",
                "utterance": f"{process_josa(_target,'00이가')} 연인과 헤어지지 못하는 이유에 대해 적어볼래?",
                "postback": _key,
            }
            _temp["payload"].append(_content_temp)
        elif _list_name == "좋아함":
            _temp["type"]="list"
            _content_temp = {
                "title": "내가 좋아하는 것",
                "placeholder": "내가 좋아하는 것을 적어보세요(ex_ 사람들에게 먼저 인사하기)",
                "utterance": f"{process_josa(_target,'00이가')} 좋아하고, 원하는 것을 구체적으로 떠올리며 적어볼래?",
                "postback": _key,
            }
            _temp["payload"].append(_content_temp)
        elif _list_name == "자기탐색":
            _temp["type"] = "list"
            _content_temp = {
                "title": "자기 탐색하기",
                "placeholder": "내가 하고 싶은 것을 적어보세요(ex_ 일본여행 다녀오기)",
                "utterance": f"{process_josa(_target,'00이가')} 앞으로 하고 싶은 것을 떠올리며 적어볼래?",
                "postback": _key,
            }
            _temp["payload"].append(_content_temp)
        elif _list_name == "selftalk":
            _temp["type"] = "selftalk"
            _content_temp = {
                "title": "Self-talk 하기",
                "utterance": "하나 약속하자면, 절대 우리 이야기를 이곳을 벗어나는 일은 없을거야. 그러니 너를 힘들게 하는 생각이나 감정을 이곳에 얘기해줄래",
                "postback": _key,
            }
            _temp["payload"].append(_content_temp)

        _pre_button["utterance"] = _temp["payload"][0]["title"]
        self.data.append(_pre_button)
        self.data.append(_temp)


    #여기서 조사 처리하면 딱이겠다 딱
    def json(self):
        return {
            'message':self.message,
            'data':self.data
        }
