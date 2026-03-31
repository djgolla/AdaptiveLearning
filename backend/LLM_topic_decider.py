#Ideally - this will be called from LLMTest2 to randomly select a topic. Then can call methods from other files for specific question generation. 
from flask import Flask, jsonify
from flask_cors import CORS #pip install flask-cors
import random
import LLM_algebra_generation, LLM_ordering_generation, LLM_rationals_generation, LLM_mean_generation, LLM_median_generation
import LLM_mode_generation, LLM_probability_generation, LLM_geometry_generation, LLM_angle_relationship_generation, LLM_expressions_generation
#python -m flask --app LLM_topic_decider run

#select from 11 math topics
#POSSIBLY can have LLM select topic first given things like stress/accuracy
def randomize_question():
    num = random.randint(0, 9) #get int from 0-9 inclusive
    print("num", num)
    match num:
        case 0:
            # Ordering, need to call generate question 
            response = LLM_ordering_generation.generate_ordering_question()
        case 1:
            # Rationals
            response = LLM_rationals_generation.generate_rational_question()
        case 2: 
            #expressions
            response = LLM_expressions_generation.generate_expression_question()
        case 3: 
            #algebra
            response = LLM_algebra_generation.generate_algebra_question()
        case 4: 
            #geometry
            response = LLM_geometry_generation.generate_geometry_question()
        case 5:
            #angle relationship
            response = LLM_angle_relationship_generation.generate_angle_relationship_question()
        case 6:
            #mean
            response = LLM_mean_generation.generate_mean_question()
        case 7: 
            #median
            response = LLM_median_generation.generate_median_question()
        case 8:
            #mode
            response = LLM_mode_generation.generate_mode_question()
        case 9:
            #probability
            response = LLM_probability_generation.generate_probability_question()

    print(response)
    return response




app= Flask(__name__)
CORS(app)
@app.route("/")
def display_question():
    response = randomize_question()
    return jsonify(response)