#Goal - test communication w/ LLM from python script 
#downloaded Ollama to access llama models.
#ollama pull llama3.1:8b [powershell]
#pip install ollama

from ollama import chat 
from ollama import ChatResponse
import json

stess_levels = {
    "english" : "30.2",
    "spanish" : "25.4",
    "french" : "28.7",
    "math" : "55.6",
    "history" : "40.1"
}

#Generate option might be better than chat for this use case, but I want to test chat first since it is more flexible and can be used for a wider range of interactions.
print("Message one")
response: ChatResponse = chat(model="llama3.1:8b", messages=[
    {"role": "user", 
     "content": "Here are the average stress levels for a student in different subjects: " + str(stess_levels) + 
     ". From the provided data, please select the subject that would be most likely to lower the student's stress. Do not print out the entire list, just the subject name and stress level of your selection."
     }
     ])

print(response['message']['content'])

print("Message two")
with open("backend/data/testquestions.json", 'r') as file:
    questions = json.load(file)

response: ChatResponse = chat(model="llama3.1:8b", messages=[
    {"role": "user", 
     "content": "Here are some questions: " + str(questions) + 
     ". .From the provided list, please select the question that would be most likely to lower the student's stress. Do not print out the entire list, just the question text and id of your selection."
     }
     ])

print(response['message']['content'])


print("Message three")
with open("backend/data/testreponsehistory.json", 'r') as file:
    history = json.load(file)
response: ChatResponse = chat(model="llama3.1:8b", messages=[
    {"role": "user", 
     "content": "Here is a different student's response history: " + str(history) + 
     ". From the provided history, please generate a question that would be most likely to lower the student's stress. The student is between the 6-8th grade range."
     }
     ])

print(response['message']['content'])

print("Message four")
#THIS SHOWS that there is no real "memory" of the previous interactions, so I will need to include the relevant information in each prompt. This is not ideal, but it is a limitation of the current setup. I will need to find a way to store the relevant information and include it in each prompt without overwhelming the model with too much information.
response: ChatResponse = chat(model="llama3.1:8b", messages=[
    {"role": "user", 
     "content": "From the previously provided question list and response history, select a question from the list that will have the highest liklihood for the student to answer correctly. Only provide the question ID and question text."
     }
     ])

print(response['message']['content'])