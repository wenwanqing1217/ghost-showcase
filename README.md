# MindFlow Workspace

Portfolio projects by Boss / ZCode.

## Projects

| Project | Path | Stack | Status |
|---------|------|-------|--------|
| MindFlow | `mindflow/` | Next.js 14, Fastify, TypeScript | build OK, tests OK |
| ai综艺 | `ai综艺/` | React 18, Vite 6, TypeScript, Tailwind, Framer Motion | build OK |
| DS | `DS/` | Next.js 14, Prisma, OpenAI, Shopify API | build OK, tests OK |
| ZCode Brain | `zcode-brain/` | TypeScript dispatcher + safety | tests OK |
| kki | `kki/` | WeChat mini program | README OK |

## Workflow

```
User (CEO)
  -> ZCode (CTO/PM)
    -> Codex (code generation)
```

ZCode Brain dispatches tasks to expert roles and runs safety checks before sending to Codex.

## Deploy

| Project | Platform | Notes |
|---------|----------|-------|
| ai综艺 | Vercel | No env vars needed |
| DS | Vercel | Needs OPENAI_API_KEY, SHOPIFY_SHOP_DOMAIN, SHOPIFY_ACCESS_TOKEN |
| MindFlow web | Vercel | Needs NEXT_PUBLIC_API_URL |
| MindFlow api | Railway | Needs OPENAI_API_KEY |
