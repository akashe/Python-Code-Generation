import re
from tokenize import tokenize
from io import BytesIO
import pickle


def format_solution(solution):
    '''
    Problem with this approach, when there are mulitple indent shift towards the left, this approach fails
    and for some reason it still has \n still left in the solutions.

    '''
    # remove empty lines first
    tmp_solution = []
    for sentence in solution:
        if sentence == '\n' or re.match(r' +\n|\t+\n', sentence):
            continue
        else:
            # remove trailing spaces
            # check if trailing spaces
            trailing_spaces = re.match(r'(^.*?)[ ]+\n', sentence)
            if trailing_spaces:
                sentence = re.sub(r'(^.*?)[ ]+\n', r'\1\n', sentence)
            tmp_solution.append(sentence)
    solution = tmp_solution

    def find_indent_value(starting_spaces_, indent_scheme_):
        sum_of_indents = 0
        for i, j in enumerate(indent_scheme_):
            sum_of_indents += j
            if sum_of_indents == starting_spaces_:
                break
        total_indents_ = i
        if total_indents_ < 0:
            raise Exception

        return total_indents_

    pruned_solution = []
    indent_scheme = []
    check_indentation_flag = True
    for sentence_number,sentence in enumerate(solution):
        starting_spaces = len(re.match(r'^([ ]*).*?', sentence)[1])
        if check_indentation_flag:
            possible_indent = starting_spaces - sum(indent_scheme)
            if possible_indent > 0 or sentence_number == 0: # checking sentence number to get the first indentation which cud be 0
                indent_scheme.append(possible_indent)
            check_indentation_flag = False
        if re.match(r'.*:\n', sentence):
            check_indentation_flag = True

        total_indents = find_indent_value(starting_spaces, indent_scheme)
        indent = total_indents * '\t'
        pruned_solution.append(re.sub(r'([ ]*)(.*?)\n', indent + r'\2\n', sentence))

    return pruned_solution


def getDataAnalysis():
    #########################
    # checking number of unique questions
    unique_questions = {}
    question = re.compile(r'^#[ ]?[0-9]*[.]?[ ]?(.*)')
    f = open("data/english_python_data_pruned.txt", "r")

    question_regex = re
    for line in f:
        match_object = question.match(line)
        if match_object and match_object[1] not in unique_questions:
            unique_questions[match_object[1]] = "aka"

    print(len(unique_questions))
    # for i in unique_questions:
    #     print(i)
    f.close()

    ########################
    # checking unique questions answer pairs
    unique_questions_with_different_solution = {}  # used to check for unique answers
    question_answer_pair = {}  # used to save solutions for unique questions
    f = open("data/english_python_data_pruned.txt", "r")

    solution = []
    for i, line in enumerate(f):
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
                            flag = 1
                    if flag:
                        unique_questions_with_different_solution[prev_match].append(solution_combined)
                        question_answer_pair[prev_match].append(solution)
            solution = []
            prev_match = match_object[1]
        else:
            solution.append(line)

    sum_ = 0
    for i in unique_questions_with_different_solution:
        sum_ += len(unique_questions_with_different_solution[i])

    print(f' total unique questions and solutions pairs are {sum_}')
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
    # 3. remove lines with only \n or only spaces
    # 4. TODO: Removing spaces around operators like ==, &&

    keyword_analysis = {}
    questions_list = []
    answers_list = []
    for i in question_answer_pair:
        for j in question_answer_pair[i]:
            questions_list.append(i)
            formatted_solution = format_solution(j)
            answers_list.append(formatted_solution)
            k = "".join(formatted_solution)
            try:
                a = list(tokenize(BytesIO(k.encode('utf-8')).readline))
                for i__ in a[1:-1]:
                    if i__[1] not in keyword_analysis:
                        keyword_analysis[i__[1]] = 1
                    else:
                        keyword_analysis[i__[1]] += 1
            except Exception:
                print("Error in tokenization")

    print('Total len of the keyword dictionary is ', len(keyword_analysis))
    print(keyword_analysis)
    # Note:
    # A lot of keywords are names of variable of strings or numbers
    # I might have to character wise input dictionary but that would make the problem more
    # difficult to solve for the network
    # Will try BPE?



def getData(path):
    '''
    Function to return data
    :return: two lists of questions and their formatted answers
    '''
    question = re.compile(r'^#[ ]?[0-9]*[.]?[ ]?(.*)')
    unique_questions_with_different_solution = {}  # used to check for unique answers
    question_answer_pair = {}  # used to save solutions for unique questions
    f = open(path, "r")

    solution = []
    for i, line in enumerate(f):
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
                            flag = 1
                    if flag:
                        unique_questions_with_different_solution[prev_match].append(solution_combined)
                        question_answer_pair[prev_match].append(solution)
            solution = []
            prev_match = match_object[1]
        else:
            solution.append(line)

    questions_list = []
    answers_list = []
    for i in question_answer_pair:
        for j in question_answer_pair[i]:
            questions_list.append(i)
            formatted_solution = format_solution(j)
            answers_list.append("".join(formatted_solution))

    return questions_list,answers_list


def getTokenizer(python_code):
    '''
    Function that returns tokenized python code
    :return: tokenized code
    '''
    tokens = []
    try:
        a = list(tokenize(BytesIO(python_code.encode('utf-8')).readline))
        for i__ in a[1:-1]:
            if i__.exact_type == 3:
                string_tokens = [k__ for k__ in i__[1]]
                tokens = tokens + string_tokens
            elif i__.exact_type == 6:   # removing dedent tokens
                continue
            else:
                tokens.append(i__[1])
    except Exception:
        print("Error in tokenization")

    return tokens

# getDataAnalysis()
# getData("data/english_python_data_pruned.txt")
