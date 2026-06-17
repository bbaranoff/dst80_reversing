import os
import numpy as np
import pyopencl as cl
import argparse
import time
from tqdm import tqdm
import warnings
from pyopencl import CompilerWarning

warnings.filterwarnings("ignore", category=CompilerWarning)
os.environ["PYOPENCL_NO_CACHE"] = "1"

def run_search(serial, ch1, tg1, ch2, tg2, max_keys):
    platforms = cl.get_platforms()
    dev = next((p.get_devices()[0] for p in platforms if "NVIDIA" in p.name),
               platforms[0].get_devices()[0])
    ctx = cl.Context([dev])
    queue = cl.CommandQueue(ctx)

    with open("dst80_constants.cl", "r") as f:
        kernel_src = f.read()

    prg = cl.Program(ctx, kernel_src).build()
    knl = cl.Kernel(prg, "dst80_search")

    h_count = np.zeros(1, dtype=np.uint32)
    h_matches = np.zeros(300, dtype=np.uint64)  # 100 matches x (constantes, kl, kr)
    mf = cl.mem_flags
    d_count = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=h_count)
    d_matches = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=h_matches)

    chunk_size = 1 << 18
    print(f"Recherche des constantes constructeur (serial=0x{serial:010x}) sur GPU : {dev.name}")
    start = time.time()
    pbar = tqdm(total=max_keys, unit="keys")
    for base in range(0, max_keys, chunk_size):
        cur = min(chunk_size, max_keys - base)
        knl(queue, (cur,), None,
            np.uint64(serial), np.uint64(base),
            np.uint64(ch1), np.uint32(tg1),
            np.uint64(ch2), np.uint32(tg2),
            d_matches, d_count)
        pbar.update(cur)
    queue.finish()
    pbar.close()
    cl.enqueue_copy(queue, h_count, d_count)
    cl.enqueue_copy(queue, h_matches, d_matches)

    elapsed = time.time() - start
    print(f"\nTermine en {elapsed:.2f}s ({max_keys/elapsed/1e6:.2f} Mkeys/s)")

    if h_count[0] > 0:
        print(f"\n{h_count[0]} MATCH(S) TROUVE(S) !!!")
        for i in range(int(h_count[0])):
            consts = int(h_matches[i*3 + 0])
            kl     = int(h_matches[i*3 + 1])
            kr     = int(h_matches[i*3 + 2])
            b0 = consts & 0xFF
            b1 = (consts >> 8) & 0xFF
            b2 = (consts >> 16) & 0xFF
            print(f"Match {i+1}: constantes c0=0x{b0:02x} c1=0x{b1:02x} c2=0x{b2:02x} "
                  f"| kl=0x{kl:010x} kr=0x{kr:010x}")
    else:
        print("\nAucun match trouve :(.")

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="DST80 - recherche des constructor constants (serial public connu)")
    p.add_argument("serial", type=lambda x: int(x, 16), help="Serial PUBLIC du transpondeur (hex)")
    p.add_argument("c1", type=lambda x: int(x, 16), help="Challenge 1 (hex)")
    p.add_argument("t1", type=lambda x: int(x, 16), help="Reponse 1 (hex)")
    p.add_argument("c2", type=lambda x: int(x, 16), help="Challenge 2 (hex)")
    p.add_argument("t2", type=lambda x: int(x, 16), help="Reponse 2 (hex)")
    p.add_argument("max_keys", type=int, nargs='?', default=16777216,  # 2^24
                   help="Taille de l'espace de constantes (defaut 2^24 = 3 octets)")
    a = p.parse_args()
    run_search(a.serial, a.c1, a.t1, a.c2, a.t2, a.max_keys)
