import os, re

class RAG:
    def __init__(self, directory="template"):
        self.docs = []
        if not os.path.exists(directory):
            return
        for f in os.listdir(directory):
            if f.endswith((".py", ".txt", ".md")):
                try:
                    self.docs.append((f, open(os.path.join(directory, f), encoding="utf-8").read()))
                except Exception:
                    pass

    def retrieve(self, query: str, k: int = 2) -> str:
        if not self.docs:
            return ""
        words = set(re.findall(r"\w+", query.lower()))
        ranked = sorted(self.docs, key=lambda d: len(words & set(re.findall(r"\w+", d[1].lower()))), reverse=True)
        return "\n\n".join(f"# Example: {n}\n{c}" for n, c in ranked[:k] if c)
