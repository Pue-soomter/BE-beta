from db import db
from . import and_

class BannerModel(db.Model):
    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(80))
    start_date = db.Column(db.DateTime())
    end_date = db.Column(db.DateTime())
    img_url = db.Column(db.Text())
    link_to = db.Column(db.Text())

    def __init__(self, _name,_start_date,_end_date,_img_url,_link_to):
        self.name = _name
        self.start_date = _start_date
        self.end_date = _end_date
        self.img_url = _img_url
        self.link_to = _link_to

    def json(self):
        return {'img': self.img_url,'link':self.link_to}

    @classmethod
    def find_by_name(cls, _name):
        return cls.query.filter_by(name=_name).first()

    @classmethod
    def find_from_end(cls, date):
        return cls.query.filter(and_(cls.start_date <= date, cls.end_date >= date)).order_by(cls.id.desc()).all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
