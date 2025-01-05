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
from graph import build_graph
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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

    # User Inputs for Report Generation
    st.header("Report Details")
    topic = st.text_input("Enter your research topic:")
    
    # Initialize the ChatOpenAI model after validating API keys
    model = "ollama"
    llm = get_models(model, openai_api_key)
    graph = build_graph(llm, tavily_api_key)
    

    # Check if name and topic are provided
    if not topic:
        st.warning("Please enter your research topic.")
        st.stop()

    # Submit Button
    if st.button("Submit"):
       try:
        initial_state = {
            "task": f"Write a report about {topic}",
            "max_revisions": 2,
            "revision_number": 1,
            "plan": "",
            "draft": "",
            "critique": "",
            "content": [],
        }
        thread = {"configurable":{"thread_id": "1"}}
        for state in graph.stream(initial_state, thread):
            key = list(state.keys())[0]
            if key == 'planner':
                st.header('planner:')
                st.write(state['planner']['plan'])
            elif key == 'researcher':
                st.header('researcher:')
                for content in state['researcher']['content']:
                    st.write(content)
            elif key == 'generate':
                st.header('generate:')
                st.write(state['generate']['draft'])
            elif key == 'reflect':
                st.header('reflect:')
                st.write(state['reflect']["critique"])
            elif key == 'research_critique':
                st.header('research_critique:')
                for content in state['research_critique']['content']:
                    st.write(content)

       except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True, stack_info=True)
            st.error(f"An error occurred: {e}")
if __name__ == "__main__":
    main()