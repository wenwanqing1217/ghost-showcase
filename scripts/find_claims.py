"""Find inflated claims in documentation."""
import os

BASE = "D:\\MW"
KEYWORDS = ["可直接部署", "生产级", "直接运行，无需配置", "无需配置", "生产环境"]

results = []
for doc in ["README.md", "PORTFOLIO.md"]:
    path = os.path.join(BASE, doc)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for kw in KEYWORDS:
        if kw in content:
            idx = content.index(kw)
            context = content[max(0, idx-80):idx+80].replace("\n", " ")
            results.append(f"{doc}: found '{kw}'\n  Context: ...{context}...\n")

with open(os.path.join(BASE, "scripts", "findings.txt"), "w", encoding="utf-8") as out:
    if results:
        out.write("\n".join(results))
    else:
        out.write("NO_INFLATED_CLAIMS_FOUND")
