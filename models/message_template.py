from .user import UserModel
from datetime import datetime
from pytz import timezone
from pyjosa.josa import Josa, Jongsung
import re

day_format = "%Y-%m-%d"
datetime_format = "%Y-%m-%d %H:%M:%S"

def process_josa(target,msg):
    """
                목적:
                    1. 00을 닉네임으로 변환하기 위한 함수

                파라미터:
                    target -> 닉네임
                    msg -> 변환할 이름

                결과:
                    닉네임으로 바뀐 문장을 반환한다.

            """
    #닉네임을 두글자로만 자르고, 정규식표현을 이용하여 괄호를 없앤다. 00(이)야 -> 이야
    target = target[-2:]
    raw_target = msg.replace("00", "")
    result = re.sub(r'\((.*?)\)', r'\1', raw_target).strip()

    #종성 여부를 판단하여 경우의수를 만들었는데, 절대 완벽하지 않습니다...
    #Josa.get_full_string()는 target과 조사(result)를 변환하여 붙여주는데 못붙이는 경우 Exception을 발생시킵니다.
    try:
        if result.endswith("야") or result.endswith("아"):
            if Jongsung.has_jongsung(target):
                return target+"아"
            else:
                return target + "야"
        if result.startswith("이"):
            target += '이' * Jongsung.has_jongsung(target)
            result = result[1:]
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
        #FE분이 날짜가 바뀌면 time을 넣어달라해서 만들었습니다. 자세한 처리 과정은 FE분께...
        _temp = {
            "type": "new_day",
            "utterance":time
        }
        self.data.append(_temp)

    def add_message(self,_message,_userid,_save_chat):
        user = UserModel.find_by_id(_userid)

        #정규식을 이용, . .. ... ..! ? ..? 등을 만나면 문장을 나누는데, 이 기호들을 삭제하지 않습니다.
        #""안의 내용은 나누지 않습니다.

        #""안의 내용은 나누지 않기 위해서 ""만 따로 빼는 과정입니다. (quoted~~로 저장됩니다.)
        quoted_substrings = MessageTemplate.quoted_substring_re.findall(_message)
        output_list = MessageTemplate.quoted_substring_re.split(_message)

        #공백제거
        output_list = [i.strip() for i in output_list if i != '']
        raw_output = []

        # "" 외의 문장들에 대해서 . .. ... 등의 기호로 split을 실시합니다.
        for out in output_list:
            raw_output += re.split(MessageTemplate.pattern, out)

        """
            현상황은 이렇습니다.
            
            입력 : '그럼 "오늘 날씨가 좋아" 라고 말씀하셨나요? 그렇군요.'
            quoted : ["오늘 날씨가 좋아"]
            output_list : ["그럼","라고 말씀하셨나요? 그렇군요."]
            raw_output :[["그럼"],["라고 말씀하셨나요?","그렇군요."]]
            
            보면 알겠지만, raw_output은 길이가 최대 2, 뒷문장이 없으면 1이다.
            따라서 raw_output과 quoted를 번갈아 합치면 최종 메세지가 완성된다.
            ["그럼"] + ["오늘 날씨가 좋아"] +["라고 말씀하셨나요?","그렇군요."]
        
        """
        output_list = raw_output
        output_list_with_quotes = []
        for i in range(len(output_list)):
            output_list_with_quotes.append(output_list[i])
            if i < len(quoted_substrings):
                output_list_with_quotes.append(quoted_substrings[i])

        messages = output_list_with_quotes

        # Find all occurrences of the substrings

        target = user.nickname

        #메세지를 분할하는 과정
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
        """
        페이로드 내용 하나는 아래 양식을 가지고 있다.
         {
                "type": "button",
                "utterance": "안녕하세요",
                "key": "1"
            }"""
        for content in payloads:
            #이 함수 진입전에 예외처리를 하긴 했으나 혹시나 있을지 모르는 예외를 또 처리함
            if content["utterance"] is None and content["type"] == 'button':
                continue

            #메시지 전송 양식 만들기
            _content_temp={}

            #desc 또는 button에 대해 +1
            counter[content["type"]]+=1
            utterance_cache[content["key"]]=content["utterance"]
            _content_temp["utterance"] = content["utterance"]
            _content_temp['postback']=content["key"]
            _temp["payload"].append(_content_temp)

        #desc인지, button인지, mixture인지 판단하기
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
                "utterance":f"{process_josa(_target,'00이가')} 스스로를 위해 할 수 있는 것들은 무엇이 있을까?",
                "select_utterance":"이제 실천할 수 있는 일을 우선순위에 따라 선택해보자!",
                "postback":_key,
            }
            _pre_button["utterance"] = "실천 목록 작성하기"
            _temp["payload"].append(_content_temp)
        elif _list_name == "목표":
            _content_temp={
                "title":"삶의 목표 탐색",
                "placeholder": "이루고 싶은 목표를 적어보세요(ex_ 혼자서 일본 여행가기)",
                "utterance":f"{process_josa(_target,'00이의')} 삶에서 원하는 목표가 있다면 뭐가 있을까?",
                "select_utterance":"이제 할 수 있는 일들을 우선순위에 따라 선택해보자!",
                "postback":_key,
            }
            _pre_button["utterance"] = "삶의 목표 정하기"
            _temp["payload"].append(_content_temp)
        elif _list_name == "나의모습":
            _content_temp = {
                "title": "내가 원하는 나",
                "placeholder": "내가 원하는 모습을 채워보세요(ex_ 사람들에게 먼저 인사하기)",
                "utterance": f"{process_josa(_target,'00이가')} 원했던 자신의 모습은 어떤 모습이었을까?",
                "select_utterance": "가장 먼저 되고 싶은 모습이나, 쉽게 해볼 수 있는 건 어떤 걸까?",
                "postback": _key,
            }
            _pre_button["utterance"] = "내가 원하는 모습 찾기"
            _temp["payload"].append(_content_temp)
        elif _list_name == "이별사유":
            _temp["type"]="list"
            _content_temp = {
                "title": "헤어짐의 이유",
                "placeholder": "연인과 만나며 힘들었던 점을 적어보세요(ex_ 데이트 중 잦은 싸움)",
                "utterance": f"{process_josa(_target,'00이가')} 연인과 만나면서 힘들었던 이유에 대해 적어볼래?",
                "postback": _key,
            }
            _pre_button["utterance"] = "헤어짐의 이유 찾기"
            _temp["payload"].append(_content_temp)
        elif _list_name == "이별못함":
            _temp["type"]="list"
            _content_temp = {
                "title": "이별 못하는 이유",
                "placeholder": "내가 헤어지지 못하는 이유를 적어보세요(ex_ 그 동안의 정 때문에)",
                "utterance": f"{process_josa(_target,'00이가')} 연인과 헤어지지 못하는 이유에 대해 적어볼래?",
                "postback": _key,
            }
            _pre_button["utterance"] = "헤어지지 못하는 이유 찾기"
            _temp["payload"].append(_content_temp)
        elif _list_name == "좋아함":
            _temp["type"]="list"
            _content_temp = {
                "title": "내가 좋아하는 것",
                "placeholder": "내가 좋아하는 것을 적어보세요(ex_ 사람들에게 먼저 인사하기)",
                "utterance": f"{process_josa(_target,'00이가')} 좋아하고, 원하는 것을 구체적으로 떠올리며 적어볼래?",
                "postback": _key,
            }
            _pre_button["utterance"] = "내가 좋아하는 것 찾기"
            _temp["payload"].append(_content_temp)
        elif _list_name == "자기탐색":
            _temp["type"] = "list"
            _content_temp = {
                "title": "자기 탐색하기",
                "placeholder": "내가 하고 싶은 것을 적어보세요(ex_ 일본여행 다녀오기)",
                "utterance": f"{process_josa(_target,'00이가')} 앞으로 하고 싶은 것을 떠올리며 적어볼래?",
                "postback": _key,
            }
            _pre_button["utterance"] = "내가 하고 싶었던 것 찾기"
            _temp["payload"].append(_content_temp)
        elif _list_name == "selftalk":
            _temp["type"] = "selftalk"
            _content_temp = {
                "title": "Self-talk 하기",
                "utterance": "하나 약속하자면, 절대 우리 이야기를 이곳을 벗어나는 일은 없을거야. 그러니 너를 힘들게 하는 생각이나 감정을 이곳에 얘기해줄래",
                "postback": _key,
            }
            _pre_button["utterance"] = "Self-talk 시작하기"
            _temp["payload"].append(_content_temp)

        self.data.append(_pre_button)
        self.data.append(_temp)


    #여기서 조사 처리하면 딱이겠다 딱
    def json(self):
        return {
            'message':self.message,
            'data':self.data
        }
