import streamlit as st
#
# Upgrade Python packages manager:
# python.exe -m pip install --upgrade pip
#
# Install all the required libraries:
# pip install -r requirements.txt
#
# Run the streamlit program (instead of green triangle print this in the terminal)
# streamlit run main.py
#

""" Draft code"""

st.title("Cognitive Support App") # think of a good title
st.header("Daily Check-in")
mood = st.slider("How do you feel today?", 1, 5)

