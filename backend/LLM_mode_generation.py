# 1. Get question from LLM. Response should include question text, topic, variables, operations.
# 2. Solve question using Python (potentially Wolfram Alpha API) to obtain correct answer.
# 3. Generate 4 unique answer options, including correct answer, using LLM.
# 4. Send question and answer options to frontend to display to user.

from collections import Counter
import os
import re
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

def to_native(value): 
    if isinstance(value, Integer): 
        return int(value) 
    return value
def extract_json(text):
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    return match.group() if match else None

mode_prompt = f"""
You are to provide a Math question suitable for 6th–8th grade students. The response must be in JSON format. 
The Question Text, Question Topic, and Variables will be displayed. The Question Topic will be "mode".

mode example: "A teacher recorded the number of books students finished during a reading challenge. The numbers of books read by the students were: 3, 5, 2, 5, 4, 6, 5, 3. What is the mode of this dataset?" 

The question should include the list of values to be used when finding the solution. Each numeric value should be listed in the variables array.

Use a variety of integer values as long as the mode has a WHOLE number solution. Multiple different values can be repeated, as long as there is a SINGULAR
most common value as the mode. 

Return ONLY valid JSON with no text before or after the JSON object.

The JSON must follow this exact structure:

{{
  "question_text": "A teacher recorded the number of books students finished during a reading challenge. The numbers of books read by the students were: 3, 5, 2, 5, 4, 6, 5, 3. What is the mode of this dataset?",
  "question_topic": "mode",
  "variables": ["3,"5","2","5","4","6","5", "2"]
}}

Rules:
- "question_text" must be a SINGLE LINE string, any newline characters inside the string is invalid.
- Use ONLY double quotes for all strings.
- ALL values in "variables" MUST be numeric strings (e.g., "12", "45")
- DO NOT use words like "red", "blue", or any non-numeric values
- If any value is not a number, the response is invalid
- The JSON object must contain the keys "question_text", "question_topic", and "variables".
- "variables" must be a list of strings.
- No rationals or decimals allowed
- Do NOT include any text or characters outside the JSON object.
"""

solution = -1

def mode(values):
    vals = [sympify(v) for v in values]
    count = Counter(vals)
    max_count = max(count.values())

    return [key for key, value in count.items() if value == max_count]



#Potential improvements:
#Maybe can store previously generated question, feed into LLM to ensure next question is not the same.
#If solution is a fraction, at least one other generated response should be a fraction. 
def generate_mode_question(max_retries=3):
    for attempt in range(max_retries):
        if attempt > 0:
            prompt = mode_prompt + "\nREMEMBER: ONLY RETURN VALID JSON. NO EXTRA TEXT."
        else:
            prompt = mode_prompt

        response = generate(
            model="llama3.1:8b",
            prompt=prompt,
            options={
                "temperature": 0.9,
                "top_p": 0.9,
                "top_k": 75
            }
        )

        raw = extract_json(response.response)

        if not raw:
            print(f"[Attempt {attempt+1}] No JSON found")
            print(response.response)
            continue

        try:
            question_data = json.loads(raw)
        except Exception as e:
            print(f"[Attempt {attempt+1}] JSON parse failed:", e)
            print(response.response)
            continue

        # Validate required keys
        required_keys = ["variables", "question_text"]
        if not all(k in question_data for k in required_keys):
            print(f"[Attempt {attempt+1}] Missing keys:", question_data)
            continue

        # If we reach here → SUCCESS
        break

    else:
        # All retries failed
        raise ValueError("Failed to generate valid JSON after retries")
    
    parts = question_data['variables']
    solution = mode(parts)

    #print("Solution:", solution)
    solution = str(solution) if solution else None

    for attempt in range(max_retries):
        incorrect_solution_prompt = f"""
        Generate three incorrect numerical answer options for a math problem.
        Question:
        {question_data["question_text"]}
        Correct Answer:
        {solution}

        Rules:
        - NO additional text, characters, or symbols should accompany this response. Response should strictly include JSON formatted data.
        - The answers must NOT equal or simplify to {solution}
        - Unique, whole numbers numbers only. These numbers MUST come from the numeric values specified in the question that are not the solution.
        - NUMBERS must be represented as strings. For example, "0.5" or "1/2" are valid representations.
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
        if attempt > 0:
            incorrect_solution_prompt += "\nREMEMBER: ONLY RETURN VALID JSON. NO EXTRA TEXT."

        raw = extract_json(answer_response.response)

        if not raw:
            print(f"[Attempt {attempt+1}] No JSON found")
            print(answer_response.response)
            continue

        try:
            answer_data = json.loads(raw)
        except Exception as e:
            print(f"[Attempt {attempt+1}] JSON parse failed:", e)
            print(answer_response.response)
            continue

        # Validate required keys
        required_keys = ["incorrect_answers"]
        if not all(k in answer_data for k in required_keys):
            print(f"[Attempt {attempt+1}] Missing keys:", answer_data)
            continue

        # If we reach here → SUCCESS
        break

    else:
        # All retries failed
        raise ValueError("Failed to generate valid JSON after retries")

    #combining generated incorrect responses with correct solution. 
    incorrect_data = answer_data

    answers = incorrect_data["incorrect_answers"] + [str(solution)]
    random.shuffle(answers)

    #Build final JSON
    return {
        "question_text": question_data["question_text"],
        "answer_options": answers,
        "correct_answer": solution
    }


#display on flask
# app= Flask(__name__)
# CORS(app)
# @app.route("/")
# def display_question():
#     return jsonify(generate_algebra_question())

