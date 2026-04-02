#Ideally - this will be called from LLMTest2 to randomly select a topic. Then can call methods from other files for specific question generation. 
from flask import Flask, jsonify
from flask_cors import CORS #pip install flask-cors
import random
from collections import deque
import LLM_algebra_generation, LLM_ordering_generation, LLM_rationals_generation, LLM_mean_generation, LLM_median_generation
import LLM_mode_generation, LLM_probability_generation, LLM_geometry_generation, LLM_angle_relationship_generation, LLM_expressions_generation
#python -m flask --app LLM_topic_decider run


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