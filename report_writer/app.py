import streamlit as st
import os
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from tavily import TavilyClient
from typing import TypedDict, List
import prompts
from models import get_models

def main():
    st.title("Report Writing Assistant")
    st.write("Researches a topic and writes a report on it.")

    # API Key Inputs
    st.header("API Credentials")
    openai_api_key = st.text_input(
        "Enter your OpenAI API key:",
        type="password",
        help="Your API key is used to access OpenAI's language models."
    )
    tavily_api_key = st.text_input(
        "Enter your Tavily API key:",
        type="password",
        help="Your API key is used to access Tavily services."
    )

    # Check if both API keys are provided
    if not openai_api_key or not tavily_api_key:
        st.warning("Please enter both your OpenAI and Tavily API keys to proceed.")
        st.stop()  # Prevents the rest of the app from running

    # Initialize the ChatOpenAI model after validating API keys
    model = "ollama"
    llm = get_models(model, openai_api_key)

    # User Inputs for Report Generation
    st.header("Report Details")
    topic = st.text_input("Enter your research topic:")

    # Check if name and topic are provided
    if not topic:
        st.warning("Please enter your research topic.")
        st.stop()

    # Submit Button
    if st.button("Submit"):
        # You can add more logic here to handle the report generation
        st.success(f"Your report on '{topic}' is being generated...")

if __name__ == "__main__":
    main()