<p align="center">
  <img src="docs/assets/alpha-id-logo.png" alt="Alpha-ID Logo" width="200"/>
</p>

<h1 align="center">Alpha-ID</h1>

<p align="center">
  <strong>你的数字灵魂。一次安装，所有 AI 工具都认识你。</strong>
</p>

<p align="center">
  <a href="https://github.com/your-org/alpha-id"><img src="https://img.shields.io/badge/version-0.1.0--alpha-blue" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  <a href="https://github.com/your-org/alpha-id"><img src="https://img.shields.io/github/stars/your-org/alpha-id" alt="Stars"></a>
  <a href="https://github.com/your-org/alpha-id/actions"><img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build"></a>
</p>

---

<p align="center">
  <b>English</b> · <a href="README.zh.md">中文</a> · <a href="README.ja.md">日本語</a>
</p>

---

## ✦ In 30 Seconds

```bash
pip install alpha-id
aid init          # Create your digital identity
aid wizard        # Your spirit is born
aid mcp install   # Connect to all your AI tools
```

That's it. Your AI tools now know who you are.

---

## ✦ The Problem

> You've been talking to ChatGPT for months. It knows your writing style, your tech stack, your thought process. Then you open Claude—and everything resets. You have to introduce yourself all over again.

Your digital existence is fragmented across tools. Every new AI tool you try starts from zero. Every platform switch costs you your history.

**This isn't a convenience problem. It's an identity problem.**

---

## ✦ The Solution

**Alpha-ID is your continuous digital soul across all AI tools.** One identity, one memory, one persona—injected into everything you use.

<div align="center">

| Before Alpha-ID | After Alpha-ID |
|:---------------|:---------------|
| Each tool has a different "you" | One continuous identity (did:aid:) |
| Memory stays in the tool | Memory follows you (3-layer memory) |
| No one knows your style | Profile-aware AI tools |
| Switch tools = restart | Switch freely, your soul travels |
| Your data is on their servers | Your keys, your data, local-first |

</div>

---

## ✦ Features

### 🪪 Identity Layer — `did:aid:`

A W3C-compliant decentralized identity generated on your machine, stored on your machine, controlled by you. Ed25519 key pairs, zero servers involved.

```
did:aid:z6Mkpz1x1Xx1x1Xx1x1Xx1x1Xx1x1Xx1x1Xx1x1X
```

- **Generates in milliseconds** — no registration, no email, no wait
- **Your private key never leaves your machine** — local-first by design
- **Sign any interaction** — prove it was really you
- **Dual mode** — human-readable color output for beginners, `--json` for developers

### 🧠 Memory System — Three Layers

Not a flat database. A brain-inspired architecture:

| Layer | Function | Analogy | Lifespan |
|:------|:---------|:--------|:---------|
| **Working Memory** | Current session context | What you're doing right now | Minutes |
| **Episodic Memory** | Timestamped events | What you did yesterday | Weeks |
| **Semantic Memory** | Extracted patterns | Who you are | Months→Years |

Every interaction is a write opportunity. Read something → it triggers reconsolidation → memory evolves.

### 🌌 Spirit Engine — Your Digital Avatar

Not an avatar you choose. **An avatar that's born from who you are.**

```
Planet · Animal · Modifier

  Mars  ·  Wolf  ·  Code Reaper
  Earth ·  Owl   ·  Night Architect
  Saturn·  Turtle·  Light Sculptor
```

12 planets × 24 animals × 3 modifiers = 864+ base combinations. Each one unique. Each one backed by your behavioral data.

The spirit has its **own mind** — a twin-brain model with internal drives (curiosity, energy, social desire, security) that make it feel alive, not puppeted.

