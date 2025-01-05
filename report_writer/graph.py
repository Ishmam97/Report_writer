# graph.py

import logging
from typing import TypedDict, List

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from tavily import TavilyClient

import prompts  # Assuming you have a `prompts.py` with your prompt strings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: List[str]
    revision_number: int
    max_revisions: int

class Queries(BaseModel):
    queries: List[str]



def plan_node(state: AgentState, llm):
    """
    Node function that modifies 'plan' in the state
    """
    try:
        logger.info("Executing plan_node")
        task_content = state["task"]
        if not isinstance(task_content, str):
            raise ValueError(f"Expected task content to be a string, got {type(task_content)}")
        
        messages = [
            SystemMessage(content=prompts.PLAN_PROMPT),
            HumanMessage(content=task_content)
        ]
        response = llm.invoke(messages)
        return {"plan": response.content} 
    except Exception as e:
        logger.error(f"Error in plan_node: {e}")
        raise

    

def researcher_node(state: AgentState, llm, tavily_client: TavilyClient):
    """
    Node function that modifies 'content' by searching on Tavily
    using queries from the LLM.
    """
    try:
        logger.info("Executing research_plan_node")

        # Get queries from LLM
        queries = llm.with_structured_output(Queries).invoke([
            SystemMessage(content=prompts.RESEARCH_PLAN_PROMPT),
            HumanMessage(content=state["task"])
        ])

        logger.debug(f"Research Plan Queries Response: {queries}")

        if (queries is None 
            or not hasattr(queries, "queries") 
            or not isinstance(queries.queries, list)):
            raise ValueError("Model did not return the expected structured output.")

        # Gather existing content
        content = state.get("content", [])

        # Use Tavily to search for each query
        for q in queries.queries:
            resp = tavily_client.search(query=q, max_results=2)
            for r in resp["results"]:
                content.append(r["content"])

        return {"content": content}
    except Exception as e:
        logger.error(f"Error in research_plan_node: {e}")
        raise
    

def generation_node(state: AgentState, llm, tavily_client: TavilyClient):
    """
    Node function that modifies 'draft' by generating text using the LLM.
    """
    try:
        logger.info("Executing generation_node")
        content_str = "\n\n".join(state["content"] or [])
        user_message = HumanMessage(
            content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}"
        )
        messages = [
            SystemMessage(
                content=prompts.WRITER_PROMPT.format(content=content_str)
            ),
            user_message
        ]
        response = llm.invoke(messages)
        return {
            "draft": response.content,
            "revision_number": state.get("revision_number", 1) + 1
        }
    except Exception as e:
        logger.error(f"Error in generation_node: {e}")
        raise

def reflection_node(state: AgentState, llm, tavily_client: TavilyClient ):
    """
    Node function that modifies 'critique' by reflecting on the draft.
    """
    try:
        logger.info("Executing reflection_node")
        messages = [
            SystemMessage(content=prompts.REFLECTION_PROMPT),
            HumanMessage(content=state["draft"])
        ]
        response = llm.invoke(messages)
        return {"critique": response.content}
    except Exception as e:
        logger.error(f"Error in reflection_node: {e}")
        raise

def research_critique_node(state: AgentState, llm, tavily_client: TavilyClient):
    """
    Node function that modifies 'content' again by searching 
    based on the critique.
    """
    try:
        logger.info("Executing research_critique_node")
        queries = llm.with_structured_output(Queries).invoke([
            SystemMessage(content=prompts.RESEARCH_CRITIQUE_PROMPT),
            HumanMessage(content=state["critique"])
        ])

        logger.debug(f"Research Critique Queries Response: {queries}")

        if (queries is None 
            or not hasattr(queries, "queries") 
            or not isinstance(queries.queries, list)):
            raise ValueError("Model did not return the expected structured output.")

        content = state.get("content", [])
        for q in queries.queries:
            resp = tavily_client.search(query=q, max_results=2)
            for r in resp["results"]:
                content.append(r["content"])

        return {"content": content}
    except Exception as e:
        logger.error(f"Error in research_critique_node: {e}")
        raise


# 3) Condition for whether we should keep refining
def should_continue(state: AgentState):
    if state["revision_number"] > state["max_revisions"]:
        return END
    return "reflect"

def build_graph(llm, tavily_api_key: str):
    """
    Build & compile the LangGraph graph, returning it.
    """
    initial_state = AgentState(
        task="",
        plan="",
        draft="",
        critique="",
        content=[],
        revision_number=1,
        max_revisions=2,
    )
    
    tavily_client = TavilyClient(api_key=tavily_api_key)
    memory = MemorySaver()
    builder = StateGraph(AgentState)

    # Using our factory functions:
    builder.add_node("planner", lambda state: plan_node(state=state, llm=llm))
    builder.add_node("researcher", lambda state: researcher_node(state=state, llm=llm, tavily_client=tavily_client))
    builder.add_node("generate", lambda state: generation_node(state=state, llm=llm, tavily_client=tavily_client))
    builder.add_node("reflect", lambda state: reflection_node(state=state, llm=llm, tavily_client=tavily_client))
    builder.add_node("research_critique", lambda state: research_critique_node(state=state, llm=llm, tavily_client=tavily_client))

    # Workflow
    builder.set_entry_point("planner")
    builder.add_conditional_edges(
        "generate",
        should_continue,
        {END: END, "reflect": "reflect"}
    )
    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "generate")
    builder.add_edge("reflect", "research_critique")
    builder.add_edge("research_critique", "generate")

    # Compile the graph with memory-based checkpointing
    graph = builder.compile(checkpointer=memory)
    return graph
