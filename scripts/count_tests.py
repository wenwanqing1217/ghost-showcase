import os, re

test_dir = r"D:\MW\alphaid\projects\tests"
results = []
total = 0
for f in sorted(os.listdir(test_dir)):
    if f.startswith("test_") and f.endswith(".py"):
        path = os.path.join(test_dir, f)
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        tests = re.findall(r"def test_", content)
        count = len(tests)
        total += count
        results.append((f, count, len(content.splitlines())))

for f, count, lines in sorted(results, key=lambda x: -x[1]):
    print(f"{count:4d} tests | {lines:5d} lines | {f}")

print(f"\nTotal: {total} tests, {len(results)} files")
