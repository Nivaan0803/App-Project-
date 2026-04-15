import streamlit as st
#
# python.exe -m pip install --upgrade pip
# pip install -r requirements.txt
# streamlit run main.py
#
st.title("Cognitive Support App") # think of a good title
st.header("Daily Check-in")
mood = st.slider("How do you feel today?", 1, 5)



