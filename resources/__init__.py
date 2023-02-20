def create_api(api):
    from .users import UserRegister, User, DevelopUserLogin, UserRefresh
    from .chats import DevelopAllChatList, NumberChatList
    from .banners import ListBanner
    from .contracts import InfoContract, LicenseContract
    from .message import HookMessage, UserMessage

    #belonged to test or developmen
    dev_ns = api.namespace('develop', description='개발 및 테스트용 api') # /goods/ 네임스페이스를 만든다
    dev_ns.add_resource(DevelopUserLogin, '/login')
    dev_ns.add_resource(DevelopAllChatList, '/allchats')

    #belonged to main_menu
    v1 = api.namespace('v1/', description='메인페이지 API')
    v1.add_resource(ListBanner, '/banners')

    #belonged to USER
    v1.add_resource(UserRegister, '/user/register')
    v1.add_resource(User, '/user')
    v1.add_resource(UserRefresh, '/user/refresh')

    # belonged to chatlog
    v1.add_resource(NumberChatList, '/chats')

    # belonged to real_time
    v1.add_resource(HookMessage, '/message')
    v1.add_resource(UserMessage, '/message/user')

    #belonged to contract
    v1.add_resource(InfoContract, '/contract')
    v1.add_resource(LicenseContract, '/license')

def create_api_models(api):
    from .test import make_models
    make_models(api)