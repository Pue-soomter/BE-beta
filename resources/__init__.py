

def create_api(api):
    from .user import UserRegister, User
    from .chat import AllChatList, NumberChatList
    #belonged to chat
    api.add_resource(NumberChatList,'/chats')

    #belonged to USER
    api.add_resource(UserRegister, '/register')
    api.add_resource(User, '/user')

def create_socketio(sock):
    from .chatnamespace import ChatNamespace
    sock.on_namespace(ChatNamespace('/realchat'))


