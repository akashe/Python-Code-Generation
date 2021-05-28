import re
from tokenize import tokenize
from io import BytesIO

python_code = '''
def compute_lcm(x, y):\n\tif x > y:\n\t\tgreater = x\n\telse:\n\t\tgreater = y\n\twhile(True):\n\t\tif((greater % x == 0) and (greater % y == 0)):\n\t\t\tlcm = greater\n\t\t\tbreak\n\t\tgreater += 1\n\treturn lcm
'''
# exec(python_code)
# python_code= python_code.replace("\t","\t ")

tokens = []
try:
    a = list(tokenize(BytesIO(python_code.encode('utf-8')).readline))
    indents = 0
    last_token = a[0]
    for i__ in a[1:-1]:
        if i__.exact_type == 56:
            tokens.append("\n")
            continue
        if i__.exact_type == 6: # Dedent
            indents -= 1
        if i__.exact_type == 5: # Indent
            indents += 1
        if last_token.exact_type == 4: # Newline
            tokens.append(indents*'\t')

        if i__.exact_type == 3:
            if re.match(r'^f"',i__[1]):
                string_tokens = ['f"']+[k__ for k__ in i__[1][2:]]
            elif re.match(r"^f'",i__[1]):
                string_tokens = ["f'"]+[k__ for k__ in i__[1][2:]]
            else:
                string_tokens = [k__ for k__ in i__[1]]
            tokens = tokens + string_tokens
        elif i__.exact_type == 6 or i__.exact_type == 5:
            passz
        else:
            tokens.append(i__[1])

        last_token = i__
except Exception:
    print("Error in tokenization")

print("a")