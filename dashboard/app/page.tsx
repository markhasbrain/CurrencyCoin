"use client";

import { useEffect, useRef, useState } from "react";
import {
  Coins,
  Pickaxe,
  Package,
  BarChart3,
  Shield,
  Lock,
  Unlock,
  Trophy,
  Activity,
  Cpu,
  Hash,
  Gem,
  Terminal,
  DollarSign,
  TrendingUp,
  Users,
  CircleDot,
} from "lucide-react";

interface StatusData {
  total_supply: number;
  mined: number;
  remaining: number;
  percent_mined: string;
  difficulty: {
    match_chars: number;
    effective_odds: string;
  };
  trading_locked: boolean;
  unlock_price: number;
  top_holders: Array<{
    rank: number;
    address: string;
    balance: number;
    percent: string;
  }>;
  recent_activity: Array<{
    coin_index: number;
    miner: string;
  }>;
}

export default function Home() {
  const [data, setData] = useState<StatusData | null>(null);

  const lastMinedRef = useRef(0);

  useEffect(() => {
    let es: EventSource | null = null;
    const connect = () => {
      es = new EventSource("/api/status/stream");
      es.onmessage = (event) => {
        try {
          const json = JSON.parse(event.data);
          if (json.mined >= lastMinedRef.current) {
            lastMinedRef.current = json.mined;
            setData(json);
          }
        } catch {
          /* skip */
        }
      };
      es.onerror = () => {
        es?.close();
        setTimeout(connect, 1000);
      };
    };
    connect();
    return () => es?.close();
  }, []);

  const pct = data ? parseFloat(data.percent_mined) : 0;

  return (
    <div className="min-h-screen bg-[#09090b] text-white">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-white/5">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(34,197,94,0.08),transparent_70%)]" />
        <div className="max-w-5xl mx-auto px-6 pt-20 pb-16 relative z-10">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center border border-green-500/30">
              <Coins className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Currency Coin</h1>
              <p className="text-sm text-zinc-500 font-mono">CUR</p>
            </div>
          </div>
          <p className="text-zinc-400 text-lg max-w-2xl leading-relaxed">
            10,000,000 coins. All mineable. No pre-mine, no ICO, no dev allocation.
            Secured by <span className="text-green-400 font-mono">CUR-128</span> --
            a 100-step, 512-bit, quantum-resistant hash algorithm.
          </p>
          <div className="flex gap-3 mt-6">
            <span className="inline-flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
              <Pickaxe className="w-3 h-3" />
              Phase 1 -- Mining Only
            </span>
            <span className="inline-flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700">
              <Lock className="w-3 h-3" />
              Trading unlocks at $100/coin
            </span>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="max-w-5xl mx-auto px-6 py-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard icon={<Package className="w-4 h-4" />} label="Total Supply" value={data ? data.total_supply.toLocaleString() : "--"} sub="CUR" />
          <StatCard icon={<Pickaxe className="w-4 h-4" />} label="Mined" value={data ? data.mined.toLocaleString() : "--"} sub="CUR" highlight />
          <StatCard icon={<Gem className="w-4 h-4" />} label="Remaining" value={data ? data.remaining.toLocaleString() : "--"} sub="CUR" />
          <StatCard icon={<BarChart3 className="w-4 h-4" />} label="Mined" value={data ? `${data.percent_mined}%` : "--"} sub="of supply" />
        </div>

        {/* Progress Bar */}
        <div className="mt-6 bg-zinc-900 rounded-full h-4 border border-zinc-800 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-600 to-green-400 rounded-full transition-all duration-300"
            style={{ width: `${Math.max(pct, 0.1)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-zinc-600 mt-2 font-mono">
          <span>0%</span>
          <span>{data?.percent_mined ?? "0"}% mined</span>
          <span>100%</span>
        </div>
      </section>

      {/* Difficulty + Mining Info */}
      <section className="max-w-5xl mx-auto px-6 pb-10">
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
              <Shield className="w-4 h-4" />
              Mining Difficulty
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-zinc-500 flex items-center gap-1.5"><Hash className="w-3.5 h-3.5" /> Match required</span>
                <span className="font-mono text-green-400">
                  {data ? `${data.difficulty.match_chars}/128` : "--"} hex chars
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500 flex items-center gap-1.5"><CircleDot className="w-3.5 h-3.5" /> Odds per guess</span>
                <span className="font-mono text-zinc-300">
                  {data?.difficulty.effective_odds ?? "--"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500 flex items-center gap-1.5"><TrendingUp className="w-3.5 h-3.5" /> Phase</span>
                <span className="font-mono text-amber-400">
                  {data?.trading_locked ? "1 -- Mining Only" : "2 -- Open Trading"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500 flex items-center gap-1.5">
                  {data?.trading_locked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                  Trading
                </span>
                <span className={`font-mono ${data?.trading_locked ? "text-red-400" : "text-green-400"}`}>
                  {data?.trading_locked ? "LOCKED" : "UNLOCKED"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500 flex items-center gap-1.5"><DollarSign className="w-3.5 h-3.5" /> Unlock price</span>
                <span className="font-mono text-zinc-300">$100.00 / CUR</span>
              </div>
            </div>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
              <TrendingUp className="w-4 h-4" />
              Difficulty Curve
            </h3>
            <div className="space-y-1 text-xs font-mono">
              {[
                { range: "0 - 1M", chars: 4, label: "Easy" },
                { range: "1M - 2M", chars: 5, label: "Moderate" },
                { range: "2M - 3M", chars: 6, label: "Hard" },
                { range: "3M - 4M", chars: 7, label: "Serious" },
                { range: "4M - 5M", chars: 8, label: "Intense" },
                { range: "5M - 6M", chars: 9, label: "Brutal" },
                { range: "6M - 7M", chars: 10, label: "Savage" },
                { range: "7M - 8M", chars: 11, label: "Extreme" },
                { range: "8M - 9M", chars: 12, label: "Insane" },
                { range: "9M - 10M", chars: "14-128", label: "Impossible" },
              ].map((tier) => {
                const active = data && data.difficulty.match_chars === tier.chars;
                return (
                  <div
                    key={tier.range}
                    className={`flex justify-between py-1 px-2 rounded ${active ? "bg-green-500/10 text-green-400" : "text-zinc-500"}`}
                  >
                    <span>{tier.range}</span>
                    <span>{tier.chars}/128 chars</span>
                    <span className={active ? "text-green-300" : ""}>{tier.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Leaderboard */}
      <section className="max-w-5xl mx-auto px-6 pb-10">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-zinc-400 uppercase tracking-wider">
              <Trophy className="w-4 h-4" />
              Leaderboard
            </h3>
            <span className="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-600">
              <Users className="w-3.5 h-3.5" />
              {data?.top_holders.length ?? 0} holder{(data?.top_holders.length ?? 0) !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-zinc-500 text-xs uppercase tracking-wider border-b border-zinc-800">
                  <th className="px-6 py-3 w-16">#</th>
                  <th className="px-6 py-3">Address</th>
                  <th className="px-6 py-3 text-right">Balance</th>
                  <th className="px-6 py-3 text-right">% Supply</th>
                  <th className="px-6 py-3 text-right w-48">Share</th>
                </tr>
              </thead>
              <tbody>
                {(!data || data.top_holders.length === 0) && (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-zinc-600 font-mono">
                      No coins mined yet. Be the first.
                    </td>
                  </tr>
                )}
                {data?.top_holders.map((h) => (
                  <tr key={h.rank} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                    <td className="px-6 py-3 font-mono">
                      {h.rank === 1 && <span className="text-amber-400 flex items-center gap-1"><Trophy className="w-3.5 h-3.5" />{h.rank}</span>}
                      {h.rank === 2 && <span className="text-zinc-300">{h.rank}</span>}
                      {h.rank === 3 && <span className="text-amber-700">{h.rank}</span>}
                      {h.rank > 3 && <span className="text-zinc-600">{h.rank}</span>}
                    </td>
                    <td className="px-6 py-3 font-mono text-zinc-300 text-xs">{h.address.slice(0, 16)}...{h.address.slice(-16)}</td>
                    <td className="px-6 py-3 text-right font-mono text-green-400">{h.balance.toLocaleString()}</td>
                    <td className="px-6 py-3 text-right font-mono text-zinc-500">{h.percent}%</td>
                    <td className="px-6 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-24 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="h-full bg-green-500 rounded-full"
                            style={{ width: `${Math.min(parseFloat(h.percent) * 10, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Recent Activity */}
      <section className="max-w-5xl mx-auto px-6 pb-10">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-zinc-800">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-zinc-400 uppercase tracking-wider">
              <Activity className="w-4 h-4" />
              Recent Activity
            </h3>
          </div>
          <div className="divide-y divide-zinc-800/50">
            {(!data || data.recent_activity.length === 0) && (
              <div className="px-6 py-8 text-center text-zinc-600 font-mono text-sm">
                No activity yet.
              </div>
            )}
            {data?.recent_activity.map((a, i) => (
              <div key={i} className="px-6 py-3 flex items-center justify-between hover:bg-zinc-800/20 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1 text-xs font-mono px-2 py-0.5 rounded bg-green-500/10 text-green-400 border border-green-500/20">
                    <Pickaxe className="w-3 h-3" />
                    MINED
                  </span>
                  <span className="text-sm font-mono text-zinc-300">
                    Coin #{a.coin_index.toLocaleString()}
                  </span>
                </div>
                <span className="text-xs font-mono text-zinc-600">{a.miner}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How to Mine - RIGHT after Recent Activity */}
      <section className="max-w-5xl mx-auto px-6 pb-10">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
            <Terminal className="w-4 h-4" />
            How to Mine
          </h3>
          <div className="space-y-3 text-sm font-mono">
            <div className="bg-black/50 rounded-lg p-4 border border-zinc-800">
              <span className="text-zinc-500"># 1. Clone the repo</span>
              <br />
              <span className="text-green-400">git clone https://github.com/markhasbrain/CurrencyCoin.git</span>
              <br />
              <span className="text-green-400">cd CurrencyCoin</span>
            </div>
            <div className="bg-black/50 rounded-lg p-4 border border-zinc-800">
              <span className="text-zinc-500"># 2. Generate all 10M coin targets (takes ~2 min)</span>
              <br />
              <span className="text-green-400">python currency.py genesis</span>
            </div>
            <div className="bg-black/50 rounded-lg p-4 border border-zinc-800">
              <span className="text-zinc-500"># 3. Generate a wallet</span>
              <br />
              <span className="text-green-400">python currency.py wallet generate</span>
            </div>
            <div className="bg-black/50 rounded-lg p-4 border border-zinc-800">
              <span className="text-zinc-500"># 4. Start mining (replace with your public key)</span>
              <br />
              <span className="text-green-400">{"python currency.py mine <your_public_key> 4"}</span>
            </div>
            <div className="bg-black/50 rounded-lg p-4 border border-zinc-800">
              <span className="text-zinc-500"># 5. Check your balance</span>
              <br />
              <span className="text-green-400">{"python currency.py wallet open <your_private_key>"}</span>
            </div>
            <div className="bg-black/50 rounded-lg p-4 border border-zinc-800">
              <span className="text-zinc-500"># 6. Send CUR to someone</span>
              <br />
              <span className="text-green-400">{"python currency.py send <your_private_key> <their_public_key> <amount>"}</span>
            </div>
          </div>
        </div>
      </section>

      {/* CUR-128 Algorithm Section */}
      <section className="max-w-5xl mx-auto px-6 pb-10">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-6">
            <Cpu className="w-4 h-4" />
            CUR-128 Algorithm
          </h3>
          <p className="text-zinc-400 text-sm mb-6 leading-relaxed">
            CUR-128 is a custom 100-step cryptographic hash function producing 512-bit (128 hex character) outputs.
            It is irreversible, quantum-resistant, and ASIC-resistant by design. The algorithm is fully public --
            security comes from math, not secrecy. 100 steps. 10 rounds. One way in, no way back.
          </p>

          <div className="bg-black/60 border border-zinc-700/50 rounded-lg p-6 overflow-x-auto">
            <p className="text-xs text-zinc-500 mb-4 font-mono">{"// CUR-128(x) = what happens to your input across 100 steps"}</p>
            <pre className="text-[10px] md:text-[11px] font-mono leading-5 text-green-400/90 whitespace-pre-wrap break-all">{
`Let x = input bytes, padded to 64B with 0x80 || zeros || len(x) as uint64

ABSORB: Split x into 8 lanes of 64 bits each:
  L[0..7] = IV[0..7] XOR chunks(x), where IV = [0x4355525245_4E4359, 0x2D313238_00000000,
  0xDEADBEEF_CAFEBABE, 0x0123456789ABCDEF, 0xFEDCBA9876543210, 0x1111111111111111,
  0xAAAAAAAAAAAAAAAA, 0x5555555555555555]
  After each 64B block: L[i] ^= ROTL64(L[(i+1)%8], 13)

STEP 1-10 (PRIME SHATTER): For each step s in [0,9], for each lane i in [0,7]:
  P1 = PRIMES[s*2], P2 = PRIMES[s*2+1]  (primes > 2^62)
  L[i] = L[i]^3 mod P2
  L[(i+1)%8] ^= (L[i] >> 32)

STEP 11-20 (BITWISE HURRICANE): For each step, for each lane i:
  L[i] = ROTL64(L[i], L[(i+3)%8] & 63)
  L[i] = SBOX_PI[ L[i] byte-by-byte ]    (256-entry S-box from Fisher-Yates(pi))
  L[i] ^= L[(i+5)%8]
  L[0], L[7] = L[0]^L[7], L[7]^L[0]

STEP 21-30 (GALOIS GRINDER): For each step, for each lane i:
  L'[i] = GF_MUL_2_64(L[i], L[(i+1)%8]) XOR L[(i+4)%8]
  where GF_MUL uses irreducible polynomial x^64 + x^4 + x^3 + x + 1

STEP 31-40 (PERMUTATION STORM): For each step:
  state = concat(L[0..7]) as 512-bit integer
  For 32 rounds: swap bits at positions (seed*7+r) and (seed*7+r+137) mod 512
  For every 3 bits (a,b,c): output bit = a XOR (b AND c)
  L[0..7] = split(state)

STEP 41-50 (MODULAR MAZE): For each step s, constant C = E_CONSTANTS[s]:
  For pairs (i, i+1): L[i] = (L[i] * L[i+1] + C) mod (2^64 - 59)
  L[i+1] = L[i] XOR ROTL64(L[i+1], s+7)
  Cascade: L[i] ^= ROTL64(L[i-1], 11) for i in [1,7]

STEP 51-60 (SPONGE SQUEEZE): Split L into rate[0..3], capacity[0..3]:
  rate[i] ^= ROTL64(cap[i], (s+1)*3) XOR SBOX(cap[i])
  cap[i] = rate_old[i] XOR GF_MUL(cap[i], rate_new[i])
  L = rate || capacity

STEP 61-70 (CHAOS ENGINE): For groups of 3 lanes (x,y,z):
  dx = 10 * (y - x),  dy = x*(28 - z&0xFF) - y,  dz = (x*y)>>16 - 8z/3
  x += dx>>8,  y += dy>>8,  z += dz>>8
  L[i] ^= ROTL64(L[(i+2)%8], 17+s)

STEP 71-80 (LATTICE FOLD): Matrix M[8x8] from LCG(phi_seed):
  For each step: L'[i] = (SUM_j(L[j] * M[i][j])) mod (2^64-189)
  L'[i] ^= ROTL64(L[i], s*3+7) & 0xFFFF

STEP 81-90 (TEMPORAL BIND): For each step, each lane sequentially:
  L[i] ^= PRIMES[s] XOR E_CONSTANTS[s]
  For 8 sub-rounds: L[i] ^= ROTL64(L[(i+sub+1)%8], sub*7+3)
  L[i] = SBOX(L[i]),  L[i] = (L[i] * PRIMES[sub] + 1) & 0xFFFFFFFFFFFFFFFF

STEP 91-100 (FINAL FORGE): For each step:
  L'[i] = XOR_j( ROTL64(L[j], (i*j+s) % 64) )   for all j in [0,7]
  L'[i] = SBOX2_SQRT2[ L'[i] byte-by-byte ]
  For pairs: fold = L'[i] XOR L'[i+1]
  L'[i] = fold * 0x517CC1B727220A95 + 1
  L'[i+1] = fold XOR ROTL64(L'[i], 23)

FINALIZE: checksum = 0
  For i in [0,7]: checksum ^= L[i], checksum = ROTL64(checksum, 7)
  For i in [0,7]: L[i] ^= ROTL64(checksum, i*8)

OUTPUT = concat(L[0], L[1], L[2], L[3], L[4], L[5], L[6], L[7])
       = 512 bits = 128 hexadecimal characters`
            }</pre>
            <div className="mt-4 pt-4 border-t border-zinc-800 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
              <div>
                <span className="text-zinc-500 block">Output</span>
                <span className="text-green-400">512 bits (128 hex)</span>
              </div>
              <div>
                <span className="text-zinc-500 block">Steps</span>
                <span className="text-green-400">100 (10 rounds x 10)</span>
              </div>
              <div>
                <span className="text-zinc-500 block">Avalanche</span>
                <span className="text-green-400">~49.6% (near ideal 50%)</span>
              </div>
              <div>
                <span className="text-zinc-500 block">Quantum Safe</span>
                <span className="text-green-400">Yes (lattice-based)</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 py-8 text-center text-xs text-zinc-600 font-mono flex items-center justify-center gap-2">
        <Coins className="w-3.5 h-3.5" />
        Currency Coin (CUR) -- 10,000,000 total supply -- CUR-128 secured -- Phase 1
      </footer>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  sub,
  highlight,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
  highlight?: boolean;
}) {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
      <p className="flex items-center gap-1.5 text-xs text-zinc-500 uppercase tracking-wider mb-1">
        {icon}
        {label}
      </p>
      <p className={`text-2xl font-bold font-mono ${highlight ? "text-green-400" : "text-white"}`}>
        {value}
      </p>
      <p className="text-xs text-zinc-600 font-mono mt-1">{sub}</p>
    </div>
  );
}
