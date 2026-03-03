"""
Agent Memory with LangChain
============================
Two memory strategies for maintaining context across conversation turns:

1. ConversationBufferMemory — keeps the full conversation history in context.
   Simple but grows unbounded; can exceed the context window on long chats.

2. ConversationSummaryMemory — compresses old messages into a running summary.
   Scales better; loses some detail in exchange for compactness.

Run:
    python 01_langchain/03_memory/agent.py
"""

from dotenv import load_dotenv
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain_openai import ChatOpenAI

load_dotenv()


def demo_buffer_memory():
    """Full conversation history kept in context."""
    print("\n--- ConversationBufferMemory ---")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    memory = ConversationBufferMemory()
    chain = ConversationChain(llm=llm, memory=memory, verbose=False)

    turns = [
        "My name is Alice and I'm learning about AI agents.",
        "What are the key concepts I should focus on first?",
        "Can you remind me what I said my name was?",  # Tests if memory works
    ]

    for turn in turns:
        print(f"\nUser:  {turn}")
        response = chain.predict(input=turn)
        print(f"Agent: {response}")

    print(f"\n[Buffer has {len(memory.chat_memory.messages)} messages in context]")


def demo_summary_memory():
    """Older messages compressed into a running summary."""
    print("\n--- ConversationSummaryMemory ---")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    memory = ConversationSummaryMemory(llm=llm)
    chain = ConversationChain(llm=llm, memory=memory, verbose=False)

    turns = [
        "I'm building a customer service chatbot for an e-commerce site.",
        "It needs to handle order tracking, returns, and product questions.",
        "We have about 10,000 products and 500 orders per day.",
        "What database would you recommend for storing conversation history?",
        "Can you summarize what my project is about?",  # Tests if summary works
    ]

    for turn in turns:
        print(f"\nUser:  {turn}")
        response = chain.predict(input=turn)
        print(f"Agent: {response}")

    print(f"\n[Running summary: {memory.buffer}]")


if __name__ == "__main__":
    demo_buffer_memory()
    demo_summary_memory()
