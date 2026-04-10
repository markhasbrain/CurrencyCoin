"""
Currency Coin (CUR) -- Mining Engine
=====================================
The miner. Pure brute force. Partial prefix matching.

How mining works:
1. Generate random 128-char hex strings
2. Hash each one through CUR-128
3. Compare the FIRST N characters of the output against coin targets
4. N starts at 4 (easy) and increases as more coins are mined
5. If the prefix matches a target -> you found a coin
6. As supply shrinks, N grows, and mining gets exponentially harder
"""

import os
import sys
import json
import time
import secrets
import threading
from cur128 import cur128
from genesis import GenesisManager
from config import MINED_FILE


class Miner:
    """The Currency Coin miner -- guesses strings until it finds a coin."""

    def __init__(self, public_key: str):
        self.public_key = public_key
        self.genesis = GenesisManager()
        self.running = False
        self.total_guesses = 0
        self.coins_found = 0
        self.start_time = None
        self._lock = threading.Lock()

    def mine(self, threads: int = 1, max_coins: int = 0):
        """
        Start mining. Press Ctrl+C to stop.
        max_coins: stop after finding this many (0 = unlimited)
        """
        if not self.genesis.load():
            print("  Genesis not found. Downloading coin targets...")
            print("  This only happens once.\n")
            from genesis import download_genesis
            if not download_genesis():
                print("  Download failed. Generating locally instead (takes ~2 min)...")
                self.genesis.generate()
            self.genesis.load()

        stats = self.genesis.get_stats()
        if stats['remaining'] == 0:
            print("[MINER] All coins have been mined! None remaining.")
            return

        diff = stats['difficulty']
        pk_short = self.public_key[:16] + "..." + self.public_key[-16:]
        print(f"")
        print(f"  +------------------------------------------------+")
        print(f"  |          CURRENCY COIN (CUR) MINER             |")
        print(f"  +------------------------------------------------+")
        print(f"  |  Public Key:  {pk_short:>33s} |")
        print(f"  |  Threads:     {threads:>33d} |")
        print(f"  |  Remaining:   {stats['remaining']:>29,} CUR |")
        print(f"  |  Difficulty:  match {diff['match_chars']:>2}/128 hex chars          |")
        print(f"  |  Odds/guess:  {diff['effective_odds']:>33s} |")
        if max_coins > 0:
            print(f"  |  Stop after:  {max_coins:>29,} coin{'s' if max_coins > 1 else ' '} |")
        print(f"  +------------------------------------------------+")
        print(f"")
        print(f"  Mining... (Ctrl+C to stop)")
        print(f"")

        self.running = True
        self.start_time = time.time()
        self.total_guesses = 0
        self.coins_found = 0
        self._max_coins = max_coins

        # Start mining threads
        workers = []
        for t in range(threads):
            worker = threading.Thread(target=self._mine_worker, args=(t,), daemon=True)
            worker.start()
            workers.append(worker)

        # Status display thread
        status_thread = threading.Thread(target=self._status_display, daemon=True)
        status_thread.start()

        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print(f"\n\n  [MINER] Stopping...")
            self.running = False

        for w in workers:
            w.join(timeout=2)

        elapsed = time.time() - self.start_time
        print(f"\n  ======================================")
        print(f"  Mining session complete.")
        print(f"  Total guesses:  {self.total_guesses:,}")
        print(f"  Coins found:    {self.coins_found}")
        print(f"  Time:           {elapsed:.1f}s")
        if elapsed > 0:
            print(f"  Hash rate:      {self.total_guesses / elapsed:,.0f} CUR-128/sec")
        print(f"  ======================================\n")

    def _mine_worker(self, thread_id: int):
        """Single mining thread -- generates random strings and checks."""
        while self.running:
            # Generate a random 64-byte input
            guess = secrets.token_hex(64)  # 128 hex chars

            # Hash through CUR-128
            result = cur128(guess.encode('utf-8'))

            with self._lock:
                self.total_guesses += 1

            # Check if prefix matches any coin target
            coin_index = self.genesis.check_hash(result)

            if coin_index >= 0:
                self._coin_found(coin_index, guess, result)

    def _coin_found(self, coin_index: int, guess: str, hash_result: str):
        """Handle a found coin."""
        with self._lock:
            self.coins_found += 1

            entry = {
                "coin_index": coin_index,
                "miner_address": self.public_key,
                "proof": guess,
                "hash": hash_result,
                "timestamp": time.time(),
                "guess_number": self.total_guesses,
            }

            if os.path.exists(MINED_FILE):
                with open(MINED_FILE, 'r') as f:
                    data = json.load(f)
            else:
                data = {"mined": [], "total_mined": 0}

            data['mined'].append(entry)
            data['total_mined'] = len(data['mined'])

            with open(MINED_FILE, 'w') as f:
                json.dump(data, f, indent=2)

            pk_short = self.public_key[:16] + "..." + self.public_key[-16:]
            print(f"\n")
            print(f"  +------------------------------------------------+")
            print(f"  |              * COIN FOUND! *                   |")
            print(f"  +------------------------------------------------+")
            print(f"  |  Coin #:     {coin_index:>34,} |")
            print(f"  |  Guess #:    {self.total_guesses:>34,} |")
            print(f"  |  Sent to:    {pk_short:>34s} |")
            print(f"  |  Total found: {self.coins_found:>33,} |")
            print(f"  +------------------------------------------------+")
            print(f"")

            # Stop if we hit max coins
            if self._max_coins > 0 and self.coins_found >= self._max_coins:
                self.running = False

    def _status_display(self):
        """Periodically display mining status."""
        while self.running:
            time.sleep(3)
            if not self.running:
                break
            elapsed = time.time() - self.start_time
            rate = self.total_guesses / elapsed if elapsed > 0 else 0

            sys.stdout.write(
                f"\r  [MINING] Guesses: {self.total_guesses:>12,} | "
                f"Rate: {rate:>8,.0f} H/s | "
                f"Found: {self.coins_found} | "
                f"Time: {elapsed:.0f}s     "
            )
            sys.stdout.flush()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python miner.py <public_key> [threads] [max_coins]")
        sys.exit(0)

    public_key = sys.argv[1]
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    max_coins = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    if len(public_key) != 128:
        print(f"  Public key must be 128 hex characters (got {len(public_key)})")
        sys.exit(1)

    miner = Miner(public_key)
    miner.mine(threads=threads, max_coins=max_coins)
