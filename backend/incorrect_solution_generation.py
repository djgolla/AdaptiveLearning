#Three options
#Using this instead of creating w/ LLM for increased consistency and speed. 
#1. Algebra, angles, geometry, mean, median, probability - take solution, add/subtract random number. 
#2. Expressions - random term w/ 'x' as variable. 
#3. Rationals - need random numerator and denominator.
#Ordering already has solution generation, may move here. 

import random
import sympy as sp 
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application
) #treat 2x as 2*x for sympy parsing
transformations = (standard_transformations + (implicit_multiplication_application,))


#POSSIBLY - for method 1, find how many decimal places answer has and round to match. 

#method 1
def generate_general_incorrect_answers(answer): 
    generated_answers = []
    
    while len(generated_answers) < 3:
        operation = random.choice(["+", "-", "*"])
        if operation == "+":
            low = random.randint(1, 10)
            high = random.randint(11, 25)
            incorrect_answer = answer + random.randint(low, high)
        elif operation == "-":
            low = random.randint(1, 10)
            high = random.randint(11, 25)
            if (answer - high) < 0:
                low = 1
                high = answer
            backup = random.randint(1, 5) #low val to ensure we dont get negatives. 
            incorrect_answer = max(answer - random.randint(low, high), backup)
        elif operation == "*":
            factor = random.randint(2, 5)
            incorrect_answer = answer * factor
        incorrect_answer = round(incorrect_answer, 2) #limit to 2 decimal places if needed.
        sp.sympify(incorrect_answer) #ensure answer is in simplest form, also converts to fraction if needed.
        
        if incorrect_answer != answer and incorrect_answer not in generated_answers: #ensure we dont add the correct answer or duplicates.
            generated_answers.append(incorrect_answer)
        else:
            continue 
    return generated_answers

# #recieve input like 2x. not sure if needed or if can treat the same.
# def generate_incorrect_simplied_answers(answer):


#maybe take numerator/denomiator as input. 
def generate_incorrect_rational(answer): 
    generated_answers = []
    while len(generated_answers) < 3:
        num = random.randint(1, 20)
        denom = random.randint(1, 20)
        
        #avoid "1" answers, some more randomness. 
        if num == denom:
            if num <= 8:
                num += random.randint(1, 5)
            elif num >= 15:
                num -= random.randint(1, 5)
            else:
                num += random.randint(-3, 3)

        incorrect_answer = sp.Rational(num, denom)
        sp.sympify(incorrect_answer) #ensure answer is in simplest form

        if incorrect_answer != answer and incorrect_answer not in generated_answers: #ensure we dont add the correct answer or duplicates.
            generated_answers.append(incorrect_answer)
        else:
            continue 

    return generated_answers