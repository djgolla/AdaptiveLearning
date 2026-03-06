# 1. Get question from LLM. Response should include question text, topic, variables, operations.
# 2. Solve question using Python (potentially Wolfram Alpha API) to obtain correct answer.
# 3. Generate 4 unique answer options, including correct answer, using LLM.
# 4. Send question and answer options to frontend to display to user.

#Potential topic types. 

#Topics: Ordering (e.g order numbers (including negatives and two digit decimal values) from least to greatest or vice versa). For least to greatest the question topic should be 'ordering-least', otherwise it is 'ordering-greatest'. 
#Rationals: (operations involving two fractions. Varaibles should be in the format '2/5' for a single fraction). The expected operation type should also be included.
#Operations: Variables should be in the format '2/5' for a single fraction, or 'x' for a variable. Additionally, the operations should be clearly defined from left to right using '+', '-', '*', '/' to indicate the operations. Both variables and operations will be realized left to right. For example, a question with variables '2', '3', '4', '+', '*' will be seen as 2 + 3 * 4, and the operations will be performed left to right, so it will be (2 + 3) * 4 = 20.
#Expressions: ex 'Simplify the expression 4(2x - 3).' The question should include the expression to be simplified, and the expected operation type should also be included. Variables should be in the format 'x' for a variable, and operations should be defined using '+', '-', '*', '/' to indicate the operations. The operations will be performed left to right, so for example, a question with variables '2x', '-3', '4', '*', will be seen as 2x - 3 * 4, and the operations will be performed left to right, so it will be (2x - 3) * 4 = 8x - 12.
#Algebra: ex 'Solve for x: 2x + 3 = 7.' The question should include the equation to be solved, and the expected operation type should also be included. Variables should be in the format 'x' for a variable, and operations should be defined using '+', '-', '*', '/' to indicate the operations. The operations will be performed left to right, so for example, a question with variables '2x', '+', '3', '=', '7', will be seen as 2x + 3 = 7, and the operations will be performed left to right, so it will be 2x = 4, and x = 2.
#Geometry: ex 'Find the area of a circle with a radius of 6 cm.' The question should include the geometric figure to be analyzed, and the expected operation type should also be included. Variables should be in the format '6 cm' for a variable, and operations should be defined using '+', '-', '*', '/' to indicate the operations. For example, a question with variables 'radius', '6 cm', 'area', '*', 'pi', will be seen as area = radius * radius * pi, and the operations will be performed left to right, so it will be area = 6 cm * 6 cm * pi = 36pi cm^2. Area, Perimeter, and Volume for simple shapes are potential questions. 
#Angle relationships: 'IF two angles are complementary and one angle measures 35 degrees, what is the measure of the other angle?' The question should include the angle relationship to be analyzed, and the expected operation type should also be included. Variables should be in the format '35 degrees' for a variable, and operations should be defined using '+', '-', '*', '/' to indicate the operations. For example, a question with variables 'angle1', '35 degrees', 'angle2', '+', 'complementary', will be seen as angle1 + angle2 = 90 degrees, and the operations will be performed left to right, so it will be 35 degrees + angle2 = 90 degrees, and angle2 = 55 degrees.
#Mean: Provide a short to medium sized integer or decimal variable dataset. 
#Median: Provide a short to medium sized integer or decimal variable dataset.
#Mode: Provide a short to medium sized integer or decimal variable dataset.
#Probability: ex 'A bag contains 5 red marbles, 3 blue marbles, and 2 green marbles. If a marble is drawn at random, what is the probability of drawing a red marble?' The question should include the probability scenario to be analyzed, and the expected operation type should also be included. Variables should be in the format '5 red marbles' for a variable, and operations should be defined using '+', '-', '*', '/' to indicate the operations. For example, a question with variables 'red marbles', '5', 'blue marbles', '3', 'green marbles', '2', 'total marbles', '+', 'probability of red marble', '/', 'total marbles', will be seen as probability of red marble = red marbles / total marbles, and the operations will be performed left to right, so it will be probability of red marble = 5 / (5 + 3 + 2) = 5/10 = 1/2.

import os
import random
from supabase import create_client, Client #pip install supabase
from dotenv import load_dotenv   #pip install dotenv
from ollama import chat, generate
from ollama import ChatResponse
import json
from flask import Flask, jsonify
from flask_cors import CORS #pip install flask-cors
import sympy as sp #pip install sympy
from sympy import symbols, Eq, solve, sympify, Integer
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application
) #treat 2x as 2*x for sympy parsing

# Enable implicit multiplication (2x → 2*x)
transformations = (standard_transformations + (implicit_multiplication_application,))

