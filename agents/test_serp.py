# test_serp.py

import os
from langchain_community.utilities import SerpAPIWrapper
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain import hub

def main():
    # ----------------------------
    # 1. API keys
    # ----------------------------
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not serpapi_key:
        raise ValueError("❌ Missing SERPAPI_API_KEY environment variable")
    if not openai_key:
        raise ValueError("❌ Missing OPENAI_API_KEY environment variable")

    # ----------------------------
    # 2. Define tool (SerpAPI)
    # ----------------------------
    search = SerpAPIWrapper(serpapi_api_key=serpapi_key)
    tools = [
        Tool(
            name="WebSearch",
            func=search.run,
            description="Use this tool to search the web for up-to-date information."
        )
    ]

    # ----------------------------
    # 3. LLM
    # ----------------------------
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # ----------------------------
    # 4. Load the ReAct prompt from LangChain Hub
    # ----------------------------
    prompt = hub.pull("hwchase17/react")  # a general reasoning + tool-use prompt

    # ----------------------------
    # 5. Create and run agent
    # ----------------------------
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # ----------------------------
    # 6. Test queries
    # ----------------------------
    queries = [
        "What is the current population of India?",
        "Who is the CEO of Tesla in 2025?"
    ]

    for q in queries:
        print(f"\n🔍 Query: {q}")
        try:
            answer = agent_executor.invoke({"input": q})
            print("Answer:", answer["output"])
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
