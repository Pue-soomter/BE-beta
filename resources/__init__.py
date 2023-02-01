def create_api(api):

    from .users import UserRegister, User, DevelopUserLogin, UserRefresh
    from .chats import DevelopAllChatList, NumberChatList
    from .banners import ListBanner
    from .contracts import InfoContract, LicenseContract

    #belonged to test or developmen
    dev_ns = api.namespace('develop', description='개발 및 테스트용 api') # /goods/ 네임스페이스를 만든다
    dev_ns.add_resource(DevelopUserLogin, '/login')
    dev_ns.add_resource(DevelopAllChatList, '/allchats')

    #belonged to chat
    chat_ns = api.namespace('v1/chats', description='채팅 기록(실시간 채팅 X)')
    chat_ns.add_resource(NumberChatList,'/')

    #belonged to main_menu
    menu_ns = api.namespace('v1/menu', description='메인페이지 API')
    menu_ns.add_resource(ListBanner, '/banners')

    #belonged to USER
    user_ns = api.namespace('v1/user', description='사용자 로그인/회원가입/정보')
    user_ns.add_resource(UserRegister, '/register')
    user_ns.add_resource(User, '/')
    user_ns.add_resource(UserRefresh, '/refresh')

    #belonged to contract
    contract_ns = api.namespace('v1/contract', description='개인정보 동의서, 라이센스')
    contract_ns.add_resource(InfoContract, '/personal')
    contract_ns.add_resource(LicenseContract, '/license')

def create_socketio(sock):
    from .chatnamespace import ChatNamespace
    sock.on_namespace(ChatNamespace('/realchat'))

def create_api_models(api):
    from .test import make_models
    make_models(api)