"""
Currency (CUR) -- Wallet System
=================================
Every wallet already exists. Every possible 128-character hex string
is a valid private key. CUR-128(private_key) = public key.

You don't "create" a wallet. You pick a private key (or generate one
randomly), and the corresponding public key is your address.

Private key: 128 hex chars (512 bits) -- YOU choose this, keep it SECRET
Public key:  128 hex chars (512 bits) -- derived via CUR-128, share freely
"""

import os
import json
import secrets
from cur128 import cur128
from config import MINED_FILE, TOTAL_SUPPLY


class Wallet:
    """
    A Currency wallet.

    Every possible private key is already a wallet.
    This class just holds the keys and lets you check your balance.
    """

    def __init__(self, private_key: str):
        """
        Initialize a wallet from a private key.

        Args:
            private_key: 128-character hex string (512 bits)
        """
        # Validate / normalize private key
        private_key = private_key.strip().lower()
        if len(private_key) != 128:
            raise ValueError(f"Private key must be exactly 128 hex characters (got {len(private_key)})")
        try:
            int(private_key, 16)
        except ValueError:
            raise ValueError("Private key must be valid hexadecimal")

        self.private_key = private_key
        self.public_key = cur128(private_key.encode('utf-8'))

    @staticmethod
    def generate_private_key() -> str:
        """Generate a random 128-character hex private key."""
        return secrets.token_hex(64)  # 64 bytes = 128 hex chars

    @classmethod
    def generate(cls):
        """Generate a wallet with a random private key."""
        return cls(cls.generate_private_key())

    def get_balance(self) -> int:
        """Count how many coins this wallet owns."""
        if not os.path.exists(MINED_FILE):
            return 0
        with open(MINED_FILE, 'r') as f:
            data = json.load(f)
        return sum(1 for entry in data['mined'] if entry['miner_address'] == self.public_key)

    def get_coins(self) -> list:
        """Get list of coin indices owned by this wallet."""
        if not os.path.exists(MINED_FILE):
            return []
        with open(MINED_FILE, 'r') as f:
            data = json.load(f)
        return [
            entry['coin_index']
            for entry in data['mined']
            if entry['miner_address'] == self.public_key
        ]

    def save(self, filepath: str):
        """Save private key to a file (for convenience -- keep this file safe)."""
        with open(filepath, 'w') as f:
            json.dump({
                "private_key": self.private_key,
                "public_key": self.public_key,
            }, f, indent=2)

    @classmethod
    def load(cls, filepath: str):
        """Load wallet from a saved key file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(data['private_key'])

    def __repr__(self):
        return f"Wallet(public_key={self.public_key[:20]}...)"


def display_wallet(wallet: Wallet):
    """Display wallet info."""
    bal = wallet.get_balance()
    print(f"")
    print(f"  PRIVATE KEY (secret -- never share this):")
    print(f"  {wallet.private_key}")
    print(f"")
    print(f"  PUBLIC KEY (your address -- share this):")
    print(f"  {wallet.public_key}")
    print(f"")
    print(f"  Balance: {bal:,} CUR")
    if bal > 0:
        print(f"  Supply:  {bal}/{TOTAL_SUPPLY:,} ({bal/TOTAL_SUPPLY*100:.6f}%)")
    print(f"")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python wallet.py generate                Generate a random wallet")
        print("  python wallet.py open <private_key>      Open wallet with private key")
        print("  python wallet.py balance <public_key>    Check any public key's balance")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'generate':
        w = Wallet.generate()
        print("\n  Wallet generated.\n")
        display_wallet(w)
        print("  SAVE YOUR PRIVATE KEY. There is no recovery. No reset. No support.")
        print("  If you lose it, your coins are gone forever.\n")

    elif cmd == 'open':
        if len(sys.argv) < 3:
            print("  Usage: python wallet.py open <128-char-hex-private-key>")
            sys.exit(1)
        try:
            w = Wallet(sys.argv[2])
            display_wallet(w)
        except ValueError as e:
            print(f"  Error: {e}")

    elif cmd == 'balance':
        if len(sys.argv) < 3:
            print("  Usage: python wallet.py balance <128-char-hex-public-key>")
            sys.exit(1)
        pub = sys.argv[2]
        if not os.path.exists(MINED_FILE):
            print("  Balance: 0 CUR")
            sys.exit(0)
        with open(MINED_FILE, 'r') as f:
            data = json.load(f)
        bal = sum(1 for e in data['mined'] if e['miner_address'] == pub)
        print(f"  Public Key: {pub}")
        print(f"  Balance:    {bal:,} CUR")
