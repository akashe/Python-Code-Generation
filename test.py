import re
from tokenize import tokenize
from io import BytesIO

python_code = '''
num = 13
factorial = 1

if num < 0:
   print("No factorials for negative numbers!")

elif num == 0:
   print("The factorial of 0 is 1")\

else:
   for i in range(1,num + 1):
       factorial = factorial*i
   print(f"The factorial of {num} is {factorial}")'
'''
# exec(python_code)


tokens = []
try:
    a = list(tokenize(BytesIO(python_code.encode('utf-8')).readline))
    for i__ in a[1:-1]:
        if i__.exact_type == 3:
            if re.match(r'^f"',i__[1]):
                string_tokens = ['f"']+[k__ for k__ in i__[1][2:]]
            elif re.match(r"^f'",i__[1]):
                string_tokens = ["f'"]+[k__ for k__ in i__[1][2:]]
            else:
                string_tokens = [k__ for k__ in i__[1]]
            tokens = tokens + string_tokens
        elif i__.exact_type == 6:
            continue
        else:
            tokens.append(i__[1])
except Exception:
    print("Error in tokenization")

print("a")