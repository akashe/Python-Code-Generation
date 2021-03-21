import re
from tokenize import tokenize
from io import BytesIO

python_code = '''
def perfect_number_checker(num):
    i = 2
    sum = 1
    while(i <= num//2 ) :
        if (num % i == 0) :
            sum += i
        i += 1
    if sum == num :
        return f'{num} is a perfect number'

    else :
        return f'{num} is not a perfect number'
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
            pass
        else:
            tokens.append(i__[1])

        last_token = i__
except Exception:
    print("Error in tokenization")

print("a")