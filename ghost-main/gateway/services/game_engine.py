"""Game Generation Service — Template-based HTML5 game generator
==============================================================

Generates simple but playable browser games as standalone HTML files.
Each game is a self-contained HTML document with embedded CSS and JavaScript,
themed according to the requested visual style.

Supported game types:
  - space_shooter: Classic space shooter with enemies and projectiles
  - platformer: Side-scrolling platformer with jumping mechanics
  - puzzle: Grid-based puzzle game (memory match)
  - racing: Top-down racing game
  - rpg: Simple dungeon crawler RPG

Supported themes:
  - cyberpunk: Neon colors, dark backgrounds, futuristic UI
  - japanese_anime: Pastel colors, cute UI elements
  - pixel_art: Retro pixelated aesthetic
  - low_poly: Geometric shapes, flat colors
  - realistic: Natural colors, realistic UI
"""

import logging
import os
import time
import uuid
from pathlib import Path

logger = logging.getLogger("ghost-gateway")

# ── Configuration ────────────────────────────────────────────────────────────

# Directory where generated game HTML files are stored
# In Docker, this should be a volume mount so games persist and are served
GAME_STORAGE_DIR = os.getenv("GAME_STORAGE_DIR", "/app/generated_games")

# Public URL prefix for accessing generated games
GAME_PUBLIC_URL = os.getenv("GAME_PUBLIC_URL", "http://localhost:18080/games")

# Ensure storage directory exists
Path(GAME_STORAGE_DIR).mkdir(parents=True, exist_ok=True)


# ── Theme Definitions ────────────────────────────────────────────────────────

THEME_STYLES = {
    "cyberpunk": {
        "bg": "#0a0a1a",
        "primary": "#00fff0",
        "secondary": "#ff00ff",
        "accent": "#ffff00",
        "text": "#e0e0ff",
        "font": "'Courier New', monospace",
        "glow": "0 0 10px rgba(0,255,240,0.5)",
        "gradient": "linear-gradient(135deg, #0a0a1a, #1a0a2e)",
    },
    "japanese_anime": {
        "bg": "#fff5f5",
        "primary": "#ff6b9d",
        "secondary": "#c44dff",
        "accent": "#ffd93d",
        "text": "#4a4a6a",
        "font": "'Segoe UI', sans-serif",
        "glow": "0 0 8px rgba(255,107,157,0.3)",
        "gradient": "linear-gradient(135deg, #fff5f5, #ffe8f0)",
    },
    "pixel_art": {
        "bg": "#1a1c2c",
        "primary": "#f4f4f4",
        "secondary": "#ff0044",
        "accent": "#00e436",
        "text": "#f4f4f4",
        "font": "'Courier New', monospace",
        "glow": "none",
        "gradient": "linear-gradient(135deg, #1a1c2c, #2a2c3c)",
    },
    "low_poly": {
        "bg": "#87CEEB",
        "primary": "#2d5016",
        "secondary": "#8B4513",
        "accent": "#FFD700",
        "text": "#1a1a1a",
        "font": "'Segoe UI', sans-serif",
        "glow": "none",
        "gradient": "linear-gradient(180deg, #87CEEB, #E0F6FF)",
    },
    "realistic": {
        "bg": "#2c2c2c",
        "primary": "#e0e0e0",
        "secondary": "#a0a0a0",
        "accent": "#4a90d9",
        "text": "#e0e0e0",
        "font": "'Segoe UI', sans-serif",
        "glow": "0 2px 4px rgba(0,0,0,0.3)",
        "gradient": "linear-gradient(135deg, #2c2c2c, #3c3c3c)",
    },
}


def _get_theme(game_type: str, theme: str) -> dict:
    """Get theme styles with fallback defaults."""
    return THEME_STYLES.get(theme, THEME_STYLES["cyberpunk"])


def _generate_game_id() -> str:
    """Generate unique game identifier."""
    return uuid.uuid4().hex[:12]


