from datetime import datetime
from models import UserModel, ChatModel, BannerModel,datetime_format, day_format, \
    CounselorModel, CounselorTimeModel, CounselorExpModel, CounselorTagModel, CounselorCertModel

def make_mock():
    flag = 0
    #
    # banner = BannerModel(
    #     _name="인스타",
    #     _link_to=r"https://www.instagram.com/soomter_/",
    #     _img_url=r"https://soomter.s3.ap-northeast-2.amazonaws.com/banner/%EB%B0%B0%EB%84%881.png",
    #     _start_date=datetime.strptime("2023-03-04",day_format),
    #     _end_date=datetime.strptime("2023-03-30",day_format),
    # )
    # banner = BannerModel.find_by_name("인스타")
    # print(banner.name)
    # banner.img_url=r"https://soomter.s3.ap-northeast-2.amazonaws.com/banner/%EB%B0%B0%EB%84%881+%EC%88%98%EC%A0%95.png"
    # banner.save_to_db()
    #
    # banner = BannerModel.find_by_name("카카오친구")
    # print(banner.name)
    # banner.img_url = r"https://soomter.s3.ap-northeast-2.amazonaws.com/banner/%EB%B0%B0%EB%84%882+%EC%88%98%EC%A0%95.png"
    # banner.save_to_db()

    #
    # banner = BannerModel(
    #     _name="카카오친구",
    #     _link_to=r"http://pf.kakao.com/_wxgJxmxj",
    #     _img_url=r"https://soomter.s3.ap-northeast-2.amazonaws.com/banner/%EB%B0%B0%EB%84%882.png",
    #     _start_date=datetime.strptime("2023-03-04", day_format),
    #     _end_date=datetime.strptime("2023-03-30", day_format),
    # )
    # banner.save_to_db()
    # #
    # with open("mocks.txt", "r", encoding='utf-8') as f:
    #     contents = f.readlines()
    #     counselor = [[], [], [], [], []]
    #
    #     for line in contents:
    #         real_line = line.strip()
    #         if real_line == "Counselor":
    #             counselor = [[], [], [], [], []]
    #             flag = 0
    #         elif real_line == "EXP":
    #             flag = 1
    #         elif real_line == "CERT":
    #             flag = 2
    #         elif real_line == "TIME":
    #             flag = 3
    #         elif real_line == "TAGS":
    #             flag = 4
    #         elif real_line != "":
    #             counselor[flag].append(real_line)
    #         else:
    #             name = counselor[0][0]
    #             sentence = counselor[0][1]
    #             pf = counselor[0][2]
    #             counselor_acc = CounselorModel(_name=name,_sentence=sentence,_profile=pf)
    #             counselor_acc.save_to_db()
    #             for con in counselor[1]:
    #                 #print(con)
    #                 counselor_con = CounselorExpModel(_content=con,_counselor_id=counselor_acc.id)
    #                 counselor_con.save_to_db()
    #             for con in counselor[2]:
    #                 counselor_con = CounselorCertModel(_content=con, _counselor_id=counselor_acc.id)
    #                 counselor_con.save_to_db()
    #             for con in counselor[3]:
    #                 counselor_con = CounselorTimeModel(_content=con,_counselor_id=counselor_acc.id)
    #                 counselor_con.save_to_db()
    #             for con in counselor[4]:
    #                 counselor_con = CounselorTagModel(_content=con,_counselor_id=counselor_acc.id)
    #                 counselor_con.save_to_db()
    # target = CounselorModel.find_with_id(11)
    # target.delete_from_db()
    #
    # target = CounselorModel.find_with_id(12)
    # target.delete_from_db()


