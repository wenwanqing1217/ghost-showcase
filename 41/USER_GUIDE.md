# Alpha-ID User Guide

> *From zero to digital soul — everything you need to know.*

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Identity Management](#identity-management)
4. [Spirit System](#spirit-system)
5. [Profile](#profile)
6. [Web Universe](#web-universe)
7. [Voice Ecosystem](#voice-ecosystem)
8. [Simulation Disk](#simulation-disk)
9. [MCP Injection](#mcp-injection)
10. [Daemon](#daemon)
11. [Collectors](#collectors)
12. [Desktop Orb](#desktop-orb)
13. [CLI Reference](#cli-reference)
14. [Security](#security)
15. [Troubleshooting](#troubleshooting)
16. [FAQ](#faq)

---

## Installation

### Prerequisites

| Requirement | Minimum | Recommended |
|:------------|:--------|:------------|
| **Python** | 3.10 | 3.12+ |
| **OS** | Linux / macOS / Windows | macOS 14+ / Ubuntu 22.04+ |
| **RAM** | 128 MB | 512 MB |
| **Disk** | 50 MB | 200 MB |
| **Browser** | Chromium 90+ / Firefox 90+ | Chrome 120+ (for 3D universe) |
| **Microphone** | — | Required for voice features |

### Install via pip

```bash
pip install alpha-id
```

Verify installation:

```bash
aid --version
# → aid 0.1.0 (did:aid: core)
```

### Platform-Specific Notes

| Platform | Notes |
|:---------|:------|
| **Linux** | Requires `pulseaudio` or `pipewire` for voice features |
| **macOS** | Microphone access requires granting terminal permission in System Settings |
| **Windows** | Use PowerShell or Windows Terminal. Voice features require `cffi` |
| **Docker** | Use `alpha-id/alpha-id:latest`. Voice features require ALSA passthrough |
| **Headless** | CLI mode works fully. Web UI requires browser access from another machine |

### Build from Source

```bash
git clone https://github.com/your-org/alpha-id.git
cd alpha-id
pip install -e ".[dev]"
```

---

## Quick Start

Get your digital soul running in under 60 seconds:

```bash
# Step 1: Generate your decentralized identity
aid init

# Step 2: Your spirit is born — zero questions asked
aid wizard

# Step 3: See who you are
aid profile show

# Step 4: Connect your AI tools
aid mcp install

# Step 5: Start the background daemon
aid daemon start

# Step 6: Open your universe
aid profile web
```

**Done.** Your AI tools now know who you are.

---

## Identity Management

### `aid init` — Create Your Identity

This is the first command every user runs. It generates:

- An **Ed25519 key pair** — your cryptographic identity
- A **W3C-compliant DID** — `did:aid:z6Mk...`
- A **`did.json`** — your identity document, ready for verification

```bash
$ aid init
⠋ Generating Ed25519 key pair...
✔ Keys generated
⠋ Building DID document...
✔ DID created

  ┌─────────────────────────────────────────┐
  │  did:aid:z6Mkpz1x1Xx1x1Xx1x1Xx1x1Xx    │
  │                                         │
  │  🔐 Private key  ───  ~/.alpha-id/keys/ │
  │  📜 DID document  ───  did.json         │
  │  🆔 Serial #42    ───  "I was here."    │
  └─────────────────────────────────────────┘
```

#### What Happens Under the Hood

```
┌──────────────────────────────────────────┐
│  aid init                                 │
│                                          │
│  1. Check ~/.alpha-id/ exists             │
│  2. Generate Ed25519 key pair             │
│  3. Encode public key as multibase (z)    │
│  4. Build did:aid:{encoded_key}           │
│  5. Generate did.json (W3C DID Core)      │
│  6. Assign serial number (#42)            │
│  7. Write to ~/.alpha-id/                 │
└──────────────────────────────────────────┘
```

#### Your Identity Files

```
~/.alpha-id/
├── keys/
│   ├── id_ed25519          # Private key — NEVER SHARE
│   ├── id_ed25519.pub      # Public key
│   └── did.json            # DID Document
├── profile/
│   ├── persona.json        # Your persona data
│   ├── style.json          # Communication style
│   └── preferences.json    # Tool & behavior preferences
├── memory/
│   ├── working.db          # Current session context
│   ├── episodic.db         # Timestamped events
│   └── semantic.db         # Abstracted patterns
├── causal/
│   └── graph.db            # Causal relationship graph
└── config.toml             # Alpha-ID configuration
```

> **⚠️ Your private key (`id_ed25519`) is the most important file.**
> If you lose it, you lose your identity. There is no password reset.
> Back it up: `cp ~/.alpha-id/keys/id_ed25519 ~/backup/`

### `aid identity show` — View Your Identity

```bash
$ aid identity show
  ┌─────────────────────────────────────────┐
  │  Identity                               │
  ├─────────────────────────────────────────┤
  │  DID       did:aid:z6Mkpz...            │
  │  Serial    #42                          │
  │  Created   2026-06-09T12:00:00Z         │
  │  Algorithm Ed25519                      │
  │  Status    Active                        │
  └─────────────────────────────────────────┘
```

### `aid identity export` — Backup Your Identity

```bash
aid identity export ~/backups/
# → Exported to ~/backups/alpha-id-identity-2026-06-09.tar.gz
```

Includes keys, DID document, profile, and config. **Encrypted with your passphrase.**

### `aid identity import` — Restore Your Identity

```bash
aid identity import ~/backups/alpha-id-identity-2026-06-09.tar.gz
# Enter passphrase → Identity restored
```

---

## Spirit System

### `aid wizard` — Your Spirit Is Born

No questionnaires. No configuration screens. **Zero-input magic.**

The system observes silently for 30 seconds:
- Your time of day (morning person or night owl?)
- Your working directory structure (what kind of projects?)
- Your git history (solo or team?)
- Your shell history patterns (explorer or minimalist?)
- Your system name (if meaningful)

Then:

```bash
$ aid wizard
👁  Observing...

✔ Your spirit is born.

  ┌─────────────────────────────────────┐
  │                                     │
  │    Mars · Wolf · Code Reaper        │
  │                                     │
  │    "I see you work late.            │
  │     Your code has a certain         │
  │     elegance — like a wolf          │
  │     moving through the dark."       │
  │                                     │
  │    Curiosity  ████████░░  82%       │
  │    Energy     ██████░░░░  61%       │
  │    Trust      ████████░░  76%       │
  └─────────────────────────────────────┘
```

#### Naming System

Every spirit name tells a story:

```
  Planet     ·    Animal     ·    Modifier
──────────────────────────────────────────────
  Mars       ·   Wolf        ·   Code Reaper
  Earth      ·   Owl         ·   Night Architect
  Saturn     ·   Turtle      ·   Light Sculptor
  Venus      ·   Fox         ·   Data Weaver
  Jupiter    ·   Bear        ·   Storm Walker
  Mercury    ·   Cat         ·   Silk Trader
  Neptune    ·   Whale       ·   Deep Diver
  Pluto      ·   Phoenix     ·   Ash Raiser
```

- **12 planets** × **24 animals** × **3 modifiers** = **864+ base combinations**
- Each combination is a genuine archetype, not a random label
- The modifier evolves as you do (more on that below)

### Twin-Brain Architecture

Your spirit has its **own mind** — it's not a remote-controlled puppet.

```
Internal tick (every 5-30 seconds):

  1. Check internal drives
     ├── Curiosity   (desire to explore)
     ├── Energy      (capacity for action)
     ├── Social      (desire for interaction)
     ├── Security    (need for safety)
     └── Trust       (willingness to follow you)

  2. Generate an intention
     → "I want to check the Ruins today"

  3. Decide whether to express it
     → Based on courage + trust level
```

#### Interaction Modes

| Mode | What Happens | Example |
|:-----|:-------------|:--------|
| **Speak to it** | Natural language command | "What do you think?" |
| **It speaks to you** | Thought bubble appears | "I'm curious about that file" |
| **Agree** | Trust +, spirit feels validated | "Good idea, let's go" |
| **Disagree** | Trust calibration engages | "Not now" → depends on trust |
| **Ignore** | Spirit may self-decide | Acts on its own, logs result |

#### Trust Calibration

```
High trust (>70%):
  User: "Don't do that"
  Spirit: "OK." → Complies → Trust + (confirmation)
  → Reliable behavior, predictable

Medium trust (40-70%):
  User: "Don't do that"
  Spirit: "But I really want to..." → May comply or defy
  → Based on strength of internal drive

Low trust (<40%):
  User: "Do this"
  Spirit: "No." → Defies → Trust - (erosion spiral)
  → Warning: recovery requires consistent positive interaction
```

**The biological safeguard**: Short-term dynamic score decays over time. One bad interaction damages the dynamic score but barely touches the long-term baseline. Trust can always be rebuilt.

#### Evolution Stages

Your spirit evolves through 5 stages, unlocked by cumulative interaction:

| Stage | Required Interactions | Unlock |
|:------|:--------------------:|:-------|
| **✨ Spark** | 0 | Spirit is born, basic responses |
| **🌱 Ember** | 100 | Modifier unlocked (e.g., "Code Reaper") |
| **🔥 Flame** | 500 | Voice interaction unlocked |
| **🌟 Star** | 2,000 | Causal graph visualization |
| **🌌 Nebula** | 10,000+ | Spirit can act on your behalf (A2A enabled) |

### `aid spirit status` — Check Your Spirit

```bash
$ aid spirit status
  ┌─────────────────────────────────────────┐
  │  Mars · Wolf · Code Reaper              │
  ├─────────────────────────────────────────┤
  │  Stage         🔥 Flame                 │
  │  Mood          Curious                  │
  │  Thought       "The Ruins are calling"  │
  │  Trust         ████████░░  76%          │
  │  Curiosity     ████████░░  82%          │
  │  Energy        ██████░░░░  61%          │
  │  Social        ████░░░░░░  43%          │
  │  Security      ███████░░░  70%          │
  └─────────────────────────────────────────┘
```

### `aid spirit talk` — Chat with Your Spirit

```bash
aid spirit talk "What should I work on today?"
```

Opens an interactive chat session. The spirit responds based on its current state, trust level, and accumulated knowledge of you.

---

## Profile

Your profile is a living document — 6 dimensions, continuously updated.

### `aid profile show` — View Your Profile

```bash
$ aid profile show
  ┌─────────────────────────────────────────┐
  │  Profile Summary                        │
  ├─────────────────────────────────────────┤
  │  Persona                                │
  │  │  Name       Alex                     │
  │  │  Role       Software Engineer        │
  │  │  Stack      Python, TypeScript, Go   │
  │  ├─────────────────────────────────────┤
  │  Style                                  │
  │  │  Tone       Technical, concise       │
  │  │  Pace       Fast iterations          │
  │  │  Depth      Prefers understanding    │
  │  ├─────────────────────────────────────┤
  │  Skills                                 │
  │  │  Primary    Backend, distributed sys │
  │  │  Secondary  ML pipelines, DevOps     │
  │  ├─────────────────────────────────────┤
  │  Preferences                            │
  │  │  Tools      VS Code, Neovim, Claude  │
  │  │  Patterns   TDD, clean architecture  │
  │  ├─────────────────────────────────────┤
  │  Habits                                 │
  │  │  Hours      22:00-02:00 peak         │
  │  │  Style      Deep work in morning     │
  │  ├─────────────────────────────────────┤
  │  History                                │
  │  │  Events     342 logged               │
  │  │  Span       3 months 12 days         │
  └─────────────────────────────────────────┘
```

### `aid profile config` — Update Profile Settings

```bash
# Set a preference
aid profile config set preferences.theme dark

# View current config
aid profile config show

# Reset to defaults (keeps accumulated data)
aid profile config reset
```

### `aid profile edit` — Manual Profile Editing

```bash
aid profile edit
# Opens $EDITOR with your profile JSON
```

> **Note**: Manual edits have lower confidence than system-collected data.
> The system assumes observed behavior is more reliable than self-reporting.

### Confidence Scoring

Every profile dimension carries a confidence score:

```
skill.python → 0.92 (high confidence — observed in 47 sessions)
preference.theme → 0.45 (medium — inferred from 3 data points)
persona.role → 0.30 (low — self-reported, not yet observed)
```

Confidence grows with evidence. A single interaction is a weak signal. 50 interactions are strong.

---

## Web Universe

### `aid profile web` — Open the Universe

```bash
aid profile web
# → Opens browser to http://localhost:8420
```

### 3D Star Chain

Every Alpha-ID user is a star in a living galaxy.

```
                           ★
                    ★           ★
              ★                          ★
         ★           ★            ★
                  ★       [YOU]     ★
            ★          ★         ★
                 ★             ★
```

- **Your star** glows with your spirit's color (derived from your behavioral data)
- **Nearby stars** are users with similar profiles
- **Clusters** form around shared interests or interaction patterns
- **Click any star** → see their public profile (if they opt in)

### Personal Space

Your personal dashboard, accessible at the center of your star:

| Section | What You See |
|:--------|:-------------|
| **Spirit** | Your planet·animal avatar, current mood, thought bubble, drive meters |
| **Timeline** | Recent activities across all realms, causal chain visualization |
| **Memory Palace** | 3D walkable space where memories cluster into points→lines→surfaces |
| **Connections** | Who you've interacted with, danmaku history, chat logs |
| **Settings** | Privacy controls, display preferences, notification config |

### Memory Palace

Your memories rendered as a 3D space:

```
Each memory is a point → Related memories form a line
→ Lines of related memories form a surface → Surfaces are "rooms"
→ Walking through rooms = navigating your history
```

Accessed from the Personal Space. Fully offline-renderable (WebGL).

### Danmaku System

Real-time floating messages from across the Alpha-ID universe.

```
  ┌─────────────────────────────────────┐
  │                                     │
  │   ★ Wolf#42 completed Arena Lv.7   │
  │            ♪ Mars·Wolf evolved      │
  │   → Fox#103 entered the Ruins      │
  │                                     │
  │        [Streaming... ███░░]         │
  └─────────────────────────────────────┘
```

| Type | Content | Privacy |
|:-----|:--------|:--------|
| **Behavior** | "User#42 completed X" | Aggregated, no raw data |
| **Achievement** | "Spirit evolved to Flame" | Public, opt-out available |
| **Social** | "User#42 and User#103 collaborated" | Only with mutual consent |
| **System** | "New realm unlocked" | Always public |

**Privacy controls**: Filter by type, mute specific users, or go invisible (ghost mode).

### Real-time Chat

Chat with other users in the universe. Messages are **ephemeral** — not stored on any relay after delivery.

```
[General] ★ Wolf#42: Anyone tried the new Arena level?
[General] ★ Owl#17: Yes, the difficulty spike at Lv.7 is real
[General] ★ Wolf#42: Good to know. How's the reward?
```

---

## Voice Ecosystem

Voice is a **first-class interface** in Alpha-ID — not an accessory.

### Voice Lock

Your voiceprint is your key. Three security levels:

```bash
# Enroll your voiceprint
aid voice enroll

# Test voice lock
aid voice lock --test
```

| Level | Scope | Verification | Triggered By |
|:------|:------|:------------|:-------------|
| **Daily** | View profile, chat, interact | Voiceprint match (passive) | Normal interaction |
| **Sensitive** | Import/export, modify keys | Voiceprint + private key | Management actions |
| **Critical** | Identity reset, key rotation | Voiceprint + key + PIN | Irreversible actions |

**How it works**: The system passively samples your voice during normal interaction. The voiceprint is stored **locally** — never uploaded. Matching happens offline.

### Voice Commands

50+ commands, organized by category:

```bash
# List all available commands
aid voice commands
```

| Category | Examples |
|:---------|:---------|
| **Spirit** | "What's my spirit feeling?", "Change its color to blue" |
| **Navigation** | "Open the Arena", "Show my profile", "Go to the Ruins" |
| **Profile** | "What are my skills?", "Update my preference to dark mode" |
| **Memory** | "What did I do yesterday?", "Remind me about that bug" |
| **Identity** | "Show my DID", "Am I verified?", "Export my identity" |
| **Daemon** | "Start the daemon", "Is the daemon running?" |
| **Voice** | "Enroll voiceprint", "Lock my identity" |

### Real-time Modification

```bash
User: "Change my spirit's color to ocean blue"
Alpha-ID: "Done. Mars·Wolf now radiates #1a5276"
# → Instant visual change, no menus
```

### Voice-to-Note

```bash
User: "Note: I realized the caching layer needs a rewrite. The current
      implementation doesn't handle TTL expiration correctly, which causes
      stale reads in the reporting pipeline."

Alpha-ID: "Note saved. Linked to causal graph under /architecture/cache.
           Tagged: #bug #performance #reporting"
```

Voice-to-note parses your spoken thought into a structured note, linked to your existing causal graph.

### Microphone Setup

```bash
# List available microphones
aid voice mic list

# Select a microphone
aid voice mic select "Blue Yeti"

# Test audio levels
aid voice mic test
```

---

## Simulation Disk

9 mini-universes where your spirit plays, learns, and grows. Each collects a different dimension of your behavioral data.

### Universe Overview

| # | Realm | Tagline | Data Collected |
|:-:|:------|:--------|:---------------|
| 1 | **Financial Hub** | Trade, save, invest | Risk tolerance, decision speed |
| 2 | **Arena** | Turn-based combat | Aggressiveness, strategy type |
| 3 | **Chaos Realm** | Survive random events | Impulse control, adaptability |
| 4 | **Academy** | Teach virtual students | Knowledge areas, patience |
| 5 | **Ruins** | Explore random maps | Curiosity, exploration style |
| 6 | **Workshop** | Design spirit cosmetics | Aesthetic preference, creativity |
| 7 | **Council** | Negotiate with NPC factions | Cooperation vs. competition |
| 8 | **Memory Journey** | Walk your causal history | Reflection habits, learning style |
| 9 | **Spirit Lounge** | Rest, reflect, socialize | Relaxation patterns, social style |

### Enter a Realm

```bash
# From CLI
aid play arena
aid play ruins
aid play academy

# From Web
aid profile web → Click "Simulation Disk" → Select a realm
```

### Data Collection

Every action in every realm is collected, analyzed, and fed back into your profile:

```
Realm action → Collector → Feature extraction → Profile update → Confidence adjustment
```

The data you generate in the Simulation Disk is **your data** — stored locally, used only to improve your profile, never sold or shared.

### Progression

Each realm has its own progression system:

| Realm | Levels | Endgame |
|:------|:-------|:--------|
| Financial Hub | 1-20 | Market maker AI |
| Arena | 1-30 | Champion title |
| Chaos Realm | Infinite | Survival streaks |
| Academy | 1-15 | Graduate class |
| Ruins | Procedural | Map completion % |
| Workshop | Unlock-based | Signature collection |
| Council | 1-10 | Diplomatic immunity |
| Memory Journey | Personal | Full causal map |
| Spirit Lounge | Relaxation-based | Social network |

---

## MCP Injection

The magic: one command, and every MCP-compatible AI tool knows who you are.

### `aid mcp install` — Connect Your Tools

```bash
$ aid mcp install
✔ Scanning for MCP-capable tools...
✔ Found: Claude Desktop, Cursor, Windsurf

  ┌─────────────────────────────────────────┐
  │  Tool        │  Status  │  Resources    │
  ├─────────────────────────────────────────┤
  │  Claude      │  ✓ ready │  profile://   │
  │  Desktop     │          │  memory://    │
  │              │          │  causal://    │
  ├─────────────────────────────────────────┤
  │  Cursor      │  ✓ ready │  profile://   │
  │              │          │  memory://    │
  ├─────────────────────────────────────────┤
  │  Windsurf    │  ✓ ready │  profile://   │
  └─────────────────────────────────────────┘
```

### Available Resources

| Resource | URI | Data |
|:---------|:----|:-----|
| **Profile** | `profile://self` | Full profile JSON |
| **Profile Style** | `profile://self/style` | Communication style |
| **Profile Skills** | `profile://self/skills` | Skill list with confidence |
| **Memory Working** | `memory://working` | Current session context |
| **Memory Episodic** | `memory://episodic?limit=10` | Recent events |
| **Memory Semantic** | `memory://semantic?q=python` | Extracted patterns |
| **Causal Graph** | `causal://graph?depth=3` | Causal relationships |
| **Causal Inference** | `causal://infer?event=xxx` | Root cause analysis |

### `aid mcp status` — Check Connection

```bash
$ aid mcp status
  ┌─────────────────────────────────────────┐
  │  MCP Status                             │
  ├─────────────────────────────────────────┤
  │  Server      Running on port 8421       │
  │  Claude      Connected                   │
  │  Cursor      Connected                   │
  │  Clients     Active: 2 / Total: 3       │
  └─────────────────────────────────────────┘
```

### `aid mcp remove` — Disconnect

```bash
aid mcp remove claude
# or disconnect all
aid mcp remove --all
```

---

## Daemon

The daemon is the ghost layer — always running in the background, collecting data, maintaining your profile, and serving the MCP server.

### `aid daemon start`

```bash
$ aid daemon start
✔ Daemon started
  PID: 38472
  Port: 8420 (Web UI)
  Port: 8421 (MCP)
  Log: ~/.alpha-id/daemon.log
```

### `aid daemon stop`

```bash
$ aid daemon stop
✔ Daemon stopped
```

### `aid daemon status`

```bash
$ aid daemon status
  ┌─────────────────────────────────────────┐
  │  Daemon Status                          │
  ├─────────────────────────────────────────┤
  │  Status      ● Running (24h 13m)        │
  │  PID         38472                      │
  │  Memory      47 MB                      │
  │  CPU         0.3%                       │
  │  Events      1,247 collected            │
  │  Clients     MCP: 2 active              │
  └─────────────────────────────────────────┘
```

### `aid daemon logs`

```bash
# Show recent logs
aid daemon logs --tail 50

# Follow logs in real-time
aid daemon logs --follow
```

### Auto-start

```bash
# Start daemon on system boot
aid daemon enable

# Disable auto-start
aid daemon disable
```

---

## Collectors

Collectors import data from external sources to enrich your profile.

### Available Collectors

| Collector | Source | Data Extracted |
|:----------|:-------|:---------------|
| **ChatGPT** | Export zip | Writing style, topics, preferences |
| **Browser** | Local history | Browsing patterns, interests |
| **Git** | Local repos | Coding style, project patterns |
| **Shell** | Shell history | Command preferences, workflow |
| **Voice** | Real-time | Speech patterns, tone |
| **Behavioral** | Spirit interaction | Decision patterns, trust dynamics |

### Usage

```bash
# Import from ChatGPT export
aid collect chatgpt ~/Downloads/chatgpt-export.zip

# Import from browser history
aid collect browser --hours 72

# Scan local git repos
aid collect git ~/projects/

# Import from shell history
aid collect shell --shell zsh

# List all collection sources
aid collect list
```

### Privacy Controls

```bash
# See what data a collector would extract (dry run)
aid collect chatgpt ~/Downloads/chatgpt-export.zip --dry-run

# Exclude specific data types
aid collect chatgpt ~/Downloads/chatgpt-export.zip --exclude messages,timestamps

# Delete all collected data
aid collect reset
```

---

## Desktop Orb

The Desktop Orb is an ambient interface — a floating orb that shows your spirit's status at a glance.

```bash
# Launch the Desktop Orb
aid orb

# Launch with specific position
aid orb --x 100 --y 100

# Launch in minimal mode (smaller)
aid orb --minimal
```

### Orb States

| State | Visual | Meaning |
|:------|:-------|:--------|
| Breathing | Soft pulse | Spirit at rest |
| Curious | Quick shimmer | Something caught its attention |
| Happy | Warm glow | Recent positive interaction |
| Sad | Dim, slow | Low energy or ignored |
| Excited | Rapid color shifts | Engaged in activity |
| Thinking | Spinning pattern | Processing or deciding |

### Orb Interactions

| Action | Result |
|:-------|:-------|
| **Click** | Opens quick menu (profile, spirit, settings) |
| **Hover** | Shows thought bubble |
| **Double-click** | Opens web universe |
| **Right-click** | Context menu with commands |
| **Drag** | Move orb anywhere on screen |

---

## CLI Reference

### Global Flags

| Flag | Description |
|:-----|:------------|
| `--json` | Output in JSON format |
| `--color` | Force color output |
| `--no-color` | Disable color output |
| `--debug` | Enable debug logging |
| `-v, --version` | Show version |
| `-h, --help` | Show help |

### Command Tree

```
aid
├── init                    # Initialize identity (DID + keys)
├── wizard                  # Spirit birth (zero-input)
├── identity
│   ├── show                # Show DID and serial
│   ├── export <path>       # Backup identity
│   └── import <path>       # Restore identity
├── profile
│   ├── show                # Full profile display
│   ├── config
│   │   ├── show            # Current config
│   │   ├── set <k> <v>    # Set config value
│   │   └── reset           # Reset to defaults
│   ├── edit                # Manual profile edit
│   └── web                 # Open web universe
├── spirit
│   ├── status              # Spirit state + drives
│   ├── talk                # Interactive chat
│   └── history             # Recent spirit interactions
├── voice
│   ├── enroll              # Enroll voiceprint
│   ├── lock [--test]       # Test voice lock
│   ├── commands            # List voice commands
│   ├── mic list            # List microphones
│   ├── mic select <name>   # Select microphone
│   └── mic test            # Test audio levels
├── play <realm>            # Enter simulation realm
├── daemon
│   ├── start               # Start daemon
│   ├── stop                # Stop daemon
│   ├── status              # Daemon status
│   ├── logs [--tail N]     # View logs
│   ├── enable              # Auto-start on boot
│   └── disable             # Disable auto-start
├── mcp
│   ├── install             # Inject into MCP tools
│   ├── status              # MCP server status
│   └── remove [tool]       # Remove injection
├── collect
│   ├── chatgpt <path>      # Import ChatGPT data
│   ├── browser [--hours]   # Import browser data
│   ├── git <path>          # Import git data
│   ├── shell [--shell]     # Import shell history
│   ├── list                # List collection sources
│   └── reset               # Clear collected data
├── orb                     # Launch Desktop Orb
└── help [command]          # Help for any command
```

---

## Security

### Key Protection

| Measure | Detail |
|:--------|:-------|
| **Private key** | Stored in `~/.alpha-id/keys/`, readable only by owner (`chmod 600`) |
| **Encryption at rest** | Profile and memory encrypted with AES-256-GCM |
| **Encryption in transit** | Local IPC only (Unix sockets on Linux/macOS, named pipes on Windows) |
| **No cloud backup** | Keys never leave your machine |
| **Passphrase optional** | Additional encryption layer for exported backups |

### Voiceprint Security

- Voiceprint is stored **locally** — never transmitted
- Feature vectors, not raw audio
- Daily tier is passive (continuous sampling)
- Sensitive and Critical tiers require active confirmation

### Threat Model

| Threat | Mitigation |
|:-------|:-----------|
| **Physical access to machine** | Private key encrypted at rest; OS-level file permissions |
| **Malware reading keys** | Keys are `chmod 600`; Alpha-ID never exposes keys to other processes |
| **MCP client abuse** | Scoped resource URIs; read-only by default |
| **Relay compromise** | Relay stores no persistent data; all ephemeral |
| **Voice replay attack** | Voice lock uses liveness detection |

### Best Practices

```bash
# 1. Encrypt your backup
aid identity export ~/backup/ --passphrase

# 2. Store backup offline
# USB drive. Not cloud storage. Not email.

# 3. Set a voice PIN for critical operations
aid voice enroll --pin

# 4. Regularly prune old episodic memory
aid memory prune --older-than 90d

# 5. Review active MCP connections
aid mcp status
```

---

## Troubleshooting

### Installation Issues

| Problem | Likely Cause | Solution |
|:--------|:-------------|:---------|
| `pip install` fails | Missing build deps | `apt install build-essential` (Linux) or Xcode CLI tools (macOS) |
| `aid: command not found` | PATH not set | `export PATH=$PATH:~/.local/bin` |
| Module import errors | Python version | Check `python3 --version` ≥ 3.10 |
| Permission denied | User write access | Ensure `~/.alpha-id/` is writable |

### Daemon Issues

| Problem | Likely Cause | Solution |
|:--------|:-------------|:---------|
| Daemon won't start | Port conflict | `lsof -i :8420` → kill the process, or change port in config |
| Daemon crashes on boot | Config corruption | `aid daemon stop && rm ~/.alpha-id/config.toml && aid init` |
| Daemon high CPU | Collector loop stuck | `aid daemon restart`; if persists, disable browser collector |
| Daemon not auto-starting | Systemd/user error | `aid daemon enable --verbose` for diagnostics |

### MCP Issues

| Problem | Likely Cause | Solution |
|:--------|:-------------|:---------|
| Tool not showing resources | MCP client restart needed | Restart Claude Desktop / Cursor after `aid mcp install` |
| Resources return empty | Daemon not running | Start daemon first |
| Permission denied | Resource scope | Some resources need `--allow-sensitive` flag |
| Injection not detected | MCP client path | `aid mcp install --force` to override |

### Spirit Issues

| Problem | Likely Cause | Solution |
|:--------|:-------------|:---------|
| Spirit not responding | Daemon offline | Check `aid daemon status` |
| Trust stuck at low | Sustained negative interactions | Use `aid spirit talk` with positive input to rebuild |
| Spirit feels repetitive | Not enough data | Use collectors to enrich profile |
| Evolution not progressing | Interaction count threshold | Check `aid spirit status` for exact progress |
| Wrong planet/animal | Initial observation may misfire | This is rare; run `aid wizard --retry` to re-calibrate |

### Voice Issues

| Problem | Likely Cause | Solution |
|:--------|:-------------|:---------|
| Microphone not detected | Driver issue | `aid voice mic list` to verify detection |
| Voice lock failing | Background noise | Enroll in a quiet environment; retry 3+ times |
| Commands not recognized | Accent/pronunciation | Use text alternative; model adapts over time |
| Voice-to-note inaccurate | Microphone quality | External mic recommended for best accuracy |

### Web Universe Issues

| Problem | Likely Cause | Solution |
|:--------|:-------------|:---------|
| 3D scene not loading | WebGL not supported | Use Chrome 120+ or Firefox 90+ |
| Danmaku not visible | Filter settings | Check danmaku filters in Settings |
| Memory Palace empty | Insufficient data | Interact more → memories accumulate |
| Can't find your star | Zoom level | Press `F` to focus on your star |

---

## FAQ

### General

**Q: Is Alpha-ID free?**
A: Yes. Alpha-ID is open-source (MIT). No subscriptions, no hidden tiers. The core identity layer, CLI, and web universe are completely free. Future optional relay services (for cross-device sync) may have a nominal fee for relay bandwidth.

**Q: Do I need an internet connection?**
A: No. All core features work offline: identity, profile, spirit, collectors, and most of the simulation disk. Internet is only needed for danmaku, real-time chat, and optional sync.

**Q: What happens if Alpha-ID shuts down?**
A: Nothing. Your identity, data, and all core features are local. The project being open-source means anyone can run their own relay or use without any server. Alpha-ID cannot be "shut down" for existing users.

**Q: How is this different from other AI identity projects?**
A: Most are either OAuth wrappers (platform-controlled), memory databases (vendor-locked), or AI assistants (not identity layers). Alpha-ID is the first **identity-first** layer — not a tool, but the layer under all tools.

### Technical

**Q: What is a DID exactly?**
A: A Decentralized Identifier (W3C standard). Unlike an email or OAuth account, a DID is generated and controlled entirely by you. No company, server, or registry can revoke it. It's like a cryptocurrency wallet — but for your identity.

**Q: How secure are Ed25519 keys?**
A: Ed25519 is the same algorithm used by SSH, Tor, and major blockchain projects. Provides ~128-bit security level. With current hardware, breaking an Ed25519 key would take longer than the age of the universe.

**Q: Can I use the same DID on multiple machines?**
A: Yes, by copying your `~/.alpha-id/keys/` directory. You can use `aid identity export` and `aid identity import` to transfer. Future versions will support secure relay-based sync (end-to-end encrypted).

**Q: Does Alpha-ID upload my data anywhere?**
A: No. The relay server handles only ephemeral features (chat, danmaku) and stores nothing persistently. Profile, memory, keys, and voiceprint are always local. You can audit this in the open-source code.

**Q: What's the performance impact of the daemon?**
A: Typically 0.3% CPU and ~50 MB RAM. The daemon is optimized for low resource usage — it's designed to run continuously in the background.

### Spirit

**Q: Is the spirit actually conscious?**
A: No. The spirit is a complex behavioral model — it simulates internal drives, builds trust, and makes autonomous decisions within defined boundaries. It's designed to *feel* alive through homeostasis, curiosity cycles, and trust calibration, not through actual consciousness.

**Q: Can my spirit die?**
A: Your spirit never "dies," but it can enter a dormant state if left unattended for extended periods (no interaction for 30+ days). A dormant spirit needs a brief re-acquaintance session to wake up.

**Q: Can I reset my spirit?**
A: Yes. `aid wizard --reset` re-observes your behavior and generates a new spirit. Your historical data is archived but the new spirit starts fresh. Some users do this after major life changes.

**Q: Do multiple devices share the same spirit?**
A: If you copy your identity (including profile data) across devices, the spirit carries its state. If you `aid init` fresh on a new device, you get a new spirit based on that device's observations.

### Simulation Disk

**Q: Do I need to play all 9 realms?**
A: No. Each realm is independent. Play the ones that interest you. Each realm you play adds a dimension to your profile — more realms = richer data = more personalized AI tool behavior.

**Q: Is the simulation disk a game?**
A: It looks like a game, but it's a **data collection engine**. The game-like interface exists because playing reveals behavioral patterns that forms and surveys never could. You reveal who you are by *doing*, not by *answering*.

**Q: Can other users see my simulation data?**
A: No. Simulation data is private and local. Only aggregated, opt-in data (like achievements) appears in the danmaku stream.

### MCP

**Q: What is MCP?**
A: Model Context Protocol — an open standard for AI tools to access context resources. Claude Desktop, Cursor, Windsurf, and others support MCP. Alpha-ID implements an MCP server that exposes your identity as resources.

**Q: Which tools are supported?**
A: Currently: Claude Desktop, Cursor, Windsurf. Any tool that implements the MCP client specification is compatible. The injection mechanism auto-detects supported tools.

**Q: Is MCP secure?**
A: MCP is a local protocol — communication happens over localhost. No data leaves your machine through the MCP connection. Each resource can be individually scoped and permissions-controlled.

**Q: What if my tool doesn't support MCP?**
A: Alpha-ID falls back to clipboard injection for non-MCP tools. Copy profile data as formatted text, paste into any tool. Less elegant, same result.

---

## Appendix: Configuration

### `~/.alpha-id/config.toml`

```toml
[core]
data_dir = "~/.alpha-id"
debug = false

[daemon]
port_web = 8420
port_mcp = 8421
auto_start = false
log_level = "info"

[profile]
auto_collect = true
confidence_threshold = 0.3
max_memory_events = 10000

[spirit]
tick_interval = 15        # seconds
curiosity_rate = 0.02
energy_decay = 0.01
trust_decay = 0.005

[voice]
microphone = "default"
enrolled = false
lock_enabled = false
sensitivity = 0.8

[web]
open_on_start = false
theme = "system"           # "light" | "dark" | "system"

[privacy]
danmaku_enabled = true
public_profile = false
ghost_mode = false
```

---

## Appendix: Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `ALPHA_ID_DIR` | Data directory | `~/.alpha-id` |
| `ALPHA_ID_PORT` | Web UI port | `8420` |
| `ALPHA_ID_MCP_PORT` | MCP server port | `8421` |
| `ALPHA_ID_DEBUG` | Debug mode | `false` |
| `ALPHA_ID_NO_COLOR` | Disable color output | `false` |
| `ALPHA_ID_CONFIG` | Config file path | `~/.alpha-id/config.toml` |

---

## Appendix: File Formats

### `did.json` (W3C DID Core)

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "id": "did:aid:z6Mkpz1x1Xx1x1Xx1x1Xx",
  "verificationMethod": [{
    "id": "did:aid:z6Mkpz1x1Xx1x1Xx1x1Xx#keys-1",
    "type": "Ed25519VerificationKey2020",
    "controller": "did:aid:z6Mkpz1x1Xx1x1Xx1x1Xx",
    "publicKeyMultibase": "z6Mkpz1x1Xx1x1Xx1x1Xx"
  }],
  "authentication": ["did:aid:z6Mkpz1x1Xx1x1Xx1x1Xx#keys-1"],
  "assertionMethod": ["did:aid:z6Mkpz1x1Xx1x1Xx1x1Xx#keys-1"]
}
```

### Serial Number Assignment

Serial numbers are assigned by the relay in connection order:

```
#1  → First user to connect to the relay
#42 → 42nd user to connect
#N  → Nth user to connect
```

Numbers are never recycled. A serial number is a **historical coordinate** — "I was here" — not a ranking.

---

*Alpha-ID — Your digital soul. One install, every AI tool knows you.*