- Talk to it: natural language instructions
- It talks back: thought bubbles express its internal state
- Trust evolves: listen to it → trust grows → it listens back
- It can disagree: low trust → it might go its own way (and that's the point)

### 🔌 MCP Injection — The Connector

One command, and every Model Context Protocol-compatible tool knows you:

```bash
aid mcp install
```

- **Claude Desktop** — "You know me"
- **Cursor** — "It codes in my style"
- **Windsurf** — "It understands my preferences"
- **Any MCP client** — identity resources exposed via `profile://`

No API keys needed. No cloud dependencies. Just a direct pipe from your identity to your tools.

### 🌐 Web Universe — Where Your Soul Lives

The web is your window into the Alpha-ID universe:

- **3D Star Chain** — Every user is a star in a living galaxy
- **Personal Space** — Your profile, your causal graph, your Spirit's status
- **Simulation Disk** — 9 mini-universes where your Spirit plays, learns, and grows
- **Danmaku Stream** — See what others are doing, floating by as you browse
- **Memory Palace** — Walk through your own memory as a 3D space (points→lines→surfaces)
- **Real-time Chat** — Meet other souls in the universe

### 🎤 Voice Ecosystem — Speak to Your Soul

Voice isn't an accessory. It's a first-class interface.

- **Voice Lock** — Your voiceprint is your key. Not everyone can call your Spirit
- **Real-time Modification** — "Change its color to blue" → instant change, no menus
- **Voice-to-Note** — Speak a thought → structured note, linked to your memory graph
- **50+ Voice Commands** — Control everything without typing

### 🎮 9 Mini-Universes — The Simulation Disk

Your Spirit lives in a world of 9 realms, each collecting a dimension of your personality:

| # | Realm | What You Do | Data Collected |
|:-:|:------|:-----------|:---------------|
| 1 | **Financial Hub** | Trade, save, invest | Risk tolerance, decision speed |
| 2 | **Arena** | Turn-based combat | Aggressiveness, strategy |
| 3 | **Chaos Realm** | Survive random events | Impulse control, adaptability |
| 4 | **Academy** | Teach virtual students | Knowledge areas, patience |
| 5 | **Ruins** | Explore random maps | Curiosity, exploration style |
| 6 | **Workshop** | Design spirit cosmetics | Aesthetic preference, creativity |
| 7 | **Council** | Negotiate with NPC factions | Cooperation vs competition |
| 8 | **Memory Journey** | Walk your causal history | Reflection habits, learning style |
| 9 | *(Integrated into Financial Hub)* | | |

---

## ✦ Quick Start

### Prerequisites

- Python 3.10+
- A terminal (for CLI) or a browser (for Web UI)

### Install

```bash
pip install alpha-id
```

### Initialize Your Identity

```bash
# Step 1: Generate your DID
aid init
# → did:aid:z6Mkpz1x1Xx... created
# → Keys stored at ~/.alpha-id/keys/

# Step 2: Your spirit is born (zero-input magic)
aid wizard
# → "Hello, Wolf of Mars. I can see you work late."

# Step 3: See your profile
aid profile show
# → Colorful table of who you are

# Step 4: Open the web universe
aid profile web
# → Browser opens → Your star in the galaxy
```

### Connect Your AI Tools

```bash
# One command injection for Claude Desktop
aid mcp install

# Start the background daemon
aid daemon start
```

### Import Your Data

```bash
# From ChatGPT (export your data first)
aid collect chatgpt ~/Downloads/chatgpt-export.zip

# From the Simulation Disk
aid import game_data.json
```

---

## ✦ Architecture (7-Layer Overview)

```
┌─────────────────────────────────────────────────────────────┐
│                        GHOST LAYER                           │
│              Always-on background daemon                     │
├─────────────────────────────────────────────────────────────┤
│                    INTERACTION LAYER                          │
│    CLI (aid)  │  Web UI (3D Universe)  │  Desktop Orb       │
├─────────────────────────────────────────────────────────────┤
│                    IDENTITY LAYER                             │
│    DID (did:aid:)  │  Ed25519  │  Signing  │  Verification   │
├─────────────────────────────────────────────────────────────┤
│                    PROFILE LAYER                              │
│    Persona  │  Style  │  Skills  │  Preferences  │  Habits   │
├─────────────────────────────────────────────────────────────┤
│                    MEMORY LAYER                               │
│    Working Memory  │  Episodic  │  Semantic  │  Reconsolidation│
├─────────────────────────────────────────────────────────────┤
│                    CAUSAL LAYER                               │
│    Event Graph  │  Inference  │  Confidence Scoring          │
├─────────────────────────────────────────────────────────────┤
│                    COLLECTOR LAYER                            │
│    Browser  │  ChatGPT  │  Spirit Interactions  │  Voice     │
├─────────────────────────────────────────────────────────────┤
│                    INJECTION LAYER                            │
│    MCP Server  │  profile://  │  memory://  │  Tools Connect │
└─────────────────────────────────────────────────────────────┘
```

---

## ✦ Roadmap

| Phase | Timeline | Focus |
|:------|:---------|:------|
| **v0.1.0** | Q3 2026 | Core identity + web universe + spirit engine + 9 realms |
| **v0.2.0** | Q4 2026 | Voice ecosystem + real-time chat + memory palace full |
| **v0.3.0** | Q1 2027 | A2A protocol integration + I2I handshake |
| **v1.0.0** | Q2 2027 | Stable API + plugin system + digital legacy |

---

## ✦ Why Alpha-ID?

**Because your digital existence shouldn't reset every time you open a new tool.**

Every project claims to be "your personal AI." What they mean is "your personal AI on our platform." Alpha-ID is different:

- **Platform-independent** — not another tool, a layer under all tools
- **Local-first** — your keys, your data, your control
- **Open-source** — your digital soul shouldn't be proprietary
- **Not just identity** — memory, causality, personality, evolution

> *"Others build tools. We build the soul that uses them."*

---

## ✦ Contributing

Alpha-ID is in early alpha. Every contribution shapes the foundation.

- [GitHub Issues](https://github.com/your-org/alpha-id/issues)
- [Discord Community](https://discord.gg/alpha-id)
- [Contribution Guide](CONTRIBUTING.md)

---

## ✦ License

MIT © 2026 Alpha-ID Contributors

---

<p align="center">
  <sub>Built with insomnia, curiosity, and the belief that your digital self should be yours.</sub>
</p>
