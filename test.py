import re
from tokenize import tokenize
from io import BytesIO

python_code = 'import functools\ndef longestWord(word_list):\n\tif word_list is None or isinstance(word_list, list) == False or len(word_list) == 0:\n\t\traise ValueError("Input word_list to \'function longestWord must be list of words of size at least 1")\n\tif len(word_list) == 1:\n\t\treturn word_list[0]\n\telse: \n\t\treturn functools.reduce(lambda x,y: x if len(x) >= len(y) else y, word_list) '

# exec(python_code)


tokens = []
try:
    a = list(tokenize(BytesIO(python_code.encode('utf-8')).readline))
    for i__ in a[1:-1]:
        if i__.exact_type == 3:
            string_tokens = [k__ for k__ in i__[1]]
            tokens = tokens + string_tokens
        else:
            tokens.append(i__[1])
except Exception:
    print("Error in tokenization")

print("a")