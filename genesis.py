"""
Currency Coin (CUR) -- Genesis System
=======================================
Generates all 22,516,162 coin target hashes at genesis.

Mining works on PARTIAL MATCHING with increasing difficulty:
- Early on, miners only need to match the first 4 hex chars of a target
- As more coins get mined, they need to match more characters
- The last coin requires matching all 128 characters

This means early coins are EASY to find, and it gets progressively
harder as the supply shrinks.
"""

import os
import sys
import json
import time
import struct
import hashlib
import urllib.request
from config import (
    TOTAL_SUPPLY, GENESIS_MASTER_SEED, DATA_DIR,
    GENESIS_FILE, MINED_FILE
)

GENESIS_URL = "https://github.com/markhasbrain/CurrencyCoin/releases/download/v1.0/genesis.bin"


def download_genesis() -> bool:
    """Download the official genesis.bin from GitHub releases."""
    os.makedirs(DATA_DIR, exist_ok=True)

    if os.path.exists(GENESIS_FILE):
        return True

    print(f"[GENESIS] Downloading genesis.bin from GitHub...")
    print(f"[GENESIS] URL: {GENESIS_URL}")
    print(f"[GENESIS] This is ~611 MB, may take a few minutes.\n")

    try:
        def _progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                pct = downloaded / total_size * 100
                mb = downloaded / 1024 / 1024
                total_mb = total_size / 1024 / 1024
                sys.stdout.write(f"\r[GENESIS] {mb:.0f} / {total_mb:.0f} MB ({pct:.1f}%)")
                sys.stdout.flush()

        urllib.request.urlretrieve(GENESIS_URL, GENESIS_FILE, _progress)
        print(f"\n[GENESIS] Download complete!")

        # Init mined.json if needed
        if not os.path.exists(MINED_FILE):
            with open(MINED_FILE, 'w') as f:
                json.dump({"mined": [], "total_mined": 0}, f)

        return True
    except Exception as e:
        print(f"\n[GENESIS] Download failed: {e}")
        return False


def _generate_coin_target(index: int) -> bytes:
    """
    Generate a coin's target hash deterministically.
    Returns 64 bytes (512 bits = 128 hex chars).
    """
    key = GENESIS_MASTER_SEED.encode()
    msg = f"COIN:{index}".encode()
    h = hashlib.new('sha512', key + msg).digest()
    for _ in range(16):
        h = hashlib.sha512(h + key + struct.pack('>Q', index)).digest()
    return h


def get_difficulty(mined_count: int) -> int:
    """
    Calculate current mining difficulty based on how many coins have been mined.

    Returns the number of hex characters that must match a target's prefix.
    This is THE formula that makes early coins easy and late coins brutal.

    With 10M total supply and ~350 H/s (18 threads):

    First 1M (10%):   match 4 chars -> ~150 coins/sec -> ~1.8 min for 1M
    1M-2M (20%):      match 5 chars -> ~9 coins/sec   -> ~30 min
    2M-3M (30%):      match 6 chars -> ~0.5 coins/sec -> ~8 hours
    3M-4M (40%):      match 7 chars -> rare finds     -> ~5 days
    4M-5M (50%):      match 8 chars -> very rare      -> ~3 months
    5M-7M (50-70%):   match 9 chars -> grind          -> years
    7M-9M (70-90%):   match 10-11   -> brutal
    9M-10M (90-100%): match 12+     -> near impossible
    Last coin:        match 128     -> CUR-5B legendary

    ASIC resistance: CUR-128 is memory-hard and sequential (100 steps).
    Throwing more hardware at it gives linear gains at best.
    A $10,000 ASIC mines maybe 2-3x faster than a laptop, not 1000x.
    """
    if mined_count >= TOTAL_SUPPLY - 1:
        return 128  # last coin = full match

    ratio = mined_count / TOTAL_SUPPLY

    # Piecewise linear with exponential tail
    # Each million coins bumps difficulty by ~1 hex char
    if ratio < 0.10:    # 0 - 1M
        return 4
    elif ratio < 0.20:  # 1M - 2M
        return 5
    elif ratio < 0.30:  # 2M - 3M
        return 6
    elif ratio < 0.40:  # 3M - 4M
        return 7
    elif ratio < 0.50:  # 4M - 5M
        return 8
    elif ratio < 0.60:  # 5M - 6M
        return 9
    elif ratio < 0.70:  # 6M - 7M
        return 10
    elif ratio < 0.80:  # 7M - 8M
        return 11
    elif ratio < 0.90:  # 8M - 9M
        return 12
    elif ratio < 0.95:  # 9M - 9.5M
        return 14
    elif ratio < 0.99:  # 9.5M - 9.9M
        return 16
    else:               # last 100K
        return 20


