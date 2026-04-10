"""
Currency (CRNY) -- Main CLI
============================
The one command to rule them all.

Usage:
  python currency.py genesis                    Generate all 22,516,162 coin targets
  python currency.py wallet generate            Generate a random wallet (private + public key)
  python currency.py wallet open <private_key>  Open wallet with your private key
  python currency.py wallet balance <pub_key>   Check any public key's balance
  python currency.py mine <public_key> [t]      Start mining (t = threads, default 1)
  python currency.py status                     Show network status
  python currency.py hash <input>               Hash something with CUR-128
  python currency.py verify <coin#>             Verify a coin's target hash
"""

import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import TOTAL_SUPPLY, TICKER, NAME, TRADING_UNLOCK_PRICE
from cur128 import cur128


BANNER = f"""
   ______
  / ____/_  ____________  ____  _______  __
 / /   / / / / ___/ ___/ / _ \\/ __ \\/ ___/ / / /
/ /___/ /_/ / /  / /    /  __/ / / / /__/ /_/ /
\\____/\\__,_/_/  /_/     \\___/_/ /_/\\___/\\__, /
                                        /____/

  {NAME} ({TICKER}) -- {TOTAL_SUPPLY:,} coins, all mineable
  Algorithm: CUR-128 (100-step, 512-bit, quantum-resistant)
  Phase 1: Mining only | Phase 2: Trading at ${TRADING_UNLOCK_PRICE:.0f}/coin
"""


def cmd_genesis():
    """Generate all coin targets."""
    from genesis import GenesisManager
    gm = GenesisManager()
    gm.generate()


def cmd_wallet(args):
    """Wallet operations."""
    from wallet import Wallet, display_wallet

    if not args:
        print("  wallet generate              Generate a random wallet")
        print("  wallet open <private_key>    Open wallet with your private key")
        print("  wallet balance <public_key>  Check any public key's balance")
        return

    subcmd = args[0]

    if subcmd == 'generate':
        w = Wallet.generate()
        print("\n  New wallet generated.\n")
        display_wallet(w)
        print("  SAVE YOUR PRIVATE KEY. There is no recovery. No reset. No support.")
        print("  If you lose it, your coins are gone forever.\n")

    elif subcmd == 'open':
        if len(args) < 2:
            print("  Usage: python currency.py wallet open <128-char-hex-private-key>")
            return
        try:
            w = Wallet(args[1])
            display_wallet(w)
        except ValueError as e:
            print(f"  Error: {e}")

    elif subcmd == 'balance':
        if len(args) < 2:
            print("  Usage: python currency.py wallet balance <128-char-hex-public-key>")
            return
        pub = args[1]
        import json
        from config import MINED_FILE
        if not os.path.exists(MINED_FILE):
            bal = 0
        else:
            with open(MINED_FILE, 'r') as f:
                data = json.load(f)
            bal = sum(1 for e in data['mined'] if e['miner_address'] == pub)
        print(f"\n  Public Key: {pub}")
        print(f"  Balance:    {bal:,} {TICKER}\n")

    else:
        print(f"  Unknown wallet command: {subcmd}")


def cmd_mine(args):
    """Start mining."""
    from miner import Miner

    if not args:
        print("  Usage: python currency.py mine <public_key> [threads] [max_coins]")
        print("")
        print("  public_key: your 128-char hex public key (run 'wallet generate' first)")
        print("  threads:    number of mining threads (default: 1)")
        print("  max_coins:  stop after finding this many (default: unlimited)")
        return

    public_key = args[0]
    threads = int(args[1]) if len(args) > 1 else 1
    max_coins = int(args[2]) if len(args) > 2 else 0

    if len(public_key) != 128:
        print(f"  Error: Public key must be 128 hex characters (got {len(public_key)})")
        return

    miner = Miner(public_key)
    miner.mine(threads=threads, max_coins=max_coins)


def cmd_send(args):
    """Send CUR to someone."""
    from ledger import Ledger

    if len(args) < 3:
        print("  Usage: python currency.py send <your_private_key> <recipient_public_key> <amount>")
        print("")
        print("  your_private_key:      your 128-char hex private key (proves you own the coins)")
        print("  recipient_public_key:  their 128-char hex public key (where coins go)")
        print("  amount:                number of CUR to send")
        return

    private_key = args[0]
    recipient = args[1]
    amount = int(args[2])

    if len(private_key) != 128:
        print(f"  Error: Private key must be 128 hex characters (got {len(private_key)})")
        return

    if len(recipient) != 128:
        print(f"  Error: Recipient public key must be 128 hex characters (got {len(recipient)})")
        return

    ledger = Ledger()
    ledger.send(private_key, recipient, amount)


