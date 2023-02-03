
class MessageTemplate():
    def __init__(self,_message):
        self.message = _message
        self.data=[]

    def add_message(self,_message,_userid,_func):
        _temp = {"type":"message"}
        _temp["message"]=_message
        _func(_userid,"bot",_message)
        self.data.append(_temp)

    def add_traffic_lights(self):
        _temp={
            "type": "traffic_lights",
            "payload": [{
                'key': '1',
                'cursor': "유저시작",
                'table': "시작",
                'utterance': "기분이 좋지 않아",
                'postback':{
                    "cursor":"챗봇도입",
                    "table":"도입1",
                    "sentence":"문장1"
                }
            }, {
                'key': '2',
                'cursor': "유저시작",
                'table': "시작",
                'utterance': "그저 그래",
                'postback': {
                    "cursor": "챗봇도입",
                    "table": "도입1",
                    "sentence": "문장1"
                }
            }, {
                'key': '3',
                'cursor': "유저시작",
                'table': "시작",
                'utterance': "괜찮은 것 같아",
                'postback': {
                    "cursor": "챗봇도입",
                    "table": "도입1",
                    "sentence": "문장2"
                }
            }

            ]
        }
        self.data.append(_temp)

    def add_button(self,payloads):
        _temp = {
            "type": "button",
            "payload": []
        }
        for content in payloads:
            _content_temp={}
            _content_temp["key"] = content[0]
            _content_temp["cursor"] = content[1]
            _content_temp["table"] = content[2]
            _content_temp["utterance"] = content[3]
            _content_temp['postback']={}
            _content_temp['postback']["cursor"] = content[4]
            _content_temp['postback']["table"] = content[5]
            _content_temp['postback']["sentence"] = content[6]
            _temp["payload"].append(_content_temp)

        self.data.append(_temp)


    def json(self):
        return {
            'message':self.message,
            'data':self.data
        }