def get_difficulty_info(mined_count: int) -> dict:
    """Get detailed difficulty info for display."""
    diff = get_difficulty(mined_count)
    # Probability of a random guess matching one target
    # Each hex char = 16 possibilities, so matching N chars = 1/16^N
    match_odds = 16 ** diff
    # But there are (TOTAL_SUPPLY - mined_count) targets to match against
    remaining = max(1, TOTAL_SUPPLY - mined_count)
    # Effective odds of ANY match per guess
    effective_odds = match_odds / remaining

    return {
        "match_chars": diff,
        "match_of_total": f"{diff}/128",
        "odds_per_target": f"1 in {match_odds:,}",
        "targets_available": remaining,
        "effective_odds": f"1 in {effective_odds:,.0f}",
        "mined": mined_count,
        "percent_mined": mined_count / TOTAL_SUPPLY * 100,
    }


class GenesisManager:
    """Manages the genesis coin set -- generation, storage, and lookup."""

    def __init__(self):
        self._prefix_index = {}  # prefix -> [(coin_index, full_hash), ...]
        self._loaded = False
        self._mined_set = set()

    def generate(self, progress_callback=None):
        """Generate all 22,516,162 coin target hashes."""
        print(f"[GENESIS] Generating {TOTAL_SUPPLY:,} coin targets...")
        print(f"[GENESIS] Master seed: {GENESIS_MASTER_SEED}")
        print(f"[GENESIS] This will take a while...\n")

        os.makedirs(DATA_DIR, exist_ok=True)

        start_time = time.time()
        batch_size = 1000

        with open(GENESIS_FILE, 'wb') as f:
            f.write(b'CUR1')  # magic bytes
            f.write(struct.pack('>I', TOTAL_SUPPLY))

            for i in range(TOTAL_SUPPLY):
                target_hash = _generate_coin_target(i)
                f.write(target_hash)

                if i % batch_size == 0 and i > 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed
                    eta = (TOTAL_SUPPLY - i) / rate if rate > 0 else 0
                    pct = i / TOTAL_SUPPLY * 100

                    if progress_callback:
                        progress_callback(i, TOTAL_SUPPLY, rate, eta)
                    else:
                        sys.stdout.write(
                            f"\r[GENESIS] {i:>12,} / {TOTAL_SUPPLY:,} "
                            f"({pct:5.2f}%) | {rate:,.0f} coins/sec | "
                            f"ETA: {eta/60:,.1f} min"
                        )
                        sys.stdout.flush()

        # Initialize mined coins tracker
        if not os.path.exists(MINED_FILE):
            with open(MINED_FILE, 'w') as f:
                json.dump({"mined": [], "total_mined": 0}, f)

        elapsed = time.time() - start_time
        genesis_size = os.path.getsize(GENESIS_FILE)
        print(f"\n\n[GENESIS] Complete!")
        print(f"[GENESIS] Generated {TOTAL_SUPPLY:,} coin targets in {elapsed:.1f}s")
        print(f"[GENESIS] Genesis file: {GENESIS_FILE} ({genesis_size / 1024 / 1024:.1f} MB)")
        return True

    def load(self, match_chars: int = 4):
        """
        Load genesis and build a prefix index for the current difficulty.

        The prefix index maps the first N hex chars of each target to its
        coin index, allowing O(1) lookup during mining.
        """
        if not os.path.exists(GENESIS_FILE):
            return False

        self._mined_set = self._load_mined_set()
        mined_count = len(self._mined_set)
        match_chars = get_difficulty(mined_count)

        print(f"[GENESIS] Loading coin targets...")
        print(f"[GENESIS] Current difficulty: match {match_chars}/128 hex chars")

        self._prefix_index = {}
        start = time.time()

        with open(GENESIS_FILE, 'rb') as f:
            f.seek(8)  # skip header
            for i in range(TOTAL_SUPPLY):
                target = f.read(64)
                if not target or len(target) < 64:
                    break

                if i in self._mined_set:
                    continue  # skip mined coins

                # Index by prefix
                prefix = target.hex()[:match_chars]
                if prefix not in self._prefix_index:
                    self._prefix_index[prefix] = []
                self._prefix_index[prefix].append((i, target))

        self._loaded = True
        self._current_difficulty = match_chars
        elapsed = time.time() - start

        remaining = TOTAL_SUPPLY - mined_count
        print(f"[GENESIS] Loaded {remaining:,} unmined coin targets in {elapsed:.1f}s")
        print(f"[GENESIS] Prefix index: {len(self._prefix_index):,} unique prefixes")
        return True

    def check_hash(self, hash_hex: str) -> int:
        """
        Check if a CUR-128 hash output matches any unmined coin target.

        Only compares the first N hex characters (based on current difficulty).
        Returns coin index if match, -1 otherwise.
        """
        prefix = hash_hex[:self._current_difficulty]

        if prefix not in self._prefix_index:
            return -1

        # Prefix matched! Find the first unmined coin with this prefix
        entries = self._prefix_index[prefix]
        if entries:
            coin_index, full_hash = entries[0]
            # Remove from index so it can't be found twice
            entries.pop(0)
            if not entries:
                del self._prefix_index[prefix]
            return coin_index

        return -1

    def _load_mined_set(self) -> set:
        if not os.path.exists(MINED_FILE):
            return set()
        with open(MINED_FILE, 'r') as f:
            data = json.load(f)
        return set(entry['coin_index'] for entry in data['mined'])

    def get_coin_target(self, index: int) -> bytes:
        with open(GENESIS_FILE, 'rb') as f:
            f.seek(8 + index * 64)
            return f.read(64)

    def get_stats(self) -> dict:
        mined_set = self._load_mined_set()
        mined_count = len(mined_set)
        diff_info = get_difficulty_info(mined_count)
        return {
            "total_supply": TOTAL_SUPPLY,
            "total_mined": mined_count,
            "remaining": TOTAL_SUPPLY - mined_count,
            "percent_mined": mined_count / TOTAL_SUPPLY * 100,
            "difficulty": diff_info,
        }


