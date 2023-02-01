from flask_restx import fields

def make_models(api):
    api.model('Register', {
        'nick_name': fields.String(example="pue",required=True, description='사용자 별명'),
        'is_member':fields.Boolean(example=False,required=True, description='비회원-false, 회원-true'),
        'email': fields.String(example="abcd1234@gmail.com",required=True, description='이메일(빈칸가능)'),
        'location': fields.String(example="경기",required=True, description='사는 지역(문자열)'),
        'birth': fields.String(example="1998-11-19",required=True, description='생년월일(%Y-%m-%d)'),
        'job': fields.String(example="학생",required=True, description='직업(문자열)'),
        'age': fields.String(example="20대",required=True, description='나이대(문자열)'),
        'is_allow': fields.Boolean(example=True, required=True, description='개인정보이용 동의여부'),
            })