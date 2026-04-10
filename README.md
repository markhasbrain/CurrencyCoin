# Currency Coin (CUR)

10,000,000 coins. All mineable. No pre-mine, no ICO, no dev allocation.

Secured by **CUR-128** — a custom 100-step, 512-bit, quantum-resistant hash algorithm built from scratch.

## How it works

- Every coin has a hidden target hash generated at genesis
- To mine, you guess random 128-character strings, hash them through CUR-128, and check if the output matches any target
- Early coins are easy to find — later coins get exponentially harder
- The last coin requires matching all 128 hex characters (effectively impossible)
- Your wallet is just a private key (128 hex chars) — CUR-128(private_key) = your public key
- Every possible private key is already a wallet. You don't "create" one, you just pick one

## Difficulty curve

| Coins mined | Match required | Difficulty |
|---|---|---|
| 0 - 1M | 4/128 hex chars | Easy |
| 1M - 2M | 5/128 | Moderate |
| 2M - 3M | 6/128 | Hard |
| 3M - 4M | 7/128 | Serious |
| 4M - 5M | 8/128 | Intense |
| 5M - 6M | 9/128 | Brutal |
| 6M - 7M | 10/128 | Savage |
| 7M - 8M | 11/128 | Extreme |
| 8M - 9M | 12/128 | Insane |
| 9M - 10M | 14-128/128 | Impossible |
| Last coin | 128/128 | CUR-5B |

## Quick start (Windows)

### Requirements

- Python 3.10+ — https://www.python.org/downloads/
- Node.js 20+ — https://nodejs.org/ (only needed for the live dashboard)
- Git — https://git-scm.com/downloads

### Setup

Open Windows Terminal (or Command Prompt) and run these commands in order:

```
git clone https://github.com/MarkFHII/CurrencyCoin.git
cd CurrencyCoin
```

### 1. Generate genesis (creates all 10M coin targets)

```
python currency.py genesis
```

This takes about 2-3 minutes. It generates a 640MB `genesis.bin` file containing all 10,000,000 coin target hashes.

### 2. Generate a wallet

```
python currency.py wallet generate
```

This gives you a **private key** (keep secret) and a **public key** (your address). Save both.

### 3. Start mining

Replace `<your_public_key>` with the public key from step 2. The number at the end is how many CPU threads to use.

```
python currency.py mine <your_public_key> 4
```

### 4. Check your balance

```
python currency.py wallet open <your_private_key>
```

### 5. Send CUR to someone

```
python currency.py send <your_private_key> <their_public_key> <amount>
```

### 6. Live dashboard (optional)

```
cd dashboard
npm install
npm run dev
```

Open http://localhost:2000 in your browser. Shows live stats, leaderboard, and mining activity in real-time.

## All commands

```
python currency.py genesis                    Generate all 10,000,000 coin targets
python currency.py wallet generate            Generate a random wallet
python currency.py wallet open <private_key>  Open wallet with private key
python currency.py wallet balance <pub_key>   Check any public key's balance
python currency.py mine <pub_key> [t] [max]   Mine coins (t=threads, max=stop after N)
python currency.py send <priv> <pub> <amt>    Send CUR to someone's public key
python currency.py status                     Show network status
python currency.py difficulty                 Show the full difficulty curve
python currency.py hash <input>               Hash any input with CUR-128
python currency.py verify <coin#>             Check a specific coin's target
```

## CUR-128 algorithm

100 steps across 10 rounds. 512-bit output. Public algorithm — security comes from math, not secrecy.

See the full step-by-step breakdown on the [live dashboard](http://localhost:2000) or in [`cur128.py`](cur128.py).

**Properties:** 512-bit output (128 hex chars) | 100 steps | ~49.6% avalanche | Quantum-resistant (lattice-based) | ASIC-resistant (memory-hard + sequential)
