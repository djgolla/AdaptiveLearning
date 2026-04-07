#Ideally - this will be called from LLMTest2 to randomly select a topic. Then can call methods from other files for specific question generation. 
import os
from flask import Flask, jsonify
from flask_cors import CORS #pip install flask-cors
from supabase import create_client, Client #pip install supabase
from dotenv import load_dotenv   #pip install dotenv
from ollama import generate
import json
import random
from collections import deque
import LLM_algebra_generation, LLM_ordering_generation, LLM_rationals_generation, LLM_mean_generation, LLM_median_generation
import LLM_mode_generation, LLM_probability_generation, LLM_geometry_generation, LLM_angle_relationship_generation, LLM_expressions_generation
#python -m flask --app LLM_topic_decider run

#connect with supabase 
load_dotenv() 
url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url,key)

#Store 10 
history = {
    "global": deque(maxlen=10), #stores last 10 questions regardless of topic, can use to ensure no repeats
    "geometry": deque(maxlen=10),
    "algebra": deque(maxlen=10),
    "expressions": deque(maxlen=10),
    "ordering": deque(maxlen=10),
    "rationals": deque(maxlen=10),
    "mean": deque(maxlen=10),
    "median": deque(maxlen=10),
    "mode": deque(maxlen=10),
    "probability": deque(maxlen=10),
    "angle_relationships": deque(maxlen=10)
}

def extract_json(text):
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]

    return None

def LLM_topic_decider(user_id): 

    #not sure if correct 
    accuracy_response = supabase.table("user_math_performance") \
        .select("correct_questions,attempted_questions, math_topics(topic_name)") \
        .eq("user_id", user_id) \
        .execute()

    json_response = jsonify(accuracy_response)

    prompt = f"""
            You are an adaptive learning algorithm for math education. Your task is to select the most appropriate math topic for a student based on their past performance data. 
            The student's performance data includes the number of correct questions, attempted questions, and the specific math topics they have engaged with.
            The math topics include: geometry, algebra, expressions, ordering, rationals, mean, median, mode, probability, angle_relationships.

            Analyze the student's performance data and select the topic they are struggling with the most, which is determined by the lowest accuracy (correct_questions/attempted_questions) across topics.
            Here is the student's current performance: {json_response}. Here is a history of most recent questions asked: {history}
            
            Your job is to support the student's learning and growth. You will do this in two ways. 
            1) Select the topic for the next question. 
            2) Select the difficulty level for the question. This can be "easy", "medium", or "hard"

            When selecting both options, consider the following. If a student has recently struggled on questions in a specific topic, it may be best to refrain from asking 
            a question from that topic or lowering the selected difficulty level. Students should also be evaluated in every topic, so ensure that a spread of topics and appropriate difficulties are selected.

            The student should not feel overwhelmed by questions. Initial questions for a topic should be "easy" or "medium". Once a student has demonstrated skill in the subject through high accuracy (>70%),
            "hard" difficulty questions can be interspersed within that topic.  
           
            YOUR RESPONSE WILL BE IN JSON FORMAT, and MUST NOT have and leading or trailing words, characters, or symbols. 
            The JSON must follow this exact structure: 
            This is an example where "angle_relationships" and "medium" were your choices. 
            {{
                "topic": "angle_relationships",
                "difficulty": "medium"
            }}
            """
    for attempt in range(3): 
        llm_response = generate(
            model = "llama3.1:8b",
            prompt = prompt,
            options={
                    "temperature": 1.1, #more creativity
                    "top_p": 0.95, #more diversity
                    "top_k": 100 #broader token sampling.
                }
        )

        raw = extract_json(llm_response.response)
        if not raw:
            print(f"[Attempt {attempt+1}] No JSON found")
            print(llm_response.response)
            continue

        try:
            topic_data = json.loads(raw)
        except Exception as e:
                print(f"[Attempt {attempt+1}] JSON parse failed:", e)
                print(llm_response.response)
                continue

        # Validate required keys
        required_keys = ["topic", "difficulty"]
        if not all(k in topic_data for k in required_keys):
            print(f"[Attempt {attempt+1}] Missing keys:", topic_data)
            continue

        # If we reach here → SUCCESS
        break

    else:
        # All retries failed
        raise ValueError("(topic selection)Failed to generate valid JSON after retries")
    
    topic = topic_data["topic"]
    difficulty = topic_data["difficulty"]

    #Then need another function, sending these as parameters to generate question. (possibly also send accuracy/stress)
    #Need to update generation prompts to consider difficulty level. 




#select from 11 math topics
#POSSIBLY can have LLM select topic first given things like stress/accuracy

#TO-DO: Implement LLM-based topic selection, provide (optional) accuracy/stress values from frontend. 
def randomize_question():
    num = random.randint(0, 9) #get int from 0-9 inclusive
    print("num", num)
    match num:
        case 0:
            # Ordering, need to call generate question 
            response = LLM_ordering_generation.generate_ordering_question(history["global"], history["ordering"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "ordering"})
            history["ordering"].append({
                    "text": response["question_text"],
                    "topic": "ordering"}) 

        case 1:
            # Rationals
            response = LLM_rationals_generation.generate_rational_question(history["global"], history["rationals"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "rationals"})
            history["rationals"].append({
                    "text": response["question_text"],
                    "topic": "rationals"})
        case 2: 
            #expressions
            response = LLM_expressions_generation.generate_expression_question(history["global"], history["expressions"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "expressions"})
            history["expressions"].append({
                    "text": response["question_text"],
                    "topic": "expressions"})
        case 3: 
            #algebra
            response = LLM_algebra_generation.generate_algebra_question(history["global"], history["algebra"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "algebra"})
            history["algebra"].append({
                    "text": response["question_text"],
                    "topic": "algebra"})
        case 4: 
            #geometry
            response = LLM_geometry_generation.generate_geometry_question(history["global"], history["geometry"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "geometry"})
            history["geometry"].append({
                    "text": response["question_text"],
                    "topic": "geometry"})
        case 5:
            #angle relationship
            response = LLM_angle_relationship_generation.generate_angle_relationship_question(history["global"], history["angle_relationships"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "angle_relationships"})
            history["angle_relationships"].append({
                    "text": response["question_text"],
                    "topic": "angle_relationships"})
        case 6:
            #mean
            response = LLM_mean_generation.generate_mean_question(history["global"], history["mean"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "mean"})
            history["mean"].append({
                    "text": response["question_text"],
                    "topic": "mean"})
        case 7: 
            #median
            response = LLM_median_generation.generate_median_question(history["global"], history["median"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "median"})
            history["median"].append({
                    "text": response["question_text"],
                    "topic": "median"})
        case 8:
            #mode
            response = LLM_mode_generation.generate_mode_question(history["global"], history["mode"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "mode"})
            history["mode"].append({
                    "text": response["question_text"],
                    "topic": "mode"})
        case 9:
            #probability
            response = LLM_probability_generation.generate_probability_question(history["global"], history["probability"])
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "probability"})
            history["probability"].append({
                    "text": response["question_text"],
                    "topic": "probability"})

    print(response)
    return response




app= Flask(__name__)
CORS(app)
@app.route("/")
def display_question():
    response = randomize_question()
    return jsonify(response)

#New display_question function, request id from frontend then calls LLM_topic_decider