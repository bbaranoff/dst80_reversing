import sys
import argparse
from rich import print

# --- LOGIQUE COEUR DST80 (Extraite de dst80.py) ---
def bit(x, n): return (x >> n) & 1
def bit_slice(x, msb, lsb): return (x & ((1 << (msb + 1)) - 1)) >> lsb
def bv2i(*args):
    o = 0
    for i in args: o = (o << 1) | i
    return o

def fa(x): return bit(0x3a35acc5, x)
def fb(x): return bit(0xac35742e, x)
def fc(x): return bit(0xb81d8bd1, x)
def fd(x): return bit(0x5acc335a, x)
def fe(x): return bit(0xe247, x)
def fg(x): return bit(0x4e72, x)
def h(x): return (0x1f9826f4 >> (2 * x)) & 3

def fn(s, k):
    return (
        fd(bv2i(bit(s, 32), bit(k, 32), bit(s, 24), bit(k, 24), bit(s, 16))),
        fe(bv2i(bit(k, 16), bit(s, 8), bit(k, 8), bit(k, 0))),
        fb(bv2i(bit(s, 33), bit(k, 33), bit(s, 25), bit(k, 25), bit(s, 17))),
        fc(bv2i(bit(k, 17), bit(s, 9), bit(k, 9), bit(k, 1))),
        fa(bv2i(bit(s, 34), bit(k, 34), bit(s, 26), bit(k, 26), bit(s, 18))),
        fb(bv2i(bit(k, 18), bit(s, 10), bit(k, 10), bit(k, 2))),
        fc(bv2i(bit(s, 35), bit(k, 35), bit(s, 27), bit(k, 27), bit(s, 19))),
        fd(bv2i(bit(k, 19), bit(s, 11), bit(k, 11), bit(k, 3))),
        fa(bv2i(bit(s, 36), bit(k, 36), bit(s, 28), bit(k, 28), bit(s, 20))),
        fe(bv2i(bit(k, 20), bit(s, 12), bit(k, 12), bit(k, 4))),
        fb(bv2i(bit(s, 37), bit(k, 37), bit(s, 29), bit(k, 29), bit(s, 21))),
        fc(bv2i(bit(k, 21), bit(s, 13), bit(k, 13), bit(k, 5))),
        fa(bv2i(bit(s, 38), bit(k, 38), bit(s, 30), bit(k, 30), bit(s, 22))),
        fb(bv2i(bit(k, 22), bit(s, 14), bit(k, 14), bit(k, 6))),
        fc(bv2i(bit(s, 39), bit(k, 39), bit(s, 31), bit(k, 31), bit(s, 23))),
        fd(bv2i(bit(k, 23), bit(s, 15), bit(k, 15), bit(k, 7)))
    )

def lfsr_round(k):
    fb = bit(k, 39) ^ bit(k, 38) ^ bit(k, 34) ^ bit(k, 29) ^ bit(k, 24) ^ bit(k, 19) ^ bit(k, 14) ^ bit(k, 9)
    return ((k << 1) | fb) & 0x7fffffffff

def simulate_dst80(kl, kr, challenge):
    s = challenge & 0x7fffffffff
    for _ in range(200):
        ml, mr = fn(s, kl), fn(s, kr)
        key_merged = (bv2i(*ml[:10]) << 10) | bv2i(*mr[:10])
        
        # Calcul de la sortie f_func
        x = key_merged
        v = h(bv2i(bit(x, 19), bit(x, 18), bit(x, 17), bit(x, 16)))
        v = h(bv2i(bit(x, 15), bit(x, 14), bit(x, 13), bit(v >> 1, 0), bit(v, 0)))
        v = h(bv2i(bit(x, 12), bit(x, 11), bit(x, 10), bit(v >> 1, 0), bit(v, 0)))
        v = h(bv2i(bit(x, 9), bit(x, 8), bit(x, 7), bit(v >> 1, 0), bit(v, 0)))
        v = h(bv2i(bit(x, 6), bit(x, 5), bit(x, 4), bit(v >> 1, 0), bit(v, 0)))
        v = h(bv2i(bit(x, 3), bit(x, 2), bit(x, 1), bit(v >> 1, 0), bit(v, 0)))
        t = fg(bv2i(bit(x, 0), bit(v >> 1, 0), bit(v, 0))) ^ (s & 3)
        
        s = (s >> 2) | (t << 38)
        kl = lfsr_round(kl)
        kr = lfsr_round(kr)
    return s & 0xFFFFFF

# --- LOGIQUE DE GENERATION ---

def construct_kr(kl):
    """Construit KR à partir de KL selon le masque de symétrie (255-octet)"""
    octets_kl = [(kl >> (i * 8)) & 0xFF for i in range(5)]
    octets_kr = [(255 - x) for x in octets_kl]
    kr = 0
    for i, x in enumerate(octets_kr):
        kr |= (x << (i * 8))
    return kr

def main():
    parser = argparse.ArgumentParser(description="Générateur de réponse signée DST80")
    parser.add_argument("--kl", type=lambda x: int(x, 16), default=0xfd4aedd12f, help="KeyL en Hex (défaut: fd4aedd12f)")
    parser.add_argument("--challenge", type=lambda x: int(x, 16), default=0x7465736c61, help="Challenge en Hex (défaut: 7465736c61)")
    
    args = parser.parse_args()

    # 1. Calcul de KR
    kr = construct_kr(args.kl)
    
    # 2. Simulation
    response = simulate_dst80(args.kl, kr, args.challenge)

    print(f"[bold blue]--- DST80 Signature Generator ---[/bold blue]")
    print(f"KeyL:       [green]0x{args.kl:010x}[/green]")
    print(f"KeyR (gen): [green]0x{kr:010x}[/green]")
    print(f"Challenge:  [cyan]0x{args.challenge:010x}[/cyan]")
    print(f"----------------------------------")
    print(f"RESPONSE:   [bold yellow]0x{response:06x}[/bold yellow]")

if __name__ == "__main__":
    main()
