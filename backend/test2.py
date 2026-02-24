#Goal is to combine flask/llm communication to display the generated question on the frontend. 
#python -m flask --app test2 run  [in terminal to run flask app]

#Eventually want to communicate with Flask/React to send LLM results to frontend. 

from ollama import chat, generate
from ollama import ChatResponse
import json
from flask import Flask, jsonify

with open("data/testquestions.json", 'r') as file:
    questions = json.load(file)

# response: ChatResponse = generate(model="llama3.1:8b", prompt=f"From the given question list, please select a random question: {str(questions)}. The response should only include the Question ID and Question Text.")

#Definently not perfect but is at least able to display the question and id consistently. 
app = Flask(__name__)
@app.route('/')
def generate_random():
    response = generate(model="llama3.1:8b", 
                        prompt=f"From the given question list, please select a random question: {str(questions)}. The response should only include the Question ID and Question Text.",
                        options = {"temperature": 0.7,
                                    "top_p": 100} #increase randomness, 
                        )
    
    return f'<p>{response.response}</p>' #response includes metadata, do response.response