def cmd_status():
    """Show network status."""
    from ledger import Ledger
    from genesis import get_difficulty_info

    ledger = Ledger()
    stats = ledger.get_supply_stats()
    diff = get_difficulty_info(stats['mined'])

    print(f"\n  =============================================")
    print(f"  {NAME} ({TICKER}) -- Network Status")
    print(f"  =============================================")
    print(f"  Total Supply:    {stats['total_supply']:>15,} {TICKER}")
    print(f"  Mined:           {stats['mined']:>15,} {TICKER}")
    print(f"  Remaining:       {stats['remaining']:>15,} {TICKER}")
    print(f"  Percent Mined:   {stats['percent_mined']:>14.4f}%")
    print(f"  ---------------------------------------------")
    print(f"  Difficulty:      match {diff['match_chars']:>2}/128 hex chars")
    print(f"  Odds per guess:  {diff['effective_odds']:>25s}")
    print(f"  ---------------------------------------------")
    print(f"  Phase:           {'1 -- MINING ONLY' if stats['trading_locked'] else '2 -- OPEN TRADING'}")
    print(f"  Trading:         {'LOCKED' if stats['trading_locked'] else 'UNLOCKED'}")
    print(f"  Unlock Price:    ${stats['unlock_price']:>13,.2f}")
    print(f"  Transfers:       {stats['total_transfers']:>15,}")
    print(f"  =============================================")

    # Show balances
    balances = ledger.get_all_balances()
    if balances:
        print(f"\n  Top Holders:")
        sorted_bal = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
        for addr, bal in sorted_bal:
            short = addr[:16] + "..." + addr[-16:]
            print(f"    {short} | {bal:>10,} {TICKER}")

    # Show recent activity
    recent = ledger.get_recent_activity(5)
    if recent:
        print(f"\n  Recent Activity:")
        for entry in recent:
            if entry.get('type') == 'transfer':
                print(f"    TRANSFER | Coin #{entry['coin_index']} | "
                      f"{entry['from'][:15]}... -> {entry['to'][:15]}...")
            else:
                short = entry['miner_address'][:20] + "..."
                print(f"    MINED    | Coin #{entry['coin_index']} | by {short}")


def cmd_difficulty():
    """Show the full difficulty curve."""
    from genesis import get_difficulty_info
    print(f"\n  Currency Coin (CUR) -- Difficulty Curve")
    print(f"  =============================================")
    print(f"  {'Mined %':>10} | {'Coins Mined':>15} | {'Match':>8} | {'Odds per guess':>20}")
    print(f"  {'-'*10} | {'-'*15} | {'-'*8} | {'-'*20}")
    for pct in [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95, 99, 100]:
        mined = int(TOTAL_SUPPLY * pct / 100)
        if mined >= TOTAL_SUPPLY:
            mined = TOTAL_SUPPLY - 1
        info = get_difficulty_info(mined)
        print(f"  {pct:>9}% | {mined:>15,} | {info['match_chars']:>4}/128 | {info['effective_odds']:>20}")
    print()


def cmd_hash(args):
    """Hash an input with CUR-128."""
    if not args:
        print("  Usage: python currency.py hash <input>")
        return

    input_str = ' '.join(args)
    result = cur128(input_str.encode('utf-8'))
    print(f"\n  Input:    {input_str}")
    print(f"  CUR-128:  {result}")
    print(f"  Length:   {len(result)} chars ({len(result)*4} bits)")

    # Show avalanche with slight modification
    if input_str:
        modified = input_str[:-1] + chr(ord(input_str[-1]) ^ 1)
        result2 = cur128(modified.encode('utf-8'))
        diff = bin(int(result, 16) ^ int(result2, 16)).count('1')
        print(f"\n  Avalanche test vs '{modified}':")
        print(f"  CUR-128:  {result2}")
        print(f"  Bits changed: {diff}/512 ({diff/512*100:.1f}%)")


def cmd_verify(args):
    """Verify a coin's target hash."""
    if not args:
        print("  Usage: python currency.py verify <coin_index>")
        return

    from genesis import GenesisManager

    index = int(args[0])
    if index < 0 or index >= TOTAL_SUPPLY:
        print(f"  Coin index must be between 0 and {TOTAL_SUPPLY - 1:,}")
        return

    gm = GenesisManager()
    if not gm.load():
        print("  Genesis not generated yet. Run: python currency.py genesis")
        return

    target = gm.get_coin_target(index)
    mined_set = gm._load_mined_set()
    print(f"\n  Coin #{index:,}")
    print(f"  Target hash: {target.hex()}")
    print(f"  Status: {'MINED' if index in mined_set else 'UNMINED -- waiting for a miner'}")


def cmd_help():
    """Show help."""
    print(f"""
  Commands:
  ---------------------------------------------------------
  genesis                    Generate all {TOTAL_SUPPLY:,} coin targets
  wallet generate            Generate a random wallet
  wallet open <private_key>  Open wallet with private key
  wallet balance <pub_key>   Check any public key's balance
  mine <pub_key> [t] [max]   Mine coins (t=threads, max=stop after N)
  send <priv> <pub> <amt>    Send CUR to someone's public key
  status                     Show network/supply status
  difficulty                 Show the full difficulty curve
  hash <input>               Hash any input with CUR-128
  verify <coin#>             Check a specific coin's target
  help                       Show this help
  ---------------------------------------------------------

  Quick Start:
    1. python currency.py genesis
    2. python currency.py wallet generate
    3. python currency.py mine <your_public_key> 4
""")


def main():
    print(BANNER)

    if len(sys.argv) < 2:
        cmd_help()
        return

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    commands = {
        'genesis': lambda: cmd_genesis(),
        'wallet': lambda: cmd_wallet(args),
        'mine': lambda: cmd_mine(args),
        'send': lambda: cmd_send(args),
        'status': lambda: cmd_status(),
        'difficulty': lambda: cmd_difficulty(),
        'hash': lambda: cmd_hash(args),
        'verify': lambda: cmd_verify(args),
        'help': lambda: cmd_help(),
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"  Unknown command: {cmd}")
        cmd_help()


if __name__ == '__main__':
    main()
