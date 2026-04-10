import fs from "fs";
import path from "path";

const TOTAL_SUPPLY = 10_000_000;
const TRADING_UNLOCK_PRICE = 100.0;
const MINED_PATH = path.join(process.cwd(), "..", "currency_data", "mined.json");

function getDifficulty(minedCount: number): number {
  if (minedCount >= TOTAL_SUPPLY - 1) return 128;
  const ratio = minedCount / TOTAL_SUPPLY;
  if (ratio < 0.10) return 4;
  if (ratio < 0.20) return 5;
  if (ratio < 0.30) return 6;
  if (ratio < 0.40) return 7;
  if (ratio < 0.50) return 8;
  if (ratio < 0.60) return 9;
  if (ratio < 0.70) return 10;
  if (ratio < 0.80) return 11;
  if (ratio < 0.90) return 12;
  if (ratio < 0.95) return 14;
  if (ratio < 0.99) return 16;
  return 20;
}

function getEffectiveOdds(minedCount: number): string {
  const diff = getDifficulty(minedCount);
  const matchOdds = Math.pow(16, diff);
  const remaining = Math.max(1, TOTAL_SUPPLY - minedCount);
  const effective = matchOdds / remaining;
  if (effective < 1) return "1 in 0";
  return `1 in ${effective.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

function buildStatus() {
  let mined: Array<{
    coin_index: number;
    miner_address: string;
    timestamp: number;
  }> = [];

  try {
    const raw = fs.readFileSync(MINED_PATH, "utf-8");
    const data = JSON.parse(raw);
    mined = data.mined || [];
  } catch {
    // not found
  }

  const totalMined = mined.length;
  const balances: Record<string, number> = {};
  for (const entry of mined) {
    balances[entry.miner_address] = (balances[entry.miner_address] || 0) + 1;
  }

  const topHolders = Object.entries(balances)
    .sort((a, b) => b[1] - a[1])
    .map(([addr, bal], i) => ({
      rank: i + 1,
      address: addr,
      balance: bal,
      percent: ((bal / TOTAL_SUPPLY) * 100).toFixed(4),
    }));

  const recent = mined
    .slice(-10)
    .reverse()
    .map((e) => ({
      coin_index: e.coin_index,
      miner: e.miner_address.slice(0, 20) + "...",
    }));

  const diff = getDifficulty(totalMined);

  return {
    total_supply: TOTAL_SUPPLY,
    mined: totalMined,
    remaining: TOTAL_SUPPLY - totalMined,
    percent_mined: ((totalMined / TOTAL_SUPPLY) * 100).toFixed(4),
    difficulty: { match_chars: diff, effective_odds: getEffectiveOdds(totalMined) },
    trading_locked: true,
    unlock_price: TRADING_UNLOCK_PRICE,
    top_holders: topHolders,
    recent_activity: recent,
  };
}

export const dynamic = "force-dynamic";

export async function GET() {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      // Send immediately
      const initial = buildStatus();
      controller.enqueue(encoder.encode(`data: ${JSON.stringify(initial)}\n\n`));

      let lastMinedCount = initial.mined;
      let lastSize = 0;
      try {
        lastSize = fs.statSync(MINED_PATH).size;
      } catch {
        // file may not exist yet
      }

      // Poll at 200ms -- only send when mined count actually increases
      const interval = setInterval(() => {
        try {
          const currentSize = fs.statSync(MINED_PATH).size;
          if (currentSize !== lastSize && currentSize > 10) {
            lastSize = currentSize;
            const status = buildStatus();
            // Only push if mined count went UP (never backwards)
            if (status.mined >= lastMinedCount) {
              // Skip if nothing changed
              if (status.mined === lastMinedCount) return;
              lastMinedCount = status.mined;
              controller.enqueue(
                encoder.encode(`data: ${JSON.stringify(status)}\n\n`)
              );
            }
          }
        } catch {
          // file being written to, skip this tick
        }
      }, 200);

      const cleanup = () => {
        clearInterval(interval);
        try {
          controller.close();
        } catch {
          // already closed
        }
      };

      setTimeout(cleanup, 600_000);
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
