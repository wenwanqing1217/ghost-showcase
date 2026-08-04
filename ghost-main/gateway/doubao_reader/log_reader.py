"""
Doubao Chat Reader — LevelDB Log Parser
=========================================
Reads Doubao desktop app's IndexedDB (LevelDB format) to extract chat conversations.
Zero API dependency, works offline, captures phone-synced chats.

Architecture:
    Doubao Desktop App (IndexedDB LevelDB)
        → LogReader.parse_log_file()
        → deduplicated conversations
        → POST to Gateway /v1/doubao/capture
        → Alpha-ID /memory/store → DualChain knowledge chain
"""

import os
import re
import struct
import json
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("doubao_reader")

BLOCK_SIZE = 32768


@dataclass
class ChatMessage:
    """A single message in a conversation"""
    role: str = ""          # "user" or "assistant"
    content: str = ""
    timestamp: int = 0


@dataclass
class Conversation:
    """A complete conversation session"""
    session_id: str = ""
    messages: List[ChatMessage] = field(default_factory=list)
    bot_id: str = ""
    captured_at: int = 0

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "bot_id": self.bot_id,
            "captured_at": self.captured_at or int(datetime.now().timestamp()),
            "messages": [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in self.messages],
        }


class LogReader:
    """Read Doubao chat data from LevelDB write-ahead log files"""

    def __init__(self, doubao_data_dir: Optional[str] = None):
        if doubao_data_dir is None:
            doubao_data_dir = os.path.expandvars(
                r"%LOCALAPPDATA%\Doubao\User Data\Default"
            )
        self.indexeddb_dir = os.path.join(
            doubao_data_dir, "IndexedDB",
            "chrome_doubao-chat_0.indexeddb.leveldb"
        )
        self._session_hash = {}  # for dedup

    @staticmethod
    def find_log_files(ldb_dir: str) -> List[str]:
        """Find all .log files in the LevelDB directory, sorted by recency"""
        log_files = []
        if os.path.exists(ldb_dir):
            for f in os.listdir(ldb_dir):
                if f.endswith(".log"):
                    fpath = os.path.join(ldb_dir, f)
                    log_files.append((os.path.getmtime(fpath), fpath))
            log_files.sort(reverse=True)  # newest first
        return [fp for _, fp in log_files]

    @staticmethod
    def parse_log_file(log_path: str) -> List[bytes]:
        """Parse a LevelDB .log file into raw records"""
        records = []
        try:
            with open(log_path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            return records

        pos = 0
        while pos < len(data):
            block_end = min(pos + BLOCK_SIZE, len(data))
            bp = pos
            while bp < block_end - 7:
                length = struct.unpack_from("<H", data, bp + 4)[0]
                if 0 < length < 32000 and bp + 7 + length <= block_end:
                    records.append(data[bp + 7 : bp + 7 + length])
                    bp += 7 + length
                else:
                    bp += 1
            pos += BLOCK_SIZE

        return records

    @staticmethod
    def extract_utf16le_text(data: bytes) -> List[str]:
        """Extract readable text from UTF-16LE encoded segments"""
        texts = set()
        for offset in [0, 1]:  # both alignments
            aligned = data[offset:]
            aligned = aligned[:len(aligned) - len(aligned) % 2]
            if len(aligned) < 4:
                continue
            try:
                decoded = aligned.decode("utf-16-le")
                for line in decoded.split("\n"):
                    line = line.strip()
                    if len(line) >= 6:
                        texts.add(line)
            except (UnicodeDecodeError, ValueError):
                continue
        return list(texts)

    def extract_conversations(self, records: List[bytes]) -> List[Conversation]:
        """Extract deduplicated conversations from raw LevelDB records"""
        seen_sessions = set()
        conversations = []

        for rec in records:
            if len(rec) < 1000:
                continue

            # Extract session ID
            text = rec.decode("latin-1")
            session_match = re.search(
                r'sessionId[^a-f0-9]*\$?([a-f0-9-]{36})', text
            )
            if not session_match:
                continue

            session_id = session_match.group(1)
            
            # Dedup: skip if we've seen this exact record
            rec_hash = hash(rec[:1000])
            if session_id in self._session_hash:
                if rec_hash in self._session_hash[session_id]:
                    continue
            else:
                self._session_hash[session_id] = set()
            self._session_hash[session_id].add(rec_hash)

            # Extract bot info
            bot_match = re.search(r'bot_id[^"]*"(\d+)"', text)
            bot_id = bot_match.group(1) if bot_match else ""

            # Extract conversation text via UTF-16LE decoding
            texts = self.extract_utf16le_text(rec)

            # Filter to meaningful chat content
            chat_texts = [
                t for t in texts
                if any(ord(c) > 0x4E00 for c in t)  # has Chinese
                and len(t) > 15
                and not any(
                    kw in t for kw in [
                        "default-chat", "blockArtifact", "undefined",
                        "ArtifactMap", "stor", "mozilla", "chrome",
                    ]
                )
            ]

            if not chat_texts:
                continue

            # Build conversation object
            conv = Conversation(
                session_id=session_id,
                bot_id=bot_id,
                captured_at=int(datetime.now().timestamp()),
            )

            # Split content into user/assistant messages heuristically
            # (the IndexedDB format doesn't cleanly separate roles)
            content = "\n".join(chat_texts)
            
            # Try to detect user vs assistant segments
            # In Doubao, user messages often appear as the query
            # and assistant messages as the response
            segments = re.split(r"\n{2,}", content)
            for i, seg in enumerate(segments):
                seg = seg.strip()
                if not seg:
                    continue
                # Heuristic: even segments tend to be user, odd are assistant
                role = "user" if i % 2 == 0 else "assistant"
                conv.messages.append(ChatMessage(role=role, content=seg))

            conversations.append(conv)

        return conversations

    def read_all(self) -> List[Conversation]:
        """Read all conversations from the latest .log file"""
        log_files = self.find_log_files(self.indexeddb_dir)
        if not log_files:
            logger.warning("No LevelDB log files found in %s", self.indexeddb_dir)
            return []

        latest_log = log_files[0]
        logger.info("Reading: %s", latest_log)

        records = self.parse_log_file(latest_log)
        logger.info("Found %d raw records", len(records))

        conversations = self.extract_conversations(records)
        logger.info("Extracted %d conversations", len(conversations))

        return conversations


# ============================================================
# Quick test
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reader = LogReader()
    convs = reader.read_all()
    
    print("\n=== EXTRACTED CONVERSATIONS ===\n")
    for i, conv in enumerate(convs):
        print("--- Conversation {} ---".format(i + 1))
        print("Session: {}".format(conv.session_id))
        print("Bot: {}".format(conv.bot_id))
        print("Messages: {}".format(len(conv.messages)))
        for m in conv.messages[:6]:
            print("  [{}] {}".format(m.role, m.content[:150]))
        print()
