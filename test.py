#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
input_str = """그랬구나..."그러나 이건 어떨까? 이것도 처리할 수 잇을까나! 하.하.하." 스스로를 부족하다고 느꼈다면 점점 00(이)를 작아지게 만들어 마음이 많이 힘들었을 것 같아..? 하지만 00아, 부족한 부분일지라도 스스로에 대해 깨달을 수 있다는 것은 엄청난 일이야..! 내가 생각하는 것보다 스스로의 부족을 알기 어려워 하는 사람들도 많거든? 거기다 00이는 그 마음에 대한 노력을 위해 여기까지 찾아와줬잖아! 그렇기 때문에 그 경험들로 00이의 모든 가치를 결정하지 않았으면 좋겠어."""
pattern = r"(?<=[.?!])\s+|\s+(?=[.?!])|\s+(?=\.\.\.)|\s+(?=\.\.)|\s+(?=\.\?)"

# Define the regular expression to match quoted substrings
# Find all occurrences of the quoted substrings


# Split the input string on the quoted substrings


# Combine the output list with the quoted substrings


# Output: ['안녕하세요.', '저는', "'병찬'", '이에요.', '오늘', '해볼', '요리는', '"카레"', '입니다.']

