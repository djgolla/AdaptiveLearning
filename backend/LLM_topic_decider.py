#Ideally - this will be called from LLMTest2 to randomly select a topic. Then can call methods from other files for specific question generation. 
import os
from flask import Flask, jsonify, request
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

    json_response = accuracy_response.data or []

    prompt = f"""
        You are a function that returns ONLY valid JSON.

        DO NOT include explanations, reasoning, code, markdown, symbols, or extra text.

        TASK:
        Select:
        1) A math topic
        2) A difficulty level

        TOPICS:
        geometry, algebra, expressions, ordering, rationals, mean, median, mode, probability, angle_relationships

        INPUT:
        performance = {json_response}
        history = {history}

        RULES (CRITICAL):
        - Use ONLY the provided performance data. NULL attempted_questions values indicate that the topic has not generated yet.
        - Do NOT create, assume, or infer any missing values
        - Do NOT fabricate tables, examples, or additional data
        - Do NOT modify or reinterpret the input data
        - If correct_questions OR attempted_questions is 0 or null → accuracy = 0
        - If data is missing → accuracy = 0
        - Do NOT explain your reasoning
        - Do NOT output calculations
        - Output ONLY JSON

        SELECTION LOGIC:
        - Choose the topic with the LOWEST accuracy
        - You may slightly vary topic choice to avoid repetition using history

        DIFFICULTY RULES:
        - accuracy < 40% → "easy"
        - 40%–70% → "medium"
        - > 70% → "hard"

        OUTPUT FORMAT (STRICT):
        Return ONLY this JSON. No extra text.

        {{
            "topic": "one_of_the_topics",
            "difficulty": "easy_or_medium_or_hard"
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

    # else:
    #     # All retries failed
    #     raise ValueError("(topic selection)Failed to generate valid JSON after retries")
    

    if (topic_data):
        #WILL add check later to default to randomized selection if LLM topic selection fails. 
        topic = topic_data["topic"]
        difficulty = topic_data["difficulty"]
        
    else:
        print("LLM selection generation failed, fallback to randomized selection")
        topic,difficulty = randomize_selection(accuracy_response)
    
   
    question = question_generation(topic, difficulty)
    print(question)
    return question


#Theres probably a cleaner way to do this - have a list of topics and then loop through to find the right one, rather than hardcoding every option. But this works for now.
def question_generation(topic, difficulty):
    print(f"topic: {topic} difficulty: {difficulty}")
    match topic:
        case "ordering":
            response = LLM_ordering_generation.generate_ordering_question(history["global"], history["ordering"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "ordering"})
            history["ordering"].append({
                    "text": response["question_text"],
                    "topic": "ordering"}) 

        case "geometry":
            response = LLM_geometry_generation.generate_geometry_question(history["global"], history["geometry"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "geometry"})
            history["geometry"].append({
                    "text": response["question_text"],
                    "topic": "geometry"})
        case "algebra":
            response = LLM_algebra_generation.generate_algebra_question(history["global"], history["algebra"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "algebra"})
            history["algebra"].append({
                    "text": response["question_text"],
                    "topic": "algebra"})
        case "expressions":
            response = LLM_expressions_generation.generate_expression_question(history["global"], history["expressions"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "expressions"})
            history["expressions"].append({
                    "text": response["question_text"],
                    "topic": "expressions"})
        case "rationals":
            response = LLM_rationals_generation.generate_rational_question(history["global"], history["rationals"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "rationals"})
            history["rationals"].append({
                    "text": response["question_text"],
                    "topic": "rationals"})
        case "mean":
            response = LLM_mean_generation.generate_mean_question(history["global"], history["mean"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "mean"})
            history["mean"].append({
                    "text": response["question_text"],
                    "topic": "mean"})
        case "median":
            response = LLM_median_generation.generate_median_question(history["global"], history["median"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "median"})
            history["median"].append({
                    "text": response["question_text"],
                    "topic": "median"})
        case "mode":
            response = LLM_mode_generation.generate_mode_question(history["global"], history["mode"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "mode"})
            history["mode"].append({
                    "text": response["question_text"],
                    "topic": "mode"})
        case "probability":
            response = LLM_probability_generation.generate_probability_question(history["global"], history["probability"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "probability"})
            history["probability"].append({
                    "text": response["question_text"],
                    "topic": "probability"})
        case "angle_relationships":
            response = LLM_angle_relationship_generation.generate_angle_relationship_question(history["global"], history["angle_relationships"],
                difficulty=difficulty)
            history["global"].append({
                    "text": response["question_text"],
                    "topic": "angle_relationships"})
            history["angle_relationships"].append({
                    "text": response["question_text"],
                    "topic": "angle_relationships"})
    return response

def randomize_selection(accuracy_response):
    num = random.randint(0, 9)
    match num:
        case 0:
            topic = "ordering"
        case 1:
            topic = "rationals"
        case 2:
            topic = "expressions"
        case 3:
            topic = "algebra"
        case 4:
            topic = "geometry"
        case 5:
            topic = "angle_relationships"
        case 6:
            topic = "mean"
        case 7:
            topic = "median"
        case 8: 
            topic = "mode"
        case 9:
            topic = "probability"
        
    #get accuracy from supabase, select difficulty level accordingly 
    for row in accuracy_response.data or []:
        if row.get("math_topics", {}).get("topic_name") == topic:
            correct = row.get("correct_questions") or 0
            attempted = row.get("attempted_questions") or 0
            break 

    if attempted == 0:
        accuracy = 0
    else:
        accuracy = correct / attempted

    if accuracy < 0.4:
        difficulty = "easy"
    elif accuracy < 0.7:
        difficulty = "medium"
    else:
        difficulty = "hard"
    
    return topic, difficulty


#select from 11 math topics
#POSSIBLY can have LLM select topic first given things like stress/accuracy

#TO-DO: Implement LLM-based topic selection, provide (optional) accuracy/stress values from frontend. 
# def randomize_question():
#     num = random.randint(0, 9) #get int from 0-9 inclusive
#     print("num", num)
#     match num:
#         case 0:
#             # Ordering, need to call generate question 
#             response = LLM_ordering_generation.generate_ordering_question(history["global"], history["ordering"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "ordering"})
#             history["ordering"].append({
#                     "text": response["question_text"],
#                     "topic": "ordering"}) 

#         case 1:
#             # Rationals
#             response = LLM_rationals_generation.generate_rational_question(history["global"], history["rationals"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "rationals"})
#             history["rationals"].append({
#                     "text": response["question_text"],
#                     "topic": "rationals"})
#         case 2: 
#             #expressions
#             response = LLM_expressions_generation.generate_expression_question(history["global"], history["expressions"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "expressions"})
#             history["expressions"].append({
#                     "text": response["question_text"],
#                     "topic": "expressions"})
#         case 3: 
#             #algebra
#             response = LLM_algebra_generation.generate_algebra_question(history["global"], history["algebra"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "algebra"})
#             history["algebra"].append({
#                     "text": response["question_text"],
#                     "topic": "algebra"})
#         case 4: 
#             #geometry
#             response = LLM_geometry_generation.generate_geometry_question(history["global"], history["geometry"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "geometry"})
#             history["geometry"].append({
#                     "text": response["question_text"],
#                     "topic": "geometry"})
#         case 5:
#             #angle relationship
#             response = LLM_angle_relationship_generation.generate_angle_relationship_question(history["global"], history["angle_relationships"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "angle_relationships"})
#             history["angle_relationships"].append({
#                     "text": response["question_text"],
#                     "topic": "angle_relationships"})
#         case 6:
#             #mean
#             response = LLM_mean_generation.generate_mean_question(history["global"], history["mean"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "mean"})
#             history["mean"].append({
#                     "text": response["question_text"],
#                     "topic": "mean"})
#         case 7: 
#             #median
#             response = LLM_median_generation.generate_median_question(history["global"], history["median"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "median"})
#             history["median"].append({
#                     "text": response["question_text"],
#                     "topic": "median"})
#         case 8:
#             #mode
#             response = LLM_mode_generation.generate_mode_question(history["global"], history["mode"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "mode"})
#             history["mode"].append({
#                     "text": response["question_text"],
#                     "topic": "mode"})
#         case 9:
#             #probability
#             response = LLM_probability_generation.generate_probability_question(history["global"], history["probability"])
#             history["global"].append({
#                     "text": response["question_text"],
#                     "topic": "probability"})
#             history["probability"].append({
#                     "text": response["question_text"],
#                     "topic": "probability"})

#     print(response)
#     return response




app= Flask(__name__)
CORS(app)
@app.route("/")
def display_question():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    response = LLM_topic_decider(user_id)
    return jsonify(response)

#New display_question function, request id from frontend then calls LLM_topic_decider