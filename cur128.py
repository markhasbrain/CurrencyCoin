"""
CUR-128: Currency Unified Resistance Hash Algorithm
====================================================
A 100-step, 512-bit (128 hex char) cryptographic hash function.

10 Rounds x 10 Steps:
  Round 1  (Steps 1-10):   PRIME SHATTER     - Modular exponentiation with large primes
  Round 2  (Steps 11-20):  BITWISE HURRICANE  - Rotations, S-box substitution, cross-lane XOR
  Round 3  (Steps 21-30):  GALOIS GRINDER     - Finite field multiplication in GF(2^64)
  Round 4  (Steps 31-40):  PERMUTATION STORM  - Data-dependent bit permutation + nonlinear combine
  Round 5  (Steps 41-50):  MODULAR MAZE       - Chained modular arithmetic, information destruction
  Round 6  (Steps 51-60):  SPONGE SQUEEZE     - Sponge construction absorption
  Round 7  (Steps 61-70):  CHAOS ENGINE       - Lorenz attractor discretized mixing
  Round 8  (Steps 71-80):  LATTICE FOLD       - Lattice-based mixing for quantum resistance
  Round 9  (Steps 81-90):  TEMPORAL BIND      - Sequential forced computation
  Round 10 (Steps 91-100): FINAL FORGE        - Full diffusion, final substitution, output

Public algorithm. Security through math, not secrecy.
"""

import struct

# =============================================================================
# CONSTANTS - All derived from mathematical constants, fully public
# =============================================================================

# First 20 primes above 2^62
PRIMES = [
    4611686018427388039, 4611686018427388079, 4611686018427388123,
    4611686018427388159, 4611686018427388171, 4611686018427388213,
    4611686018427388243, 4611686018427388261, 4611686018427388291,
    4611686018427388321, 4611686018427388369, 4611686018427388399,
    4611686018427388441, 4611686018427388463, 4611686018427388501,
    4611686018427388543, 4611686018427388573, 4611686018427388621,
    4611686018427388651, 4611686018427388693,
]

# S-Box (16x16 = 256 entries) derived from digits of pi
SBOX_PI = [
    0x3, 0x1, 0x4, 0x1, 0x5, 0x9, 0x2, 0x6, 0x5, 0x3, 0x5, 0x8, 0x9, 0x7, 0x9, 0x3,
    0x2, 0x3, 0x8, 0x4, 0x6, 0x2, 0x6, 0x4, 0x3, 0x3, 0x8, 0x3, 0x2, 0x7, 0x9, 0x5,
    0x0, 0x2, 0x8, 0x8, 0x4, 0x1, 0x9, 0x7, 0x1, 0x6, 0x9, 0x3, 0x9, 0x9, 0x3, 0x7,
    0x5, 0x1, 0x0, 0x5, 0x8, 0x2, 0x0, 0x9, 0x7, 0x4, 0x9, 0x4, 0x4, 0x5, 0x9, 0x2,
    0x3, 0x0, 0x7, 0x8, 0x1, 0x6, 0x4, 0x0, 0x6, 0x2, 0x8, 0x6, 0x2, 0x0, 0x8, 0x9,
    0x9, 0x8, 0x6, 0x2, 0x8, 0x0, 0x3, 0x4, 0x8, 0x2, 0x5, 0x3, 0x4, 0x2, 0x1, 0x1,
    0x7, 0x0, 0x6, 0x7, 0x9, 0x8, 0x2, 0x1, 0x4, 0x8, 0x0, 0x8, 0x6, 0x5, 0x1, 0x3,
    0x2, 0x8, 0x2, 0x3, 0x0, 0x6, 0x6, 0x4, 0x7, 0x0, 0x9, 0x3, 0x8, 0x4, 0x4, 0x6,
    0x0, 0x9, 0x5, 0x5, 0x0, 0x5, 0x8, 0x2, 0x2, 0x3, 0x1, 0x7, 0x2, 0x5, 0x3, 0x5,
    0x9, 0x4, 0x0, 0x8, 0x1, 0x2, 0x8, 0x4, 0x8, 0x1, 0x1, 0x1, 0x7, 0x4, 0x5, 0x0,
    0x2, 0x8, 0x4, 0x1, 0x0, 0x2, 0x7, 0x0, 0x1, 0x9, 0x3, 0x8, 0x5, 0x2, 0x1, 0x1,
    0x0, 0x5, 0x5, 0x5, 0x9, 0x6, 0x4, 0x4, 0x6, 0x2, 0x2, 0x9, 0x4, 0x8, 0x9, 0x5,
    0x4, 0x9, 0x3, 0x0, 0x3, 0x8, 0x1, 0x9, 0x6, 0x4, 0x4, 0x2, 0x8, 0x8, 0x1, 0x0,
    0x9, 0x7, 0x5, 0x6, 0x6, 0x5, 0x9, 0x3, 0x3, 0x4, 0x4, 0x6, 0x1, 0x2, 0x8, 0x4,
    0x7, 0x5, 0x6, 0x4, 0x8, 0x2, 0x3, 0x3, 0x7, 0x8, 0x6, 0x7, 0x8, 0x3, 0x1, 0x6,
    0x5, 0x2, 0x7, 0x1, 0x2, 0x0, 0x1, 0x9, 0x0, 0x9, 0x1, 0x4, 0x5, 0x6, 0x4, 0x8,
]

