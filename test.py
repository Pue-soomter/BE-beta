from pyjosa.josa import Josa, Jongsung
import re

raw_target = "00인걸"
target = "경모"

raw_target = raw_target.replace("00","")
result = re.sub(r'\((.*?)\)', r'\1',raw_target).strip()

output=""
try:
    if result == "이":
        output = target+'이'*Jongsung.has_jongsung(target)
    else:
        if Jongsung.has_jongsung(target) and not result.startswith("이"):
            target+="이"
        output = Josa.get_full_string(target, result)
except Exception as e:
    if not Jongsung.is_hangle(target):
        output = target + result[-1]
    elif result.startswith("이는"):
        if Jongsung.has_jongsung(target):
            output = target+"이는"
        else:
            output = target+"는"
    elif result == "":
        output=target
    else:
        try:
            output = Josa.get_full_string(target, result[-1])
        except :
            output = target + result


print(output)

