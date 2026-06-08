import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

def _llm(model, base_url):
    return ChatOllama(model=model, base_url=base_url, temperature=0.0)

def ask(prompt: str, system: str, model: str, base_url: str) -> str:
    chain = ChatPromptTemplate.from_messages([("system", system), ("user", "{p}")]) | _llm(model, base_url)
    return chain.invoke({"p": prompt}).content

def extract_code(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    m = re.search(r"```(?:python|json)?\s*(.*?)(?:```|$)", text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else text.strip()
