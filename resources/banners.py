from models.banner import BannerModel
from flask import request
from flask_jwt_extended import (
    get_jwt_identity,
)
from flask_restx import Api, Resource, fields,marshal_with
from datetime import datetime
from models import day_format, datetime_format
from app import api

class ListBanner(Resource):
    @api.doc(
        description="특정 날에 활성화된 배너",
        params={"date(": "(nullable) 특정 날 제시 %Y-%m-%d"})
    def get(self):
        try :
            params = request.args.to_dict()
            target = params['date']
        except KeyError:
            target = datetime.now().strftime(day_format)
        banners = [banner.json() for banner in BannerModel.find_from_end(datetime.strptime(target,day_format))]
        return {
            'message': "ok",
            'data': banners,
        }, 200
