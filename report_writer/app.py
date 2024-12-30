import streamlit as st
import os
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
from typing import TypedDict, List

def main():
    st.title("Report Writing Assistant")
    st.write("Researches a topic and writes a report on it.")

    openai_api_key = st.text_input("Enter your openai api key:")
    tavily_api_key = st.text_input("Enter your tavily api key:")

    model = "ollama"
    
    llm =  ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key, temperature=0.9)

    if model == "ollama":
        llm = ChatOpenAI(model="llama3.1", base_url="http://localhost:11434/v1", temperature=0.9, api_key="na")

    

    name = st.text_input("Enter your name:")
    topic = st.text_input("Enter your research topic:")
    if st.button("Submit"):
        st.success(f"Hello, {name}!")

if __name__ == "__main__":
    main()