# ── Game Template Generators ─────────────────────────────────────────────────

def _generate_space_shooter(theme: str, description: str) -> str:
    """Generate a space shooter game HTML."""
    t = _get_theme("space_shooter", theme)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Space Shooter — {theme.title()}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {t['bg']};
            color: {t['text']};
            font-family: {t['font']};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow: hidden;
        }}
        #gameCanvas {{
            border: 2px solid {t['primary']};
            box-shadow: {t['glow']};
            background: {t['gradient']};
            max-width: 100%;
            max-height: 80vh;
        }}
        .info {{
            margin-top: 10px;
            font-size: 14px;
            color: {t['text']};
            text-align: center;
        }}
        .title {{
            font-size: 24px;
            margin-bottom: 10px;
            color: {t['primary']};
            text-shadow: {t['glow']};
        }}
        .controls {{
            font-size: 12px;
            color: {t['secondary']};
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="title">🚀 Space Shooter — {theme.title()}</div>
    <canvas id="gameCanvas" width="600" height="400"></canvas>
    <div class="info">Score: <span id="score">0</span> | Lives: <span id="lives">3</span></div>
    <div class="controls">← → 移动 | SPACE 射击 | 消灭敌人获得分数</div>
    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const scoreEl = document.getElementById('score');
        const livesEl = document.getElementById('lives');

        // Player
        const player = {{
            x: canvas.width / 2 - 20,
            y: canvas.height - 50,
            width: 40,
            height: 30,
            speed: 5,
            color: '{t['primary']}'
        }};

        // Game state
        let bullets = [];
        let enemies = [];
        let particles = [];
        let score = 0;
        let lives = 3;
        let keys = {{}};

        // Input
        document.addEventListener('keydown', (e) => {{
            keys[e.key] = true;
            if (e.key === ' ' && !e.repeat) {{
                bullets.push({{ x: player.x + player.width / 2, y: player.y, speed: -8, width: 4, height: 10 }});
            }}
        }});
        document.addEventListener('keyup', (e) => keys[e.key] = false);

        // Spawn enemies
        function spawnEnemy() {{
            const types = ['basic', 'fast', 'tank'];
            const type = types[Math.floor(Math.random() * types.length)];
            let width = 30, height = 30, hp = 1, speed = 2;
            if (type === 'fast') {{ speed = 4; width = 25; height = 25; }}
            if (type === 'tank') {{ hp = 3; width = 45; height = 40; speed = 1; }}
            enemies.push({{
                x: Math.random() * (canvas.width - width),
                y: -height,
                width, height, hp, speed, type,
                color: type === 'tank' ? '#ff4444' : type === 'fast' ? '#ffaa00' : '{t['secondary']}'
            }});
        }}

        // Update
        function update() {{
            // Player movement
            if (keys['ArrowLeft'] && player.x > 0) player.x -= player.speed;
            if (keys['ArrowRight'] && player.x < canvas.width - player.width) player.x += player.speed;

            // Bullets
            bullets = bullets.filter(b => {{
                b.y += b.speed;
                return b.y > -10;
            }});

            // Enemies
            enemies = enemies.filter(e => {{
                e.y += e.speed;
                if (e.y > canvas.height) return false;
                return true;
            }});

            // Collision: bullets vs enemies
            bullets.forEach((b, bi) => {{
                enemies.forEach((e, ei) => {{
                    if (b.x > e.x && b.x < e.x + e.width &&
                        b.y > e.y && b.y < e.y + e.height) {{
                        e.hp--;
                        bullets.splice(bi, 1);
                        if (e.hp <= 0) {{
                            enemies.splice(ei, 1);
                            score += e.type === 'tank' ? 30 : e.type === 'fast' ? 20 : 10;
                            scoreEl.textContent = score;
                        }}
                    }}
                }});
            }});

            // Collision: enemies vs player
            enemies.forEach((e, ei) => {{
                if (e.x < player.x + player.width &&
                    e.x + e.width > player.x &&
                    e.y < player.y + player.height &&
                    e.y + e.height > player.y) {{
                    enemies.splice(ei, 1);
                    lives--;
                    livesEl.textContent = lives;
                    if (lives <= 0) {{
                        alert('游戏结束！最终得分: ' + score);
                        location.reload();
                    }}
                }}
            }});

            // Spawn enemies periodically
            if (Math.random() < 0.02) spawnEnemy();
        }}

        // Draw
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Player (triangle spaceship)
            ctx.fillStyle = player.color;
            ctx.beginPath();
            ctx.moveTo(player.x + player.width / 2, player.y);
            ctx.lineTo(player.x, player.y + player.height);
            ctx.lineTo(player.x + player.width, player.y + player.height);
            ctx.closePath();
            ctx.fill();

            // Bullets
            ctx.fillStyle = '{t['accent']}';
            bullets.forEach(b => {{
                ctx.fillRect(b.x - b.width / 2, b.y, b.width, b.height);
            }});

            // Enemies
            enemies.forEach(e => {{
                ctx.fillStyle = e.color;
                ctx.fillRect(e.x, e.y, e.width, e.height);
                // HP indicator for tanks
                if (e.type === 'tank') {{
                    ctx.fillStyle = '#fff';
                    ctx.fillRect(e.x, e.y - 5, e.width * (e.hp / 3), 3);
                }}
            }});

            // Particles
            particles = particles.filter(p => {{
                p.x += p.vx;
                p.y += p.vy;
                p.life -= 0.02;
                if (p.life <= 0) return false;
                ctx.globalAlpha = p.life;
                ctx.fillStyle = p.color;
                ctx.fillRect(p.x, p.y, p.size, p.size);
                ctx.globalAlpha = 1;
                return true;
            }});
        }}

        // Game loop
        function gameLoop() {{
            update();
            draw();
            requestAnimationFrame(gameLoop);
        }}

        gameLoop();
    </script>
