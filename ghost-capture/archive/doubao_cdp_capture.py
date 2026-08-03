"""
Doubao CDP Capture — connects to Codex in-app browser via DevTools Protocol
Captures doubao conversations in real-time and sends to Gateway.
Runs as a background daemon.
"""

import asyncio
import json
import time
import hashlib
import logging
import requests
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("doubao_cdp")

CDP_URL = "ws://127.0.0.1:9229/devtools/browser/9456fd66-0cfa-4522-a52c-20f9d0306ef5"
GATEWAY_URL = "http://localhost:18080/v1/doubao/capture"
POLL_INTERVAL = 2.0  # seconds
SESSION_ID = "cdp-" + str(int(time.time()))
seen_hashes = set()


async def inject_capture(page):
    """Inject conversation capture logic into the doubao page."""
    
    # Inject a function that reads the page text and diffs
    await page.evaluate("""
        window.__ghost_captured = window.__ghost_captured || "";
    """)
    
    logger.info("Capture script injected into doubao page")


async def capture_loop(page):
    """Periodically read doubao page content and capture new text."""
    global seen_hashes
    
    while True:
        try:
            # Get all visible text from the page
            text = await page.evaluate("""
                () => {
                    // Get text content, excluding scripts and styles
                    const body = document.body;
                    if (!body) return "";
                    const clone = body.cloneNode(true);
                    // Remove script and style elements
                    const scripts = clone.querySelectorAll("script, style, svg, noscript");
                    for (const s of scripts) s.remove();
                    return clone.innerText || "";
                }
            """)
            
            if not text or len(text) < 50:
                await asyncio.sleep(POLL_INTERVAL)
                continue
            
            # Get the last captured text
            last_text = await page.evaluate("() => window.__ghost_captured || ''")
            
            if not last_text:
                # First capture - just store the text
                await page.evaluate(f"window.__ghost_captured = {json.dumps(text)}")
                await asyncio.sleep(POLL_INTERVAL)
                continue
            
            # Only capture if text has changed significantly
            if text == last_text:
                await asyncio.sleep(POLL_INTERVAL)
                continue
            
            # Text changed! Find the new parts
            old_lines = last_text.split("\n")
            new_lines = text.split("\n")
            
            # Find lines that are new
            old_set = set()
            for line in old_lines:
                line = line.strip()
                if len(line) > 5:
                    old_set.add(line[:80])
            
            new_messages = []
            for line in new_lines:
                line = line.strip()
                if len(line) < 5:
                    continue
                key = line[:80]
                if key not in old_set and key not in seen_hashes:
                    seen_hashes.add(key)
                    # Heuristic: short = user question, long = assistant answer
                    role = "user" if len(line) < 100 else "assistant"
                    new_messages.append({
                        "role": role,
                        "content": line,
                        "timestamp": int(time.time() * 1000)
                    })
            
            if new_messages:
                logger.info("Captured %d new messages", len(new_messages))
                
                payload = {
                    "session_id": SESSION_ID,
                    "bot_id": "doubao_web_cdp",
                    "captured_at": int(time.time()),
                    "messages": new_messages
                }
                
                try:
                    r = requests.post(GATEWAY_URL, json=payload, timeout=5)
                    logger.info("Gateway response: %s", r.status_code)
                except Exception as e:
                    logger.warning("Gateway unavailable: %s", e)
                
                # Update stored text
                await page.evaluate(f"window.__ghost_captured = {json.dumps(text)}")
            else:
                # Content changed but no new discrete messages found
                # Still update the stored text to avoid re-capturing
                await page.evaluate(f"window.__ghost_captured = {json.dumps(text)}")
            
        except Exception as e:
            logger.error("Capture error: %s", e)
        
        await asyncio.sleep(POLL_INTERVAL)


async def main():
    logger.info("Starting Doubao CDP capture daemon...")
    
    async with async_playwright() as p:
        # Connect to existing browser via CDP
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        logger.info("Connected to browser via CDP")
        
        # Get all contexts/pages
        contexts = browser.contexts
        logger.info("Browser contexts: %d", len(contexts))
        
        doubao_page = None
        
        # Try each context
        for ctx in contexts:
            pages = ctx.pages
            logger.info("Context has %d pages", len(pages))
            for page in pages:
                url = page.url
                logger.info("  Page: %s", url[:100])
                if "doubao.com" in url and "/chat" in url:
                    doubao_page = page
                    logger.info(">>> Found doubao chat page!")
                    break
            if doubao_page:
                break
        
        if not doubao_page:
            logger.error("Doubao chat page not found in browser tabs!")
            await browser.close()
            return
        
        logger.info("Starting capture on doubao page: %s", doubao_page.url[:80])
        
        # Inject capture script
        await inject_capture(doubao_page)
        
        # Start capture loop
        await capture_loop(doubao_page)


if __name__ == "__main__":
    asyncio.run(main())