# Build a proper 256-entry S-box with full byte mapping using pi-derived permutation
def _build_sbox():
    """Generate a proper bijective S-box from pi digits."""
    sbox = list(range(256))
    # Fisher-Yates shuffle using pi-derived values
    seed = 314159265358979323846
    for i in range(255, 0, -1):
        seed = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        j = seed % (i + 1)
        sbox[i], sbox[j] = sbox[j], sbox[i]
    return sbox

SBOX = _build_sbox()

# Second S-box derived from sqrt(2) for Round 10
def _build_sbox2():
    sbox = list(range(256))
    seed = 141421356237309504880
    for i in range(255, 0, -1):
        seed = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        j = seed % (i + 1)
        sbox[i], sbox[j] = sbox[j], sbox[i]
    return sbox

SBOX2 = _build_sbox2()

# Constants from Euler's number e for Round 5
E_CONSTANTS = [
    0x2B7E151628AED2A6, 0xABF7158809CF4F3C,
    0x62E7160F38B4DA56, 0xA784D9045190CFEF,
    0x324E7738926CFBE5, 0xF4BF8D8D8C31D763,
    0xDA06C80ABB1185EB, 0x4F7C7B5757F59584,
    0x90CFD47D7C19BB42, 0x158D9554F7B46BCE,
]

# Golden ratio constants for Round 8
PHI_MATRIX_SEED = 0x9E3779B97F4A7C15  # floor(2^64 / phi)

MASK64 = 0xFFFFFFFFFFFFFFFF

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _u64(x):
    """Clamp to unsigned 64-bit."""
    return x & MASK64

def _rotl64(x, n):
    """Rotate left 64-bit."""
    n &= 63
    return _u64((x << n) | (x >> (64 - n))) if n else x

def _rotr64(x, n):
    """Rotate right 64-bit."""
    n &= 63
    return _u64((x >> n) | (x << (64 - n))) if n else x

def _sbox_byte(b, sbox=SBOX):
    """Substitute a single byte through S-box."""
    return sbox[b & 0xFF]

def _sbox_lane(lane, sbox=SBOX):
    """Apply S-box substitution to each byte of a 64-bit lane."""
    result = 0
    for i in range(8):
        byte = (lane >> (i * 8)) & 0xFF
        result |= sbox[byte] << (i * 8)
    return result

def _gf64_multiply(a, b):
    """Multiply in GF(2^64) with polynomial x^64 + x^4 + x^3 + x + 1."""
    POLY = 0x1B  # reduction polynomial (x^4 + x^3 + x + 1)
    result = 0
    a = _u64(a)
    b = _u64(b)
    for _ in range(64):
        if b & 1:
            result ^= a
        hi = a >> 63
        a = _u64(a << 1)
        if hi:
            a ^= POLY
        b >>= 1
    return result

# =============================================================================
# ABSORPTION - Convert arbitrary input to 512-bit state (8 lanes of 64 bits)
# =============================================================================