</body>
</html>"""


def _generate_platformer(theme: str, description: str) -> str:
    """Generate a platformer game HTML."""
    t = _get_theme("platformer", theme)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Platformer — {theme.title()}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {t['bg']};
            color: {t['text']};
            font-family: {t['font']};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        #gameCanvas {{
            border: 2px solid {t['primary']};
            box-shadow: {t['glow']};
            background: {t['gradient']};
            max-width: 100%;
        }}
        .info {{ margin-top: 10px; font-size: 14px; }}
        .title {{
            font-size: 24px; margin-bottom: 10px;
            color: {t['primary']}; text-shadow: {t['glow']};
        }}
        .controls {{ font-size: 12px; color: {t['secondary']}; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="title">🏃 Platformer — {theme.title()}</div>
    <canvas id="gameCanvas" width="800" height="400"></canvas>
    <div class="info">Coins: <span id="coins">0</span> | Level: <span id="level">1</span></div>
    <div class="controls">← → 移动 | SPACE/↑ 跳跃 | 收集金币到达终点</div>
    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const coinsEl = document.getElementById('coins');
        const levelEl = document.getElementById('level');

        const gravity = 0.6;
        const player = {{
            x: 50, y: 200, width: 30, height: 40,
            vx: 0, vy: 0, speed: 5, jumpPower: -12,
            onGround: false, color: '{t['primary']}'
        }};

        let platforms = [];
        let coins = [];
        let particles = [];
        let score = 0;
        let level = 1;
        let keys = {{}};
        let cameraX = 0;

        function generateLevel(lvl) {{
            platforms = [
                {{ x: 0, y: 350, width: 800, height: 50 }},  // ground
                {{ x: 200, y: 280, width: 120, height: 20 }},
                {{ x: 400, y: 220, width: 100, height: 20 }},
                {{ x: 580, y: 160, width: 80, height: 20 }},
                {{ x: 700, y: 280, width: 150, height: 20 }},
            ];
            if (lvl > 1) {{
                platforms.push(
                    {{ x: 900, y: 280, width: 100, height: 20 }},
                    {{ x: 1050, y: 200, width: 80, height: 20 }}
                );
            }}
            coins = [
                {{ x: 250, y: 240, collected: false }},
                {{ x: 430, y: 180, collected: false }},
                {{ x: 600, y: 120, collected: false }},
                {{ x: 750, y: 240, collected: false }},
            ];
        }}

        generateLevel(level);

        document.addEventListener('keydown', (e) => {{
            keys[e.key] = true;
            if ((e.key === ' ' || e.key === 'ArrowUp') && player.onGround) {{
                player.vy = player.jumpPower;
                player.onGround = false;
            }}
        }});
        document.addEventListener('keyup', (e) => keys[e.key] = false);

        function update() {{
            // Horizontal movement
            player.vx = 0;
            if (keys['ArrowLeft']) player.vx = -player.speed;
            if (keys['ArrowRight']) player.vx = player.speed;

            player.x += player.vx;
            player.vy += gravity;
            player.y += player.vy;

            // Platform collision
            player.onGround = false;
            platforms.forEach(p => {{
                if (player.x < p.x + p.width &&
                    player.x + player.width > p.x &&
                    player.y + player.height > p.y &&
                    player.y + player.height < p.y + p.height + 10 &&
                    player.vy >= 0) {{
                    player.y = p.y - player.height;
                    player.vy = 0;
                    player.onGround = true;
                }}
            }});

            // Fall death
            if (player.y > canvas.height) {{
                player.x = 50; player.y = 200; player.vy = 0;
            }}

            // Coin collection
            coins.forEach(c => {{
                if (!c.collected &&
                    player.x < c.x + 15 && player.x + player.width > c.x &&
                    player.y < c.y + 15 && player.y + player.height > c.y) {{
                    c.collected = true;
                    score++;
                    coinsEl.textContent = score;
                }}
            }});

            // Level complete
            const allCollected = coins.every(c => c.collected);
            if (allCollected) {{
                level++;
                levelEl.textContent = level;
                player.x = 50; player.y = 200; player.vy = 0;
                generateLevel(level);
            }}

            // Camera
            cameraX = Math.max(0, player.x - canvas.width / 3);
        }}

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();
            ctx.translate(-cameraX, 0);

            // Platforms
            ctx.fillStyle = '{t['secondary']}';
            platforms.forEach(p => {{
                ctx.fillRect(p.x, p.y, p.width, p.height);
            }});

            // Coins
            coins.forEach(c => {{
                if (!c.collected) {{
                    ctx.fillStyle = '{t['accent']}';
                    ctx.beginPath();
                    ctx.arc(c.x + 7, c.y + 7, 8, 0, Math.PI * 2);
                    ctx.fill();
                }}
            }});

            // Player
            ctx.fillStyle = player.color;
            ctx.fillRect(player.x, player.y, player.width, player.height);

            ctx.restore();
        }}

        function gameLoop() {{
            update();
            draw();
            requestAnimationFrame(gameLoop);
        }}

        gameLoop();
    </script>
</body>
</html>"""


