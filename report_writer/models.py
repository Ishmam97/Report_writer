from langchain_openai import ChatOpenAI

def get_models(model_name, api_key):
    llm = None
    if model_name == "ollama":
            llm = ChatOpenAI(
                model="llama3.1",
                base_url="http://localhost:11434/v1",
                temperature=0.9,
                api_key="na"  # Consider securing this API key
            )
            
    elif model_name == "openai":
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=api_key,
                temperature=0.9
            )
    
    else:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.9
        )
    return llm