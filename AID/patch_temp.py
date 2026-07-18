from pathlib import Path

path = Path("src/entrypoints/aid_mcp_server.py")
text = path.read_text(encoding="utf-8")
old = '''def _has_capability(name: str) -> bool:
    return bool(globals().get(name))
'''
new = '''def _has_capability(name: str) -> bool:
    aid_mcp = sys.modules.get("aid_mcp_server")
    if aid_mcp is not None and hasattr(aid_mcp, name):
        return bool(getattr(aid_mcp, name))
    return bool(globals().get(name))
'''
if old not in text:
    print("NOT FOUND _has_capability")
    raise SystemExit(1)
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("patched", path)
