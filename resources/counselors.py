from models import CounselorModel
from flask import request
from flask_jwt_extended import (
    get_jwt_identity,
)
from flask_restx import Api, Resource, fields,marshal_with
import random
from datetime import datetime
from models import day_format, datetime_format
from app import api

class ListCounselor(Resource):
    @api.doc(
        description="상담사 리스트 불러오기"
    )
    def get(self):

        counselors = [counselor.json() for counselor in CounselorModel.find_all()]
        random.shuffle(counselors)

        return {
            'message': "ok",
            'data': counselors[:2],
        }, 200
