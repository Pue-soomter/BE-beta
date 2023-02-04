from datetime import datetime
from models import UserModel, ChatModel, BannerModel,datetime_format, day_format

def make_mock():

    user = UserModel(
        _nickname="chanee"
    )
    user.save_to_db()

    chat = ChatModel(
        _user_id=user.id,
        _date=datetime.strptime("2023-01-30 13:30:15",datetime_format),
        _chatter="bot",
        _utterance="안녕 병찬아?"
    )
    chat.save_to_db()

    chat = ChatModel(
        _user_id=user.id,
        _date=datetime.strptime("2023-01-30 13:30:18", datetime_format),
        _chatter="bot",
        _utterance="무슨일 있니?"
    )
    chat.save_to_db()

    chat = ChatModel(
        _user_id=user.id,
        _date=datetime.strptime("2023-01-30 13:30:30", datetime_format),
        _chatter="user",
        _utterance="일 없습네다."
    )
    chat.save_to_db()

    banner = BannerModel(
        _name="샘플1",
        _start_date=datetime.strptime("2023-01-30", day_format),
        _end_date=datetime.strptime("2023-03-01", day_format),
        _img_url="https://soomter.s3.ap-northeast-2.amazonaws.com/sample1.jpg",
        _link_to="www.google.com"
    )
    banner.save_to_db()

    banner = BannerModel(
        _name="샘플2",
        _start_date=datetime.strptime("2023-01-30", day_format),
        _end_date=datetime.strptime("2023-03-01", day_format),
        _img_url="https://soomter.s3.ap-northeast-2.amazonaws.com/sample2.jpg",
        _link_to="www.google.com"
    )
    banner.save_to_db()
