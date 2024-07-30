import streamlit as st
import pandas as pd
import numpy as np


def calculate_enneagram(answers):
    # This is a placeholder logic for calculating Enneagram type
    # Replace this with the actual logic based on your questionnaire
    scores = np.random.randint(1, 10, size=9)
    return np.argmax(scores) + 1


# Set the title of the app
st.title("Enneagram Type Assessment")

# Introduction text
st.write("Answer the following questions to find out your Enneagram type:")

# Define the questions
questions = [
    "I strive for perfection.",
    "I work hard to be helpful to others.",
    "It is important to me to be admired by others.",
    "I am always busy and productive.",
    "I am very sensitive and can be easily hurt.",
    "I seek security and safety.",
    "I am always looking for new experiences.",
    "I am a natural leader.",
    "I am easy-going and relaxed."
]

# Collect answers from user
answers = []
for i, question in enumerate(questions):
    answer = st.radio(question, options=[
                      "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"], index=2, key=i)
    answers.append(answer)

# Convert answers to numerical values
answer_mapping = {
    "Strongly Disagree": 1,
    "Disagree": 2,
    "Neutral": 3,
    "Agree": 4,
    "Strongly Agree": 5
}
numerical_answers = [answer_mapping[answer] for answer in answers]

# Button to submit answers
if st.button("Submit"):
    enneagram_type = calculate_enneagram(numerical_answers)
    st.write(f"Your Enneagram type is: {enneagram_type}")
