from pyjosa.josa import Josa, Jongsung
import re

msg = "00이야"
target = "병찬"


def process_josa(target,msg):

    target = target[-2:]
    raw_target = msg.replace("00", "")
    result = re.sub(r'\((.*?)\)', r'\1', raw_target).strip()

    try:
        if result.endswith("야") or result.endswith("아"):
            if Jongsung.has_jongsung(target):
                return target+"아"
            else:
                return target + "야"
        if result.startswith("이"):
            target += '이' * Jongsung.has_jongsung(target)
            result = result[1:]
        else:
            if Jongsung.has_jongsung(target) and not result.startswith("이"):
                target += "이"
        output = Josa.get_full_string(target, result)
    except Exception as e:
        if not Jongsung.is_hangle(target):
            output = target + result[-1]
        elif result.startswith("이는"):
            if Jongsung.has_jongsung(target):
                output = target + "이는"
            else:
                output = target + "는"
        elif result == "":
            output = target
        else:
            try:
                output = Josa.get_full_string(target, result[-1])
            except:
                output = target + result

    return output

print(process_josa(target,msg))