def _generate_puzzle(theme: str, description: str) -> str:
    """Generate a memory puzzle game HTML."""
    t = _get_theme("puzzle", theme)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Puzzle — {theme.title()}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {t['bg']};
            color: {t['text']};
            font-family: {t['font']};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        #gameBoard {{
            display: grid;
            grid-template-columns: repeat(4, 80px);
            gap: 8px;
            margin: 20px 0;
        }}
        .card {{
            width: 80px; height: 80px;
            background: {t['secondary']};
            border: 2px solid {t['primary']};
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: {t['glow']};
        }}
        .card:hover {{ transform: scale(1.05); }}
        .card.flipped {{ background: {t['bg']}; border-color: {t['accent']}; }}
        .card.matched {{ opacity: 0.5; cursor: default; }}
        .title {{
            font-size: 24px; margin-bottom: 10px;
            color: {t['primary']}; text-shadow: {t['glow']};
        }}
        .info {{ font-size: 14px; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="title">🧩 Memory Puzzle — {theme.title()}</div>
    <div class="info">Moves: <span id="moves">0</span> | Pairs: <span id="pairs">0</span>/8</div>
    <div id="gameBoard"></div>
    <script>
        const symbols = ['🎮', '🚀', '⭐', '🌙', '💎', '🔥', '🎵', '🌈'];
        let cards = [...symbols, ...symbols].sort(() => Math.random() - 0.5);
        let flipped = [];
        let matched = 0;
        let moves = 0;
        let locked = false;

        const board = document.getElementById('gameBoard');
        const movesEl = document.getElementById('moves');
        const pairsEl = document.getElementById('pairs');

        cards.forEach((symbol, i) => {{
            const card = document.createElement('div');
            card.className = 'card';
            card.dataset.index = i;
            card.dataset.symbol = symbol;
            card.textContent = '?';
            card.addEventListener('click', () => flipCard(card));
            board.appendChild(card);
        }});

        function flipCard(card) {{
            if (locked || card.classList.contains('flipped') || card.classList.contains('matched')) return;

            card.classList.add('flipped');
            card.textContent = card.dataset.symbol;
            flipped.push(card);

            if (flipped.length === 2) {{
                moves++;
                movesEl.textContent = moves;
                locked = true;
                if (flipped[0].dataset.symbol === flipped[1].dataset.symbol) {{
                    flipped.forEach(c => c.classList.add('matched'));
                    matched++;
                    pairsEl.textContent = matched;
                    flipped = [];
                    locked = false;
                    if (matched === 8) {{
                        setTimeout(() => alert('恭喜完成！移动次数: ' + moves), 300);
                    }}
                }} else {{
                    setTimeout(() => {{
                        flipped.forEach(c => {{ c.classList.remove('flipped'); c.textContent = '?'; }});
                        flipped = [];
                        locked = false;
                    }}, 1000);
                }}
            }}
        }}
    </script>
</body>
</html>"""


def _generate_racing(theme: str, description: str) -> str:
    """Generate a racing game HTML."""
    t = _get_theme("racing", theme)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Racing — {theme.title()}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {t['bg']};
            color: {t['text']};
            font-family: {t['font']};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        #gameCanvas {{
            border: 2px solid {t['primary']};
            box-shadow: {t['glow']};
            background: {t['gradient']};
            max-width: 100%;
        }}
        .info {{ margin-top: 10px; font-size: 14px; }}
        .title {{
            font-size: 24px; margin-bottom: 10px;
            color: {t['primary']}; text-shadow: {t['glow']};
        }}
        .controls {{ font-size: 12px; color: {t['secondary']}; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="title">🏎️ Racing — {theme.title()}</div>
    <canvas id="gameCanvas" width="400" height="500"></canvas>
    <div class="info">Score: <span id="score">0</span> | Speed: <span id="speed">5</span></div>
    <div class="controls">← → 转向 | ↑ 加速 | ↓ 减速 | 躲避障碍物</div>
    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const scoreEl = document.getElementById('score');
        const speedEl = document.getElementById('speed');

        const road = {{ x: 100, width: 200 }};
        let playerCar = {{ x: 190, y: 400, width: 30, height: 50, speed: 5 }};
        let obstacles = [];
        let score = 0;
        let keys = {{}};

        document.addEventListener('keydown', (e) => keys[e.key] = true);
        document.addEventListener('keyup', (e) => keys[e.key] = false);

        function spawnObstacle() {{
            const lane = road.x + Math.random() * (road.width - 40);
            obstacles.push({{
                x: lane, y: -50, width: 30, height: 50,
                speed: 3 + Math.random() * 3, color: '#ff4444'
            }});
        }}

        function update() {{
            // Player
            if (keys['ArrowLeft'] && playerCar.x > road.x) playerCar.x -= 3;
            if (keys['ArrowRight'] && playerCar.x < road.x + road.width - playerCar.width) playerCar.x += 3;
            if (keys['ArrowUp'] && playerCar.speed < 12) playerCar.speed += 0.1;
            if (keys['ArrowDown'] && playerCar.speed > 2) playerCar.speed -= 0.1;

            // Obstacles
            obstacles = obstacles.filter(o => {{
                o.y += o.speed - playerCar.speed * 0.3;
                if (o.y > canvas.height) {{ score += 10; scoreEl.textContent = score; return false; }}
                return true;
            }});

            // Collision
            obstacles.forEach(o => {{
                if (playerCar.x < o.x + o.width &&
                    playerCar.x + playerCar.width > o.x &&
                    playerCar.y < o.y + o.height &&
                    playerCar.y + playerCar.height > o.y) {{
                    alert('碰撞！游戏结束。得分: ' + score);
                    location.reload();
                }}
            }});

            if (Math.random() < 0.02) spawnObstacle();
            speedEl.textContent = playerCar.speed.toFixed(1);
        }}

        function draw() {{
            // Road
            ctx.fillStyle = '#333';
            ctx.fillRect(road.x, 0, road.width, canvas.height);
            // Lane markings
            ctx.strokeStyle = '#fff';
            ctx.setLineDash([20, 20]);
            ctx.lineDashOffset -= playerCar.speed;
            for (let i = 0; i < 5; i++) {{
                ctx.beginPath();
                ctx.moveTo(road.x + road.width / 2, i * 120);
                ctx.lineTo(road.x + road.width / 2, i * 120 + 60);
                ctx.stroke();
            }}
            ctx.setLineDash([]);

            // Player car
            ctx.fillStyle = '{t['primary']}';
            ctx.fillRect(playerCar.x, playerCar.y, playerCar.width, playerCar.height);

            // Obstacles
            obstacles.forEach(o => {{
                ctx.fillStyle = o.color;
                ctx.fillRect(o.x, o.y, o.width, o.height);
            }});
        }}

        function gameLoop() {{
            update();
            draw();
            requestAnimationFrame(gameLoop);
        }}

        gameLoop();
    </script>
</body>
</html>"""


def _generate_rpg(theme: str, description: str) -> str:
    """Generate a simple RPG dungeon crawler game HTML."""
    t = _get_theme("rpg", theme)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPG Dungeon — {theme.title()}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {t['bg']};
            color: {t['text']};
            font-family: {t['font']};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        #gameCanvas {{
            border: 2px solid {t['primary']};
            box-shadow: {t['glow']};
            background: #111;
            max-width: 100%;
        }}
        .info {{ margin-top: 10px; font-size: 14px; }}
        .title {{
            font-size: 24px; margin-bottom: 10px;
            color: {t['primary']}; text-shadow: {t['glow']};
        }}
        .controls {{ font-size: 12px; color: {t['secondary']}; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="title">⚔️ RPG Dungeon — {theme.title()}</div>
    <canvas id="gameCanvas" width="600" height="400"></canvas>
    <div class="info">HP: <span id="hp">100</span> | Level: <span id="level">1</span> | Enemies: <span id="enemies">0</span></div>
    <div class="controls">← → ↑ ↓ 移动 | 空格 攻击 | 探索地牢击败敌人</div>
    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const hpEl = document.getElementById('hp');
        const levelEl = document.getElementById('level');
        const enemiesEl = document.getElementById('enemies');

        const tileSize = 40;
        const mapWidth = 15;
        const mapHeight = 10;

        // Simple dungeon map: 0=floor, 1=wall, 2=exit
        const dungeon = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
            [1,0,1,0,1,0,1,1,1,0,1,0,1,0,1],
            [1,0,1,0,0,0,0,0,1,0,0,0,1,0,1],
            [1,0,1,1,1,1,1,0,1,1,1,0,1,0,1],
            [1,0,0,0,0,0,1,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,0,1,1,1,0,1,1,1,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,1,1,1,1,1,1,1,1,1,1,1,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        ];

        const player = {{ x: 1, y: 1, hp: 100, level: 1, attack: 10, color: '{t['primary']}' }};
        let enemies = [];
        let particles = [];
        let keys = {{}};

        function spawnEnemies(count) {{
            enemies = [];
            for (let i = 0; i < count; i++) {{
                let ex, ey;
                do {{
                    ex = Math.floor(Math.random() * mapWidth);
                    ey = Math.floor(Math.random() * mapHeight);
                }} while (dungeon[ey][ex] !== 0 || (ex === player.x && ey === player.y));
                enemies.push({{ x: ex, y: ey, hp: 30, attack: 5, color: '#ff4444' }});
            }}
            enemiesEl.textContent = enemies.length;
        }}

        spawnEnemies(5);

        document.addEventListener('keydown', (e) => {{
            keys[e.key] = true;
            if (e.key === ' ') attack();
        }});
        document.addEventListener('keyup', (e) => keys[e.key] = false);

        function movePlayer(dx, dy) {{
            const newX = player.x + dx;
            const newY = player.y + dy;
            if (newX >= 0 && newX < mapWidth && newY >= 0 && newY < mapHeight && dungeon[newY][newX] !== 1) {{
                player.x = newX;
                player.y = newY;
                // Check enemy collision
                enemies.forEach((e, i) => {{
                    if (e.x === newX && e.y === newY) {{
                        player.hp -= e.attack;
                        hpEl.textContent = Math.max(0, player.hp);
                        if (player.hp <= 0) {{
                            alert('你被击败了！');
                            location.reload();
                        }}
                    }}
                }});
            }}
        }}

        function attack() {{
            enemies.forEach((e, i) => {{
                if (Math.abs(e.x - player.x) <= 1 && Math.abs(e.y - player.y) <= 1) {{
                    e.hp -= player.attack;
                    if (e.hp <= 0) {{
                        enemies.splice(i, 1);
                        enemiesEl.textContent = enemies.length;
                        score += 50;
                        if (enemies.length === 0) {{
                            player.level++;
                            levelEl.textContent = player.level;
                            spawnEnemies(3 + player.level);
                        }}
                    }}
                }}
            }});
        }}

        function update() {{
            if (keys['ArrowLeft']) movePlayer(-1, 0);
            if (keys['ArrowRight']) movePlayer(1, 0);
            if (keys['ArrowUp']) movePlayer(0, -1);
            if (keys['ArrowDown']) movePlayer(0, 1);
        }}

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            for (let y = 0; y < mapHeight; y++) {{
                for (let x = 0; x < mapWidth; x++) {{
                    if (dungeon[y][x] === 1) {{
                        ctx.fillStyle = '#444';
                        ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
                    }} else {{
                        ctx.fillStyle = '#222';
                        ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
                        ctx.strokeStyle = '#333';
                        ctx.strokeRect(x * tileSize, y * tileSize, tileSize, tileSize);
                    }}
                }}
            }}
            // Player
            ctx.fillStyle = player.color;
            ctx.fillRect(player.x * tileSize + 5, player.y * tileSize + 5, tileSize - 10, tileSize - 10);
            // Enemies
            enemies.forEach(e => {{
                ctx.fillStyle = e.color;
                ctx.fillRect(e.x * tileSize + 5, e.y * tileSize + 5, tileSize - 10, tileSize - 10);
            }});
        }}

        function gameLoop() {{
            update();
            draw();
            requestAnimationFrame(gameLoop);
        }}

        gameLoop();
    </script>
