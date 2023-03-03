from db import db
from .counselor_time import CounselorTimeModel
from .counselor_tags import CounselorTagModel
from .counselor_experience import CounselorExpModel
from .counselor_certificate import CounselorCertModel

class CounselorModel(db.Model):
    __tablename__ = 'counselors'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(80)) #별명
    sentence = db.Column(db.Text(),nullable=True)
    profile_image = db.Column(db.Text(),nullable=True)


    experiences = db.relationship('CounselorExpModel', backref='counselors')
    times = db.relationship('CounselorTimeModel', backref='counselors')
    certificates = db.relationship('CounselorCertModel', backref='counselors')
    tags = db.relationship('CounselorTagModel', backref='counselors')

    def __init__(self, _name,_sentence,_profile):
        self.name = _name
        self.sentence = _sentence
        self.profile_image = _profile

    def json(self):
        return {
            'id':self.id,
            'name':self.name,
            'sentence':self.sentence,
            'profile_image':self.profile_image,
            'experiences':[con.get_content() for con in CounselorExpModel.find_all_with_counselor_id(self.id)],
            'certificates':[con.get_content() for con in CounselorCertModel.find_all_with_counselor_id(self.id)],
            'tags': [con.get_content() for con in CounselorTagModel.find_all_with_counselor_id(self.id)],
            'times':[con.get_content() for con in CounselorTimeModel.find_all_with_counselor_id(self.id)],
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def find_with_id(cls, _id):
        return cls.query.filter_by(id=_id).first()