if __name__ == '__main__':
    gm = GenesisManager()

    if '--generate' in sys.argv:
        gm.generate()
    elif '--stats' in sys.argv:
        stats = gm.get_stats()
        print(f"Total Supply:    {stats['total_supply']:,}")
        print(f"Total Mined:     {stats['total_mined']:,}")
        print(f"Remaining:       {stats['remaining']:,}")
        print(f"Percent Mined:   {stats['percent_mined']:.4f}%")
        d = stats['difficulty']
        print(f"Difficulty:      Match {d['match_chars']}/128 chars")
        print(f"Odds per guess:  {d['effective_odds']}")
    elif '--difficulty' in sys.argv:
        # Show difficulty curve
        print(f"{'Mined %':>10} | {'Coins Mined':>15} | {'Match':>6} | {'Odds per guess':>20}")
        print(f"{'-'*10} | {'-'*15} | {'-'*6} | {'-'*20}")
        for pct in [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95, 99, 100]:
            mined = int(TOTAL_SUPPLY * pct / 100)
            if mined >= TOTAL_SUPPLY:
                mined = TOTAL_SUPPLY - 1
            info = get_difficulty_info(mined)
            print(f"{pct:>9}% | {mined:>15,} | {info['match_chars']:>4}/128 | {info['effective_odds']:>20}")
    else:
        print("Usage:")
        print("  python genesis.py --generate    Generate all coin targets")
        print("  python genesis.py --stats       Show genesis stats")
        print("  python genesis.py --difficulty   Show difficulty curve")
