import re

#########################
# checking number of unique questions
unique_questions = {}
question = re.compile(r'^#[ ]?[0-9]*[.]?[ ]?(.*)')
f = open("english_python_data_pruned.txt","r")

question_regex = re
for line in f:
    match_object = question.match(line)
    if match_object and match_object[1] not in unique_questions:
        unique_questions[match_object[1]]="aka"

print(len(unique_questions))
# for i in unique_questions:
#     print(i)
f.close()

########################
# checking unique questions answer pairs
unique_questions_with_different_solution = {} # used to check for unique answers
question_answer_pair = {} # used to save solutions for unique questions
f = open("english_python_data_pruned.txt","r")

solution = []
for i,line in enumerate(f):
    match_object = question.match(line)
    if match_object:
        if len(solution) == 0:
            prev_match = match_object[1]
            continue
        else:
            solution_combined = " ".join(solution).replace('\n', "").replace('\t', "").replace(" ", "")
            if prev_match not in unique_questions_with_different_solution:
                unique_questions_with_different_solution[prev_match] = [solution_combined]
                question_answer_pair[prev_match] = [solution]
            else:
                flag = 0
                for j in unique_questions_with_different_solution[prev_match]:
                    if j != solution_combined:
                        flag =1
                if flag:
                    unique_questions_with_different_solution[prev_match].append(solution_combined)
                    question_answer_pair[prev_match].append(solution)
        solution = []
        prev_match = match_object[1]
    else:
        solution.append(line)

sum = 0
for i in unique_questions_with_different_solution:
    sum += len(unique_questions_with_different_solution[i])

print(f' total unique questions and solutions pairs are {sum}')
f.close()

############################
# Extracting question answers pairs using Regex

# f = open("english_python_data_pruned.txt","r")
# entire_file = f.read()
# question_and_answer = r'^#[ ]?[0-9]*[.]?[ ]?(.*?)$([\S\s]*)-------------'
# pairs = re.findall(question_and_answer,entire_file,re.MULTILINE)
#


###########################
# Formatting solutions
# 1. convert 4 space or 3 space indentation to \t
# 2. removing trailing spaces
# 3. remove lines with only \n
# 4. TODO: Removing spaces around operators like ==, &&

def format_solution(solution):
    '''
    Problem with this approach, when there are mulitple indent shift towards the left, this approach fails
    and for some reason it still has \n still left in the solutions.

    '''
    # remove empty lines first
    tmp_solution = []
    for sentence in solution:
        if sentence == '\n' or sentence == "\n" or sentence =='\r':
            continue
        else:
            # remove trailing spaces
            # check if trailing spaces
            trailing_spaces = re.match(r'(^.*?)[ ]+\n',sentence)
            if trailing_spaces:
                sentence = re.sub(r'(^.*?)[ ]+\n',r'\1\n',sentence)
            tmp_solution.append(sentence)
    solution = tmp_solution

    i = 0
    pruned_solution = []
    # The reason for doing seperately for the first line is to tackle the cases where there is
    # a starting space for all the lines of the code
    previous_starting_spaces = len(re.match(r'^([ ]*).*?',solution[0])[1])
    # remove starting spaces of first line
    pruned_solution.append(re.sub(r'([ ]*)(.*?)\n',r'\2\n',solution[0]))
    for sentence in solution[1:]:
        present_starting_spaces = len(re.match(r'^([ ]*).*?',sentence)[1])
        if present_starting_spaces < previous_starting_spaces:
            if i >= 1:
                i -= 1
        if present_starting_spaces > previous_starting_spaces:
            i += 1
        indent = i * '\t'
        pruned_solution.append(re.sub(r'([ ]*)(.*?)\n',indent+r'\2\n',sentence))
        previous_starting_spaces = present_starting_spaces

    return pruned_solution


questions_list = []
answers_list = []
for i in question_answer_pair:
    for j in question_answer_pair[i]:
        questions_list.append(i)
        answers_list.append(format_solution(j))

f = open("test.txt","w")
for i in answers_list:
    for j in i:
        f.write(j)


