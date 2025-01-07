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
    st.subheader("Multi-Agent Researcher Powered by langgraph 🤖")
    col1, col2 = st.columns(2)
    with col1:
        st.write("""
        Built with langgraph and specialized tools, this multi-agent researcher 
        system orchestrates powerful web searching and advanced multi-step 
        planning so you can gather and analyze information with ease. 
        More exciting capabilities are on the horizon, ensuring you stay ahead 
        in your knowledge pursuits!

        **Use local models or cloud-based services** — the choice is yours. 
        Privacy, performance, and flexibility are our top priorities, 
        so you can tailor this application to fit your unique needs. 🔎💡""")
    
    with col2:
        st.image("report_writer/img/agent_architecture.png", caption="Agent Architecture", width=200)

    # Catchy, exciting description
    st.subheader("Why You'll Love This App")
    st.write("""
        Get ready to supercharge your research and report-writing process! 
        This multi-agent system harnesses powerful web searching and 
        advanced multi-step planning, ensuring you have the most relevant 
        information at your fingertips. Whether you’re exploring an academic topic, 
        developing a business proposal, or crafting a technical document, 
        our automated researcher and planner will simplify your workflow from start to finish.
        
        **Use local models or cloud-based services** — the choice is yours. 
        Privacy, performance, and flexibility are our top priorities, 
        so you can tailor this application to fit your unique needs. More to come soon! 🚀📚
    """)

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

    if not openai_api_key or not tavily_api_key:
        st.warning("Please enter both your OpenAI and Tavily API keys to proceed.")
        st.stop()
    
    st.header("Report Details")
    topic = st.text_input("Enter your research topic:")
    
    model = "openai"
    llm = get_models(model, openai_api_key)
    graph = build_graph(llm, tavily_api_key)
    
    if not topic:
        st.warning("Please enter your research topic.")
        st.stop()

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
        
        final_draft = ""

        for state in graph.stream(initial_state, thread):
            key = list(state.keys())[0]
            
            if key == 'planner':
                st.subheader("Planner:")
                st.write(state['planner']['plan'])
            
            elif key == 'researcher':
                with st.expander("Researcher (click to expand)"):
                    for content in state['researcher']['content']:
                        st.write(content)
            
            elif key == 'generate':
                with st.expander("Generate (click to expand)"):
                    st.write(state['generate']['draft'])
                # Update final_draft
                final_draft = state['generate']['draft']
            
            elif key == 'reflect':
                with st.expander("Reflect (click to expand)"):
                    st.write(state['reflect']["critique"])
            
            elif key == 'research_critique':
                with st.expander("Research Critique (click to expand)"):
                    for content in state['research_critique']['content']:
                        st.write(content)

        st.header("Final Draft")
        st.write(final_draft)

       except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True, stack_info=True)
            st.error(f"An error occurred: {e}")
if __name__ == "__main__":
    main()