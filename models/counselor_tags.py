from db import db
from . import and_

class CounselorTagModel(db.Model):
    __tablename__ = 'counselor_tags'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text())
    counselor_id = db.Column(db.Integer, db.ForeignKey('counselors.id'))

    def __init__(self,_content, _counselor_id):
        self.content = _content
        self.counselor_id = _counselor_id


    def get_content(self):
        return self.content

    def json(self):
        return {'content': self.content}

    @classmethod
    def find_all_with_counselor_id(cls, _counselor_id):
        return cls.query.filter_by(counselor_id=_counselor_id).all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
