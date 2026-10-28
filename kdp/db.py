"""SQLite: cache stron, frazy, analizy SERP i produktów."""
import json
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, body TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS keywords (
    market TEXT, keyword TEXT, seed TEXT, hits INTEGER, best_pos INTEGER,
    first_seen REAL, last_seen REAL, PRIMARY KEY (market, keyword));
CREATE TABLE IF NOT EXISTS serp (
    market TEXT, keyword TEXT, ts REAL, total_results INTEGER, data TEXT,
    PRIMARY KEY (market, keyword, ts));
CREATE TABLE IF NOT EXISTS products (
    market TEXT, asin TEXT, ts REAL, data TEXT, PRIMARY KEY (market, asin));
CREATE TABLE IF NOT EXISTS niches (
    market TEXT, keyword TEXT, ts REAL, score REAL, data TEXT,
    PRIMARY KEY (market, keyword, ts));
"""


class DB:
    def __init__(self, path: Path):
        self.c = sqlite3.connect(path)
        self.c.executescript(SCHEMA)

    # cache
    def cache_get(self, key, ttl_h):
        row = self.c.execute("SELECT body, ts FROM cache WHERE key=?", (key,)).fetchone()
        if row and time.time() - row[1] < ttl_h * 3600:
            return row[0]
        return None

    def cache_put(self, key, body):
        self.c.execute("REPLACE INTO cache VALUES (?,?,?)", (key, body, time.time()))
        self.c.commit()

    # keywords
    def upsert_keyword(self, market, kw, seed, hits, best_pos):
        now = time.time()
        self.c.execute("""
            INSERT INTO keywords VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(market, keyword) DO UPDATE SET
              hits=MAX(hits, excluded.hits), best_pos=MIN(best_pos, excluded.best_pos),
              last_seen=excluded.last_seen""",
            (market, kw, seed, hits, best_pos, now, now))

    def keywords(self, market, limit=None, seed=None):
        q = "SELECT keyword, seed, hits, best_pos FROM keywords WHERE market=?"
        args = [market]
        if seed:
            q += " AND seed=?"
            args.append(seed)
        q += " ORDER BY hits DESC, best_pos ASC, length(keyword) DESC"
        if limit:
            q += f" LIMIT {int(limit)}"
        return self.c.execute(q, args).fetchall()

    # serp / products / niches
    def save_serp(self, market, kw, total, items):
        self.c.execute("INSERT OR REPLACE INTO serp VALUES (?,?,?,?,?)",
                       (market, kw, time.time(), total, json.dumps(items)))

    def get_product(self, market, asin, ttl_h):
        row = self.c.execute("SELECT data, ts FROM products WHERE market=? AND asin=?",
                             (market, asin)).fetchone()
        if row and time.time() - row[1] < ttl_h * 3600:
            return json.loads(row[0])
        return None

    def save_product(self, market, asin, data):
        self.c.execute("REPLACE INTO products VALUES (?,?,?,?)",
                       (market, asin, time.time(), json.dumps(data)))

    def save_niche(self, market, kw, score, data):
        self.c.execute("INSERT OR REPLACE INTO niches VALUES (?,?,?,?,?)",
                       (market, kw, time.time(), score, json.dumps(data)))

    def latest_niches(self, market):
        rows = self.c.execute("""
            SELECT n.keyword, n.score, n.data FROM niches n
            JOIN (SELECT keyword, MAX(ts) ts FROM niches WHERE market=? GROUP BY keyword) l
              ON n.keyword=l.keyword AND n.ts=l.ts
            WHERE n.market=? ORDER BY n.score DESC""", (market, market)).fetchall()
        return [dict(json.loads(d), keyword=k, score=s) for k, s, d in rows]

    def history(self, market, kw):
        return self.c.execute("SELECT ts, score FROM niches WHERE market=? AND keyword=? ORDER BY ts",
                              (market, kw)).fetchall()

    def commit(self):
        self.c.commit()
