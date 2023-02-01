from datetime import datetime
from models import UserModel, ChatModel, BannerModel,datetime_format, day_format

def make_mock():

    user = UserModel(
        _nickname="chanee",
        _email="well87865@gmail.com",
        _is_allow= True,
        _location= "경기",
        _birth=datetime.strptime("1998-11-19",day_format),
        _is_member=False,
        _prof_image="",
        _age=24,
        _job="학생"
    )
    user.save_to_db()

    chat = ChatModel(
        _user_id=user.id,
        _date=datetime.strptime("2023-01-30 13:30:15",datetime_format),
        _chatter="bot",
        _sentence="안녕 병찬아?"
    )
    chat.save_to_db()

    chat = ChatModel(
        _user_id=user.id,
        _date=datetime.strptime("2023-01-30 13:30:18", datetime_format),
        _chatter="bot",
        _sentence="무슨일 있니?"
    )
    chat.save_to_db()

    chat = ChatModel(
        _user_id=user.id,
        _date=datetime.strptime("2023-01-30 13:30:30", datetime_format),
        _chatter="user",
        _sentence="일 없습네다."
    )
    chat.save_to_db()

    banner = BannerModel(
        _name="네이버",
        _start_date=datetime.strptime("2023-01-30", day_format),
        _end_date=datetime.strptime("2023-03-01", day_format),
        _img_url="www.naver.com",
        _link_to="www.google.com"
    )
    banner.save_to_db()

    banner = BannerModel(
        _name="카카오",
        _start_date=datetime.strptime("2023-01-30", day_format),
        _end_date=datetime.strptime("2023-03-01", day_format),
        _img_url="www.kakao.com",
        _link_to="www.google.com"
    )
    banner.save_to_db()