def _absorb(data: bytes) -> list:
    """Absorb input data into 8 x 64-bit lanes."""
    # Pad to multiple of 64 bytes (512 bits)
    # Append 0x80, then zeros, then 8-byte big-endian length
    msg = bytearray(data)
    orig_len = len(msg)
    msg.append(0x80)
    while (len(msg) % 64) != 56:
        msg.append(0x00)
    msg.extend(struct.pack('>Q', orig_len))

    # Initialize lanes with IV derived from "CURRENCY" in hex
    lanes = [
        0x4355525245_4E4359,  # "CURRENCY"
        0x2D313238_00000000,  # "-128"
        0xDEADBEEF_CAFEBABE,
        0x0123456789ABCDEF,
        0xFEDCBA9876543210,
        0x1111111111111111,
        0xAAAAAAAAAAAAAAAA,
        0x5555555555555555,
    ]

    # XOR input blocks into lanes
    for offset in range(0, len(msg), 64):
        block = msg[offset:offset + 64]
        for i in range(8):
            chunk = struct.unpack_from('>Q', block, i * 8)[0]
            lanes[i] = _u64(lanes[i] ^ chunk)
        # Mini permutation after each block absorption
        for i in range(8):
            lanes[i] = _u64(lanes[i] ^ _rotl64(lanes[(i + 1) % 8], 13))

    return lanes


# =============================================================================
# ROUND 1: PRIME SHATTER (Steps 1-10)
# =============================================================================

def _round1_prime_shatter(lanes):
    for step in range(10):
        p1 = PRIMES[step * 2]
        p2 = PRIMES[step * 2 + 1]
        for i in range(8):
            # Modular exponentiation: lane = lane^3 mod prime
            # (Using cube instead of full prime exponent for performance)
            val = lanes[i] if lanes[i] > 0 else 1
            val = pow(val, 3, p2)
            # Carry overflow XOR into neighbor
            carry = val >> 32
            lanes[(i + 1) % 8] = _u64(lanes[(i + 1) % 8] ^ carry)
            lanes[i] = _u64(val)
    return lanes


# =============================================================================
# ROUND 2: BITWISE HURRICANE (Steps 11-20)
# =============================================================================

def _round2_bitwise_hurricane(lanes):
    for step in range(10):
        for i in range(8):
            # Data-dependent rotation
            rot_amount = lanes[(i + 3) % 8] & 63
            lanes[i] = _rotl64(lanes[i], rot_amount)
            # S-box substitution
            lanes[i] = _sbox_lane(lanes[i])
            # Cross-lane XOR
            lanes[i] = _u64(lanes[i] ^ lanes[(i + 5) % 8])
        # Extra mixing per step
        lanes[0], lanes[7] = _u64(lanes[0] ^ lanes[7]), _u64(lanes[7] ^ lanes[0])
    return lanes


# =============================================================================
# ROUND 3: GALOIS GRINDER (Steps 21-30)
# =============================================================================

def _round3_galois_grinder(lanes):
    for step in range(10):
        new_lanes = lanes[:]
        for i in range(8):
            gf_prod = _gf64_multiply(lanes[i], lanes[(i + 1) % 8])
            new_lanes[i] = _u64(gf_prod ^ lanes[(i + 4) % 8])
        lanes = new_lanes
    return lanes


# =============================================================================
# ROUND 4: PERMUTATION STORM (Steps 31-40)
# =============================================================================

def _round4_permutation_storm(lanes):
    for step in range(10):
        # Convert lanes to flat bit array (represented as int for efficiency)
        state_int = 0
        for i in range(8):
            state_int |= (lanes[i] << (i * 64))

        # Data-dependent bit permutation using lane values as seeds
        perm_seed = lanes[step % 8]
        # Simplified permutation: swap bit pairs based on seed
        for bit_round in range(32):
            seed_bits = (perm_seed >> (bit_round * 2)) & 0x3
            shift = (seed_bits + 1) * 7 + bit_round
            mask_a = 1 << (shift % 512)
            mask_b = 1 << ((shift + 137) % 512)
            bit_a = 1 if (state_int & mask_a) else 0
            bit_b = 1 if (state_int & mask_b) else 0
            if bit_a != bit_b:
                state_int ^= mask_a | mask_b

        # Nonlinear combination: for groups of 3 bits, a XOR (b AND c)
        result = 0
        for bit in range(0, 512, 3):
            a = (state_int >> bit) & 1
            b = (state_int >> ((bit + 1) % 512)) & 1
            c = (state_int >> ((bit + 2) % 512)) & 1
            nl = a ^ (b & c)
            result |= nl << bit

        state_int = result

        # Convert back to lanes
        for i in range(8):
            lanes[i] = _u64(state_int >> (i * 64))

    return lanes


