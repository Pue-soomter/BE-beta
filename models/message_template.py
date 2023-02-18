from .user import UserModel

class MessageTemplate():
    def __init__(self,_message):
        self.message = _message
        self.data=[]

    def add_message(self,_message,_userid,_save_chat):
        user = UserModel.find_by_id(_userid)
        _temp = {"type":"message"}
        _temp["utterance"]=_message.replace("00",user.nickname)
        _temp["chatter"] = 'bot'
        _save_chat(_userid,"bot",_message)
        self.data.append(_temp)

    def add_traffic_lights(self,cursor_cache):
        _temp={
            "type": "traffic_lights",
            "chatter":'user',
            "payload": [{
                'utterance': "테스트입니다. 빨간불",
                'postback':{
                    'key':'1',
                    'utterance': "테스트입니다. 빨간불",
                }
            }, {
                'utterance': "테스트입니다. 주황불",
                'postback': {
                    'key':'2',
                    'utterance': "테스트입니다. 주황불",
                }
            }, {
                'utterance': "테스트입니다. 초록불",
                'postback': {
                    'key':'3',
                    'utterance': "테스트입니다. 초록불"
                }
            }
            ]
        }
        self.data.append(_temp)
        cursor_cache["1"] = "도입1-챗봇도입-문장1"
        cursor_cache["2"] = "도입1-챗봇도입-문장1"
        cursor_cache["3"] = "도입1-챗봇도입-문장1"
        cursor_cache["current"] = "유저시작"

    def add_postback(self,payloads):
        counter = {"desc":0,"button":0}
        _temp = {
            "type": "postback",
            "default" : payloads[0]["key"],
            "chatter":"user",
            "payload": []
        }
        for content in payloads:
            _content_temp={}
            counter[content["type"]]+=1
            #_content_temp["type"]=content["type"]
            _content_temp["utterance"] = content["utterance"]
            _content_temp['postback']={}
            _content_temp['postback']["key"] = content["key"]
            _content_temp['postback']["utterance"] = content["utterance"]
            _temp["payload"].append(_content_temp)

        if counter["desc"] * counter["button"] == 0:
            _temp["type"] = "desc" if counter["desc"]>counter["button"] else "button"
            _temp.pop("default")
        else :
            _temp["type"] = "mixture"
            _temp["payload"] = _temp["payload"][1:]

        self.data.append(_temp)

    def add_list(self,_list_name,_key):
        _temp = {
            "type": "list",
            "payload": []
        }
        if _list_name == "실천":
            _content_temp={
                "title":"실천 목록 작성",
                "utterance":"한번 실천목록을 작성해볼까?",
                "postback":{
                    "key":_key,
                    "list":[]
                }
            }
            _temp["payload"].append(_content_temp)
        elif _list_name == "???":
            """
                TO DO
            """
        self.data.append(_temp)

    def add_special(self,_name,_key):
        _temp = {
            "type": _name,
            "payload": []
        }
        _content_temp = {
            "postback": {
                "key": _key,
                "list": []
            }
        }
        _temp["payload"].append(_content_temp)
        self.data.append(_temp)

    def json(self):
        return {
            'message':self.message,
            'data':self.data
        }
