"""
RAG Agent with LangChain
=========================
Retrieval-Augmented Generation (RAG) implemented as an agent tool.

The agent decides *when* to retrieve documents — it only searches the knowledge
base when the user asks about topics it might not know from training data.

This is more flexible than a plain RAG chain: the agent can combine retrieval
with other tools (e.g., calculations) in a single response.

Run:
    pip install -e ".[langchain]"
    python 01_langchain/04_rag_agent/agent.py
"""

from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

# Replace with your own documents (PDFs, text files, web pages, etc.)
DOCUMENTS = [
    """
    Agent-101 is a tutorial repository for learning about AI agents.
    It covers four frameworks: LangChain, LangGraph, Strands Agents, and Google ADK.
    Each section includes working Python scripts demonstrating key agent patterns.
    """,
    """
    LangGraph is a framework for building stateful, multi-actor LLM applications.
    It uses a directed graph where nodes are Python functions and edges define control flow.
    LangGraph supports cycles, which are essential for agent loops and retries.
    """,
    """
    The ReAct pattern (Reasoning + Acting) was introduced in the paper
    "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022).
    It interleaves reasoning traces with action steps, improving interpretability
    and task performance over chain-of-thought or tool use alone.
    """,
    """
    Strands Agents is an open-source SDK from AWS for building AI agents.
    It uses Amazon Bedrock as the default LLM provider and supports tools
    defined with simple Python decorators. Strands is designed for
    production-grade, scalable agent systems on AWS infrastructure.
    """,
    """
    Google ADK (Agent Development Kit) is Google's open-source Python framework
    for building agents that run on Gemini models. It supports multi-agent
    architectures via AgentTool, where one agent can delegate to another.
    ADK integrates natively with Google Cloud and Vertex AI.
    """,
]


def build_retriever():
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    docs = splitter.create_documents(DOCUMENTS)
    vectorstore = Chroma.from_documents(docs, embedding=OpenAIEmbeddings())
    return vectorstore.as_retriever(search_kwargs={"k": 2})


def main():
    retriever = build_retriever()

    @tool
    def search_knowledge_base(query: str) -> str:
        """Search the Agent-101 knowledge base for information about AI agents,
        frameworks (LangChain, LangGraph, Strands, Google ADK), and concepts.
        Use this when asked about specific topics from the tutorial.
        """
        docs = retriever.invoke(query)
        return "\n\n".join(doc.page_content.strip() for doc in docs)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    tools = [search_knowledge_base]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=3)

    queries = [
        "What paper introduced the ReAct pattern and what does it do?",
        "What is Strands Agents and who made it?",
        "How does LangGraph differ from LangChain?",
    ]

    for query in queries:
        print(f"\n{'='*60}\nQuery: {query}\n{'='*60}")
        result = executor.invoke({"input": query})
        print(f"\nAnswer: {result['output']}")


if __name__ == "__main__":
    main()