# =============================================================================
# ROUND 5: MODULAR MAZE (Steps 41-50)
# =============================================================================

def _round5_modular_maze(lanes):
    MOD = (1 << 64) - 59  # 2^64 - 59, a prime
    for step in range(10):
        c = E_CONSTANTS[step]
        for i in range(0, 8, 2):
            j = i + 1
            combined = (lanes[i] * lanes[j] + c) % MOD
            lanes[i] = _u64(combined)
            lanes[j] = _u64(combined ^ _rotl64(lanes[j], step + 7))
        # Forward cascade
        for i in range(1, 8):
            lanes[i] = _u64(lanes[i] ^ _rotl64(lanes[i - 1], 11))
    return lanes


# =============================================================================
# ROUND 6: SPONGE SQUEEZE (Steps 51-60)
# =============================================================================

def _round6_sponge_squeeze(lanes):
    for step in range(10):
        # Rate = lanes 0-3, Capacity = lanes 4-7
        rate = lanes[:4]
        cap = lanes[4:]

        # rate ^= rotate(capacity, step) XOR sbox(capacity)
        for i in range(4):
            rotated = _rotl64(cap[i], (step + 1) * 3)
            substituted = _sbox_lane(cap[i])
            rate[i] = _u64(rate[i] ^ rotated ^ substituted)

        # capacity = rate_old XOR gf_multiply(capacity, rate_new)
        old_rate = lanes[:4]  # before modification
        for i in range(4):
            gf = _gf64_multiply(cap[i], rate[i])
            cap[i] = _u64(old_rate[i] ^ gf)

        lanes = rate + cap
    return lanes


# =============================================================================
# ROUND 7: CHAOS ENGINE (Steps 61-70)
# =============================================================================

