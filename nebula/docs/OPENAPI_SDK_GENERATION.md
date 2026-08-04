# OpenAPI SDK Generation

从 Nebula OpenAPI 规范生成 SDK。

```bash
openapi-generator-cli generate \
  -i http://localhost:2002/openapi.json \
  -g python \
  -o ./sdk/python
```

支持语言：Python, TypeScript, Go