def to_native(value): 
    if isinstance(value, Integer): 
        return int(value) 
    return value

#algebra solver works, but questions are very similar.
#POSSIBLY - can have separate prompts for each topic type. Randomize which gets selected. 
#ISSUE: saw a case where correct answer was not in answer options. 
general_prompt = "You are being asked to provide a Math question suitable for 6th-8th grade students. The response should be in JSON format. The Question Text, Question Topic, and any Variables will be displayed." \
"Here are the potential topic types: Ordering, Rationals, Operations, Expressions, Algebra, Geometry, Angle relationships, Mean, Median, Mode, Probability. Below is some guidance for the response formatting depending on the question topic." \
"Topics: Ordering (e.g order numbers (including negatives and two digit decimal values) from least to greatest or vice versa). For least to greatest the question topic should be 'ordering-least', otherwise it is 'ordering-greatest'. " \
"Rationals: (operations involving two fractions. Varaibles should be in the format '2/5' for a single fraction). The expected operation type should also be included. Ex: '2/5' '+' '1/3' "  \
"Operations: Variables should be in the format '2/5' for a single fraction, or 'x' for a variable. Additionally, the operations should be clearly defined from left to right using '+', '-', '*', '/' to indicate the operations. Both variables and operations will be realized left to right. " \
"Expressions: ex 'Simplify the expression 4(2x - 3).' The question should include the expression to be simplified, and the expected operation type should also be included. Variables should be in the format 'x' for a variable, and operations should be defined using '+', '-', '*', '/' to indicate the operations. The operations will be performed left to right. 4(2x - 3) should be displayed as '4' '*' '2x' '-' '4' '*' '3' "  \
"Algebra: ex 'Solve for x: 2x + 3 = 7.' The question should include the equation to be solved, and the expected operation type should also be included. Variables should be in the format 'x' for a variable, and operations should be defined using '+', '-', '*', '/' to indicate the operations. The operations will be performed left to right, so for example, a question with variables '2x', '+', '3', '=', '7', will be seen as 2x + 3 = 7. " \
"Geometry: ex 'Find the area of a circle with a radius of 6 cm.' The question should include the geometric figure to be analyzed, and the expected operation type should also be included. The first variable should be the operation type - either Area, Perimeter, or Volume. Additionally variables will be the shape's resective dimensions. Operations do not need to be included. " \
"Angle relationships: 'IF two angles are complementary and one angle measures 35 degrees, what is the measure of the other angle?' The question should include the angle relationship to be analyzed, and the expected operation type should also be included. Variables should be in the format '35 degrees' for a variable, and operations should be defined using '+', '-', '*', '/' to indicate the operations. For example, a question with variables 'angle1', '35 degrees', 'angle2', '+', 'complementary', will be seen as angle1 + angle2 = 90 degrees, and the operations will be performed left to right, so it will be 35 degrees + angle2 = 90 degrees, and angle2 = 55 degrees. " \
"Mean: Provide a short to medium sized integer or decimal variable dataset. " \
"Median: Provide a short to medium sized integer or decimal variable dataset." \
"Mode: Provide a short to medium sized integer or decimal variable dataset." \
"Probability: ex 'A bag contains 5 red marbles, 3 blue marbles, and 2 green marbles. If a marble is drawn at random, what is the probability of drawing a red marble?' The question should include the probability scenario to be analyzed, and the expected operation type should also be included. Variables should be in the format '5 red marbles' for a variable, and operations should be defined using '+', '-', '*', '/' to indicate the operations. For example, a question with variables 'red marbles', '5', 'blue marbles', '3', 'green marbles', '2', 'total marbles', '+', 'probability of red marble', '/', 'total marbles', will be seen as probability of red marble = red marbles / total marbles, and the operations will be performed left to right, so it will be probability of red marble = 5 / (5 + 3 + 2) = 5/10 = 1/2." \
"The response should be solely in JSON format without any additional text, characters, or symbols before and after {}. The JSON should include the following keys: 'question_text', 'question_topic', and 'variables'. The value for 'question_text' should be a string of the question being asked. The value for 'question_topic' should be a string of the question topic, which should be one of the previously defined topic types. The value for 'variables' should be a list of the variables included in the question, with each variable formatted as previously defined for each topic type. For example, if the question is 'Solve for x: 2x + 3 = 7.' then the response should strictly be in the format: { 'question_text': 'Solve for x: 2x + 3 = 7.', 'question_topic': 'algebra', 'variables': ['2x', '+', '3', '=', '7'] }. If a variable is in use like '2x', 'x' should always be the unknown value. To be JSON compliant double quotes should be used instead." \
"FOR TESTING PURPOSES, PLEASE GENERATE A QUESTION ON THE TOPIC OF Algebra."