</body>
</html>"""


# ── Main Generation Function ─────────────────────────────────────────────────

GAME_TEMPLATES = {
    "space_shooter": _generate_space_shooter,
    "platformer": _generate_platformer,
    "puzzle": _generate_puzzle,
    "racing": _generate_racing,
    "rpg": _generate_rpg,
}


async def generate_game(
    game_type: str,
    theme: str,
    description: str = "",
) -> dict:
    """Generate a game HTML file and return metadata.

    Args:
        game_type: Type of game (space_shooter, platformer, puzzle, racing, rpg)
        theme: Visual theme (cyberpunk, japanese_anime, pixel_art, low_poly, realistic)
        description: Optional description for customization

    Returns:
        dict with game_id, game_type, theme, game_url, status

    Raises:
        ValueError: If game_type is not supported
    """
    if game_type not in GAME_TEMPLATES:
        raise ValueError(
            f"Unsupported game type: '{game_type}'. "
            f"Supported: {', '.join(GAME_TEMPLATES.keys())}"
        )

    generator = GAME_TEMPLATES[game_type]
    game_id = _generate_game_id()

    # Generate HTML content
    html_content = generator(theme, description)

    # Write to file
    filename = f"{game_type}_{theme}_{game_id}.html"
    filepath = Path(GAME_STORAGE_DIR) / filename

    try:
        filepath.write_text(html_content, encoding="utf-8")
        logger.info(f"Generated game: {filename} ({len(html_content)} bytes)")
    except OSError as e:
        logger.error(f"Failed to write game file {filepath}: {e}")
        raise RuntimeError(f"Failed to save generated game: {e}") from e

    # Construct public URL
    game_url = f"{GAME_PUBLIC_URL.rstrip('/')}/{filename}"

    return {
        "game_id": game_id,
        "game_type": game_type,
        "theme": theme,
        "description": description,
        "game_url": game_url,
        "status": "completed",
        "file_size": len(html_content),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def get_game_status(game_id: str) -> dict:
    """Check if a generated game file exists.

    Args:
        game_id: The game identifier

    Returns:
        dict with game_id, status, game_url if found
    """
    # Search for game file by game_id
    pattern = f"*_{game_id}.html"
    matches = list(Path(GAME_STORAGE_DIR).glob(pattern))

    if not matches:
        return {
            "game_id": game_id,
            "status": "not_found",
        }

    filepath = matches[0]
    filename = filepath.name
    game_url = f"{GAME_PUBLIC_URL.rstrip('/')}/{filename}"

    # Extract game_type and theme from filename
    # Filename format: {game_type}_{theme}_{game_id}.html
    # game_type may contain underscores (e.g. "space_shooter")
    # game_id is always the last segment before .html
    base = filename.replace(".html", "")
    # Split from the right: last part is game_id, second-to-last is theme, rest is game_type
    parts = base.rsplit("_", 2)
    if len(parts) >= 3:
        game_type = parts[0]
        theme = parts[1]
    else:
        game_type = base
        theme = "unknown"

    return {
        "game_id": game_id,
        "game_type": game_type,
        "theme": theme,
        "status": "completed",
        "game_url": game_url,
        "file_size": filepath.stat().st_size,
    }


def list_generated_games(limit: int = 50) -> list[dict]:
    """List recently generated games.

    Args:
        limit: Maximum number of games to return

    Returns:
        List of game metadata dicts, sorted by newest first
    """
    games = []
    pattern = "*.html"
    files = sorted(
        Path(GAME_STORAGE_DIR).glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for filepath in files[:limit]:
        filename = filepath.name
        base = filename.replace(".html", "")
        # Filename format: {game_type}_{theme}_{game_id}.html
        # Split from the right: last part is game_id, second-to-last is theme, rest is game_type
        parts = base.rsplit("_", 2)
        if len(parts) >= 3:
            game_type = parts[0]
            theme = parts[1]
            game_id = parts[2]
        else:
            game_type = base
            theme = "unknown"
            game_id = filename

        games.append({
            "game_id": game_id,
            "game_type": game_type,
            "theme": theme,
            "filename": filename,
            "game_url": f"{GAME_PUBLIC_URL.rstrip('/')}/{filename}",
            "file_size": filepath.stat().st_size,
            "created_at": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime(filepath.stat().st_mtime),
            ),
        })

    return games
