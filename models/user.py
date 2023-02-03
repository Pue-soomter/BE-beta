from db import db

class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    nickname = db.Column(db.String(80)) #별명
    is_member = db.Column(db.Boolean()) #회원구분,(0-비회원, 1-회원)

    email = db.Column(db.String(80),nullable=True,unique=True)
    birth = db.Column(db.DateTime())
    location = db.Column(db.String(80)) #사는지역
    job = db.Column(db.String(80))
    age = db.Column(db.String(80))
    gender = db.Column(db.String(80))
    is_allow = db.Column(db.Boolean())

    profile_image = db.Column(db.Text(),nullable=True)

    chats = db.relationship('ChatModel', backref='users')

    def __init__(self, _nickname,_is_member,_birth,_location,_job,_age,_is_allow,_gender,_email=None,_prof_image=None):
        self.nickname = _nickname
        self.is_member = _is_member  # 회원구분,(0-비회원, 1-회원)

        self.email = _email
        self.birth = _birth
        self.location = _location
        self.job = _job
        self.age = _age
        self.gender = _gender
        self.is_allow = _is_allow

        self.profile_image =_prof_image

    def json(self):
        return {
            "info":{
                'id':self.id,
                'nick_name':self.nickname,
                'profile_image':self.profile_image,
                'member': "members" if self.is_member else "non-members",
            },
            "additional":{
                'email': self.email,
                'birth': self.birth,
                'age': self.age,
                'job': self.job,
                'location': self.location,
                'gender':self.gender
            }
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_nickname(cls, _nickname):
        return cls.query.filter_by(nickname=_nickname).first()

    @classmethod
    def find_by_email(cls, _email):
        return cls.query.filter_by(email=_email).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()