algebra_prompt = f"""
You are to provide a Math question suitable for 6th–8th grade students. The response must be in JSON format. 
The Question Text, Question Topic, and Variables will be displayed. The Question Topic will be "algebra".

Algebra example: "Solve for x: 2x + 3 = 7." 
The question should include the equation to be solved. Variables must be formatted as strings such as "x", and operations must be 
represented using the symbols "+", "-", "*", "/". For example, the variables list ["2x", "+", "3", "=", "7"] represents the equation 2x + 3 = 7.

There may be up to three operations on the left-hand side, and up to two terms may contain the variable "x". 
Use a variety of integer values as long as the equation has a valid solution.

Return ONLY valid JSON with no text before or after the JSON object.

The JSON must follow this exact structure:

{{
  "question_text": "Solve for x: 2x + 3 = 7.",
  "question_topic": "algebra",
  "variables": ["2x", "+", "3", "=", "7"]
}}

Rules:
- Use ONLY double quotes for all strings.
- The JSON object must contain the keys "question_text", "question_topic", and "variables".
- "variables" must be a list of strings.
- Do NOT include any characters outside the JSON object.
"""

solution = -1


#Potential improvements:
#Maybe can store previously generated question, feed into LLM to ensure next question is not the same.
#If solution is a fraction, at least one other generated response should be a fraction. 
def generate_algebra_question():
    response = generate(model="llama3.1:8b", 
                        prompt=algebra_prompt,
                        options = {"temperature": 0.9,
                                    "top_p": 0.9,
                                    "top_k": 75} #increase randomness, 
                        )
    if (response.response.startswith("{") and response.response.endswith("}")):
        question_data = json.loads(response.response)
    
    parts = question_data['variables']
    equation_stra = "".join(parts) #turn individual variables/operations into a single string to be parsed by sympy
    x = symbols('x') #define variable for sympy
    left, right = equation_stra.split('=') #split equation into left and right parts
    left_expr = parse_expr(left, transformations=transformations)
    right_expr = parse_expr(right, transformations=transformations)
    equation = Eq(left_expr, right_expr) 
    solution = solve(equation, x) #solve for x
    #print("Solution:", solution)
    solution = str(solution[0]) if solution else None

    incorrect_solution_prompt = f"""
    Generate three incorrect numerical answer options for a math problem.
    Question:
    {question_data["question_text"]}
    Correct Answer:
    {solution}

    Rules:
    - NO additional text, characters, or symbols should accompany this response. Response should strictly include JSON formatted data.
    - The answers must NOT equal or simplify to {solution}
    - Unique numbers only 
    - Only numbers or simple numeric strings are allowed. Do NOT use brackets, fractions, or expressions.
    - No fractions or expressions
    - Return JSON format: each array value of incorrect_answers should be a separate incorrect answer
    {{
    "incorrect_answers": ["x","x","x"]
    }}
    """

    if (solution != None):
        answer_response = generate(model="llama3.1:8b",
                                prompt=incorrect_solution_prompt,
                                options = {"temperature": 0.4,
                                            "top_p": 0.9,
                                            "top_k": 40}) #slightly less randomness, 

    #combining generated incorrect responses with correct solution. 
    incorrect_data = json.loads(answer_response.response)

    answers = incorrect_data["incorrect_answers"] + [str(solution)]
    random.shuffle(answers)

    #Build final JSON
    return {
        "question_text": question_data["question_text"],
        "answer_options": answers,
        "correct_answer": solution
    }


#trying to now display on flask
app= Flask(__name__)
CORS(app)
@app.route("/")
def display_question():
    return jsonify(generate_algebra_question())



#ISSUES - correct answer still not being included. Format is often incorrect
# solution_prompt = f"""
#         You must generate four answer options for a math question.

#         THE CORRECT ANSWER MUST APPEAR EXACTLY AS: {solution}
#         Do not simplify, modify, or reformat the correct answer.

#         Return ONLY valid JSON in this structure. the answer_options values should be filled with four numerical values, one of which being {solution}:

#         {{
#         "answer_options": ["x", "x", "x", "x"],
#         "correct_answer": "{solution}"
#         }}

#         Rules:
#         - answer_options must contain exactly 4 unique values.
#         - One of the values MUST be the exact correct answer: {solution}
#         - The other 3 values must be plausible incorrect answers.
#         - Do NOT include any text outside the JSON.
#         - Do NOT include question_text.
#         - All values must be numbers or strings representing numbers.
#         - Randomize the order of answer_options.
#         """