import os
from supabase import create_client, Client #pip install supabase
from dotenv import load_dotenv   #pip install dotenv
from ollama import chat, generate
from ollama import ChatResponse
import json
from flask import Flask, jsonify
from flask_cors import CORS #pip install flask-cors

#NOT WORKING RN, need to create supabase table first. 

#Setup Flask app and enable CORS to communicate with React frontend
app = Flask(__name__)
CORS(app)

#Obtain accuracy data from frontend. 
load_dotenv() #need to create .env file in backend folder with SUPABASE_URL and SUPABASE_KEY
url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)  

#isolating accuracy values. 
if (supabase.from_("user_accuracies").select("*").execute().data != None): #Will need to either error check each individual value, or enforce a defauly value of 0 if not provided.
    accuracies = {
        "math_accuracy": supabase.from_("user_accuracies").select("math_accuracy").execute().data,
        "science_accuracy": supabase.from_("user_accuracies").select("science_accuracy").execute().data,
        "english_accuracy": supabase.from_("user_accuracies").select("english_accuracy").execute().data,
        "history_accuracy": supabase.from_("user_accuracies").select("history_accuracy").execute().data
    }

prompt = "Here are the average accuracies for a student in different subjects: " + str(accuracies) + \
    ". From the provided data, please generate a question that would be most likely to lower the student's stress. The student is between the 6-8th grade range. + \
    The response should be in JSON format and include the question text, four unique string answer options, and the string of the correct answer. No other text should accompany the response."



#TEST ROUTES 
@app.route("/api/data", methods=["GET"])
def get_data(): 
    data = supabase.from_("user_accuracies").select("*").execute()
    print(data.data)
    return jsonify(data.data)

@app.route("/")
def home():
    return "Flask backend is running!"

@app.route("/generate-question")
def generate_question():
    response = generate(model="llama3.1:8b", 
                        prompt=prompt,
                        options = {"temperature": 0.7,
                                    "top_p": 100} #increase randomness, 
                        )
    return jsonify({"question": response.response}) #response includes metadata, do response.response

if __name__ == "__main__": #run flask app on port 5000, separate from React frontend which runs on 5173
    app.run(debug=True, port=5000)