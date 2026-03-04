"""
Tool Calling with LangChain
============================
Direct tool calling using ChatOpenAI's bind_tools() — no ReAct prompt needed.

Unlike ReAct (which uses text prompting to trigger tools), this uses the LLM's
native function-calling API. More reliable for structured tasks; less interpretable.

The tool loop is manual here so you can see exactly what's happening:
  LLM → tool_calls → run tools → pass results back → LLM → final answer

Run:
    python 01_langchain/02_tool_calling/agent.py
"""

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city. Returns temperature and conditions."""
    weather_data = {
        "new york": "72°F, partly cloudy",
        "london": "58°F, rainy",
        "tokyo": "68°F, sunny",
        "paris": "65°F, overcast",
    }
    return weather_data.get(city.lower(), f"No weather data for {city}")


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between currencies. Supported: USD, EUR, GBP, JPY."""
    rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5}
    if from_currency not in rates or to_currency not in rates:
        return f"Unsupported currency. Supported: {', '.join(rates.keys())}"
    result = amount * (rates[to_currency] / rates[from_currency])
    return f"{amount} {from_currency} = {result:.2f} {to_currency}"


def run_tool_loop(llm_with_tools, tools_by_name: dict, user_message: str) -> str:
    """Run the tool-calling loop until the LLM stops requesting tool calls."""
    messages = [HumanMessage(content=user_message)]

    while True:
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content

        for tool_call in response.tool_calls:
            print(f"  → {tool_call['name']}({tool_call['args']})")
            result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))


def main():
    tools = [get_weather, convert_currency]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}

    queries = [
        "What's the weather like in Tokyo?",
        "Convert 100 USD to EUR and tell me the weather in Paris.",
        "How much is 500 GBP in JPY?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        answer = run_tool_loop(llm_with_tools, tools_by_name, query)
        print(f"Answer: {answer}")


if __name__ == "__main__":
    main()
