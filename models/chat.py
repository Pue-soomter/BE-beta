from db import db
from . import and_

class ChatModel(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime()) #YYYYMMDD
    chatter = db.Column(db.String(80))  #발신/송신 구별
    utterance = db.Column(db.Text()) #대화내용

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, _user_id, _date,_chatter,_utterance):
        self.date = _date
        self.chatter = _chatter
        self.utterance = _utterance

        self.user_id = _user_id

    def json(self):
        return {'date': self.date, 'chatter': self.chatter,'utterance':self.utterance}

    @classmethod
    def find_by_number_with_user_id(cls, _user_id,_latest,number):
        return cls.query.filter(cls.date < _latest, cls.user_id == _user_id).order_by(cls.id.desc()).limit(number).all()

    @classmethod
    def find_all_with_user_id(cls,_user_id):
        return cls.query.filter_by(user_id=_user_id).order_by(cls.id.desc()).all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