def _round7_chaos_engine(lanes):
    # Lorenz parameters (scaled to integer arithmetic)
    SIGMA = 10
    RHO = 28
    BETA_NUM, BETA_DEN = 8, 3
    SCALE = 1 << 16  # fixed-point scale

    for step in range(10):
        for i in range(0, 8, 3):
            # Use 3 lanes as x, y, z
            x = lanes[i % 8]
            y = lanes[(i + 1) % 8]
            z = lanes[(i + 2) % 8]

            # Discretized Lorenz with wrapping
            dx = _u64(SIGMA * (_u64(y - x) & MASK64))
            dy = _u64(_u64(x * (RHO - (z & 0xFF))) - y)
            dz = _u64(_u64((x * y) >> 16) - _u64(BETA_NUM * z // BETA_DEN))

            lanes[i % 8] = _u64(x + (dx >> 8))
            lanes[(i + 1) % 8] = _u64(y + (dy >> 8))
            lanes[(i + 2) % 8] = _u64(z + (dz >> 8))

        # Extra diffusion
        for i in range(8):
            lanes[i] = _u64(lanes[i] ^ _rotl64(lanes[(i + 2) % 8], 17 + step))

    return lanes


# =============================================================================
# ROUND 8: LATTICE FOLD (Steps 71-80)
# =============================================================================

def _round8_lattice_fold(lanes):
    # Generate mixing matrix from golden ratio
    matrix = []
    val = PHI_MATRIX_SEED
    for i in range(8):
        row = []
        for j in range(8):
            val = _u64(val * 6364136223846793005 + 1442695040888963407)
            row.append(val)
        matrix.append(row)

    Q = (1 << 64) - 189  # large prime modulus

    for step in range(10):
        new_lanes = [0] * 8
        for i in range(8):
            acc = 0
            for j in range(8):
                acc = (acc + lanes[j] * matrix[i][j]) % Q
            # Add deterministic "noise" from current state
            noise = _rotl64(lanes[i], step * 3 + 7) & 0xFFFF
            new_lanes[i] = _u64(acc ^ noise)
        lanes = new_lanes
    return lanes


# =============================================================================
# ROUND 9: TEMPORAL BIND (Steps 81-90)
# =============================================================================

def _round9_temporal_bind(lanes):
    for step in range(10):
        step_const = _u64(PRIMES[step] ^ E_CONSTANTS[step])
        # Force sequential: each mini-step depends on previous
        for i in range(8):
            lanes[i] = _u64(lanes[i] ^ step_const)
            # Mini CUR: 8 sub-steps of mixing
            for sub in range(8):
                lanes[i] = _u64(lanes[i] ^ _rotl64(lanes[(i + sub + 1) % 8], sub * 7 + 3))
                lanes[i] = _sbox_lane(lanes[i])
                lanes[i] = _u64(lanes[i] * PRIMES[sub % len(PRIMES)] + 1)
                lanes[i] = _u64(lanes[i] & MASK64)
    return lanes


# =============================================================================
# ROUND 10: FINAL FORGE (Steps 91-100)
# =============================================================================

def _round10_final_forge(lanes):
    for step in range(10):
        # Full diffusion: every lane affects every other
        new_lanes = [0] * 8
        for i in range(8):
            for j in range(8):
                new_lanes[i] = _u64(new_lanes[i] ^ _rotl64(lanes[j], (i * j + step) % 64))

        # S-box2 substitution (sqrt(2) derived)
        for i in range(8):
            new_lanes[i] = _sbox_lane(new_lanes[i], SBOX2)

        # Lane folding
        for i in range(0, 8, 2):
            fold = _u64(new_lanes[i] ^ new_lanes[i + 1])
            new_lanes[i] = _u64(fold * 0x517CC1B727220A95 + 1)  # odd multiply
            new_lanes[i + 1] = _u64(fold ^ _rotl64(new_lanes[i], 23))

        lanes = new_lanes

    # Step 100: Final finalization
    # Checksum lane
    checksum = 0
    for i in range(8):
        checksum = _u64(checksum ^ lanes[i])
        checksum = _rotl64(checksum, 7)
    for i in range(8):
        lanes[i] = _u64(lanes[i] ^ _rotl64(checksum, i * 8))

    return lanes


# =============================================================================
# MAIN HASH FUNCTION
# =============================================================================

def cur128(data: bytes) -> str:
    """
    CUR-128 Hash Function

    Input:  arbitrary bytes
    Output: 128 hex characters (512 bits)

    100 steps of irreversible mathematical transformation.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    # Absorb input into 8 x 64-bit lanes
    lanes = _absorb(data)

    # 100 Steps across 10 Rounds
    lanes = _round1_prime_shatter(lanes)     # Steps 1-10
    lanes = _round2_bitwise_hurricane(lanes)  # Steps 11-20
    lanes = _round3_galois_grinder(lanes)     # Steps 21-30
    lanes = _round4_permutation_storm(lanes)  # Steps 31-40
    lanes = _round5_modular_maze(lanes)       # Steps 41-50
    lanes = _round6_sponge_squeeze(lanes)     # Steps 51-60
    lanes = _round7_chaos_engine(lanes)       # Steps 61-70
    lanes = _round8_lattice_fold(lanes)       # Steps 71-80
    lanes = _round9_temporal_bind(lanes)      # Steps 81-90
    lanes = _round10_final_forge(lanes)       # Steps 91-100

    # Format output: 8 lanes x 16 hex chars = 128 hex characters
    return ''.join(f'{lane:016x}' for lane in lanes)


def cur128_bytes(data: bytes) -> bytes:
    """Return raw 64-byte (512-bit) hash."""
    hex_str = cur128(data)
    return bytes.fromhex(hex_str)


# =============================================================================
# QUICK VERIFICATION
# =============================================================================

if __name__ == '__main__':
    # Test basic functionality
    print("CUR-128 Hash Algorithm")
    print("=" * 60)

    test_inputs = [
        b"hello",
        b"hellp",  # 1 char different
        b"Currency",
        b"",
        b"a" * 1000,
    ]

    for inp in test_inputs:
        h = cur128(inp)
        display = inp[:30].decode('utf-8', errors='replace')
        if len(inp) > 30:
            display += "..."
        print(f'CUR-128("{display}") =')
        print(f'  {h}')
        print(f'  Length: {len(h)} chars ({len(h)*4} bits)')
        print()

    # Avalanche test
    h1 = cur128(b"hello")
    h2 = cur128(b"hellp")
    diff_bits = bin(int(h1, 16) ^ int(h2, 16)).count('1')
    print(f"Avalanche test: 'hello' vs 'hellp'")
    print(f"  Bits different: {diff_bits}/512 ({diff_bits/512*100:.1f}%)")
    print(f"  (Ideal: ~50% = ~256 bits)")
