import re
c = open("D:/MW/mindflow-map/src/mindflow_map/api/feishu.py", "r", encoding="utf-8").read()

# Remove everything from "from lark_oapi.ws.client" to just before "from mindflow_map.config"
old_start = 'from lark_oapi.ws.client import Client as WSClient\n'
old_end = '\nfrom mindflow_map.config import settings'

c = c[c.index(old_start):]
c = c[c.index(old_end):]

# Find first occurrence of lark imports and replace with just the config import
c = open("D:/MW/mindflow-map/src/mindflow_map/api/feishu.py", "r", encoding="utf-8").read()
lines = c.split("\n")

# Find the line numbers
lark_start = None
config_line = None
for i, line in enumerate(lines):
    if "lark_oapi.ws.client" in line and "import" in line:
        if lark_start is None:
            lark_start = i
    if "from mindflow_map.config import settings" in line:
        config_line = i

if lark_start is not None and config_line is not None:
    # Replace everything from lark_start to config_line (exclusive)
    new_lines = lines[:lark_start] + lines[config_line:]
    open("D:/MW/mindflow-map/src/mindflow_map/api/feishu.py", "w", encoding="utf-8").write("\n".join(new_lines))
    print(f"Removed lines {lark_start} to {config_line-1}")
else:
    print(f"lark_start={lark_start}, config_line={config_line}")
