"""
Currency Coin (CUR) -- Ledger System
======================================
Tracks all mined coins, ownership, and transfers.

Balances are computed from the ledger -- nobody can fake a balance.
You either mined it, or someone sent it to you. That's it.
"""

import os
import json
import time
from cur128 import cur128
from config import MINED_FILE, TOTAL_SUPPLY, TRADING_UNLOCK_PRICE


class Ledger:
    """The Currency Coin ledger -- immutable record of all coin activity."""

    def _load(self) -> dict:
        if not os.path.exists(MINED_FILE):
            return {"mined": [], "total_mined": 0, "transfers": []}
        with open(MINED_FILE, 'r') as f:
            data = json.load(f)
        if 'transfers' not in data:
            data['transfers'] = []
        return data

    def _save(self, data: dict):
        with open(MINED_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def get_balance(self, public_key: str) -> int:
        """Get balance for a public key."""
        balances = self.get_all_balances()
        return balances.get(public_key, 0)

    def send(self, sender_private_key: str, recipient_public_key: str, amount: int) -> bool:
        """
        Send CUR from one wallet to another.

        Requires the SENDER's private key to prove ownership.
        The recipient is identified by their public key.
        """
        # Derive sender's public key from their private key
        sender_public_key = cur128(sender_private_key.encode('utf-8'))

        # Verify sender has enough balance
        balance = self.get_balance(sender_public_key)
        if balance < amount:
            print(f"  Insufficient balance. You have {balance:,} CUR, tried to send {amount:,}.")
            return False

        if amount <= 0:
            print(f"  Amount must be greater than 0.")
            return False

        if recipient_public_key == sender_public_key:
            print(f"  Cannot send to yourself.")
            return False

        # Validate recipient public key format
        if len(recipient_public_key) != 128:
            print(f"  Recipient public key must be 128 hex characters.")
            return False

        # Record the transfer
        data = self._load()
        transfer_entry = {
            "from": sender_public_key,
            "to": recipient_public_key,
            "amount": amount,
            "timestamp": time.time(),
            "type": "transfer",
        }
        data['transfers'].append(transfer_entry)
        self._save(data)

        sender_short = sender_public_key[:16] + "..." + sender_public_key[-16:]
        recip_short = recipient_public_key[:16] + "..." + recipient_public_key[-16:]
        print(f"")
        print(f"  Sent {amount:,} CUR")
        print(f"  From: {sender_short}")
        print(f"  To:   {recip_short}")
        print(f"")
        return True

    def get_all_balances(self) -> dict:
        """Get balance for every address."""
        data = self._load()
        balances = {}

        # Count mined coins per address
        for entry in data['mined']:
            addr = entry['miner_address']
            balances[addr] = balances.get(addr, 0) + 1

        # Apply transfers
        for transfer in data.get('transfers', []):
            from_addr = transfer['from']
            to_addr = transfer['to']
            amount = transfer.get('amount', 1)
            balances[from_addr] = balances.get(from_addr, 0) - amount
            balances[to_addr] = balances.get(to_addr, 0) + amount

        return {k: v for k, v in balances.items() if v > 0}

    def get_supply_stats(self) -> dict:
        """Get supply statistics."""
        data = self._load()
        mined = len(data['mined'])
        return {
            "total_supply": TOTAL_SUPPLY,
            "mined": mined,
            "remaining": TOTAL_SUPPLY - mined,
            "percent_mined": (mined / TOTAL_SUPPLY * 100) if TOTAL_SUPPLY > 0 else 0,
            "trading_locked": False,
            "unlock_price": TRADING_UNLOCK_PRICE,
            "total_transfers": len(data.get('transfers', [])),
        }

    def get_recent_activity(self, limit: int = 20) -> list:
        """Get recent mining and transfer activity."""
        data = self._load()
        all_activity = data['mined'][-limit:] + data.get('transfers', [])[-limit:]
        all_activity.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return all_activity[:limit]
