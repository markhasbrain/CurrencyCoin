"""
Currency (CRNY) — Configuration & Constants
=============================================
"""

# Total supply — 10 million coins, that's it, forever
TOTAL_SUPPLY = 10_000_000

# Ticker symbol
TICKER = "CUR"
NAME = "Currency Coin"

# The master seed — public, deterministic, unchangeable
# This seed + coin index generates every coin's target hash
# Knowing this doesn't help you mine — CUR-128 is one-way
GENESIS_MASTER_SEED = "CURRENCY-GENESIS-2026-04-10-22516162-THE-ONLY-WAY-IS-FORWARD"

# Phase 2 unlock price (USD per CRNY)
TRADING_UNLOCK_PRICE = 100.00

# Data directories
DATA_DIR = "currency_data"
WALLETS_DIR = f"{DATA_DIR}/wallets"
LEDGER_FILE = f"{DATA_DIR}/ledger.json"
GENESIS_FILE = f"{DATA_DIR}/genesis.bin"
MINED_FILE = f"{DATA_DIR}/mined.json"

# Mining
BATCH_SIZE = 10_000  # guesses per batch before checking
DISPLAY_INTERVAL = 5  # seconds between status updates

# Network (future)
DEFAULT_PORT = 7742
PROTOCOL_VERSION = 1
