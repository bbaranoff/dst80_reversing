import os
import numpy as np
import pyopencl as cl
import argparse
import time
from tqdm import tqdm
import warnings
from pyopencl import CompilerWarning

# À placer au début de ton script
warnings.filterwarnings("ignore", category=CompilerWarning)

os.environ["PYOPENCL_NO_CACHE"] = "1"

def run_constructor_search(c1, t1, c2, t2, m1, m2):
    platforms = cl.get_platforms()
    dev = next((p.get_devices()[0] for p in platforms if "NVIDIA" in p.name), platforms[0].get_devices()[0])
    ctx = cl.Context([dev])
    queue = cl.CommandQueue(ctx)
    
    with open("dst80_constructor.cl", "r") as f:
        kernel_src = f.read()
    
    # Remplacement précis des constantes dans le code source du kernel
    kernel_mod = kernel_src.replace("ulong m1 = 0x2f;", f"ulong m1 = 0x{m1:02x};")
    kernel_mod = kernel_mod.replace("ulong m2 = 0x00;", f"ulong m2 = 0x{m2:02x};")
    
    prg = cl.Program(ctx, kernel_mod).build()
    knl = cl.Kernel(prg, "dst80_search")

    h_count = np.zeros(1, dtype=np.uint32)
    h_matches = np.zeros(200, dtype=np.uint64)
    mf = cl.mem_flags
    d_count = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=h_count)
    d_matches = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=h_matches)

    # Espace de recherche : 255^3
    max_keys = 16581375 
    chunk_size = 1 << 18 
    
    print(f"Bruteforce with softcoded constructor bytes (m2=0x{m2:02x}, m1=0x{m1:02x}) and GPU : {dev.name}")
    start_time = time.time()
    pbar = tqdm(total=max_keys, unit="keys")
    
    for base in range(0, max_keys, chunk_size):
        current_chunk = min(chunk_size, max_keys - base)
        knl(queue, (current_chunk,), None, 
            np.uint64(base), np.uint64(c1), np.uint32(t1),
            np.uint64(c2), np.uint32(t2), d_matches, d_count)
        pbar.update(current_chunk)
            
    queue.finish()
    pbar.close()
    cl.enqueue_copy(queue, h_count, d_count)
    cl.enqueue_copy(queue, h_matches, d_matches)

    if h_count[0] > 0:
        print(f"\n{h_count[0]} MATCH(S) TROUVÉ(S) !!!")
        for i in range(int(h_count[0])):
            print(f"Match {i+1}: kl=0x{h_matches[i*2]:010x}, kr=0x{h_matches[i*2+1]:010x}")
    else:
        print("\nAucun match :(.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("c1", type=lambda x: int(x, 16))
    parser.add_argument("t1", type=lambda x: int(x, 16))
    parser.add_argument("c2", type=lambda x: int(x, 16))
    parser.add_argument("t2", type=lambda x: int(x, 16))
    parser.add_argument("m2", type=lambda x: int(x, 16), help="Avant-dernier octet (d1)")
    parser.add_argument("m1", type=lambda x: int(x, 16), help="Dernier octet (2f)")
    args = parser.parse_args()
    
    # Correction de l'ordre ici : m1 pour m1, m2 pour m2
    run_constructor_search(args.c1, args.t1, args.c2, args.t2, args.m1, args.m2)
