import os
import sys
import numpy as np
import pyopencl as cl
import argparse
import time
from tqdm import tqdm

# Éviter que PyOpenCL ne charge ses types trop tôt
os.environ["PYOPENCL_NO_CACHE"] = "1"

def run_search(c1, t1, c2, t2, max_keys):
    # Sélection automatique du GPU NVIDIA
    platforms = cl.get_platforms()
    dev = None
    for p in platforms:
        if "NVIDIA" in p.name:
            dev = p.get_devices()[0]
            break
    if not dev: dev = platforms[0].get_devices()[0]

    ctx = cl.Context([dev])
    queue = cl.CommandQueue(ctx)
    
    # Chargement du Kernel
    if not os.path.exists("dst80_kernel.cl"):
        print("Erreur: dst80_kernel.cl non trouvé.")
        return

    with open("dst80_kernel.cl", "r") as f:
        kernel_src = f.read()
    
    # Compilation
    prg = cl.Program(ctx, kernel_src).build()

    # --- ÉTAPE 1 : Créer l'objet Kernel explicitement une seule fois ---
    knl = cl.Kernel(prg, "dst80_search")

    # Buffers
    h_count = np.zeros(1, dtype=np.uint32)
    h_matches = np.zeros(200, dtype=np.uint64)
    
    # ... (buffers mémoire identiques)
    mf = cl.mem_flags
    d_count = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=h_count)
    d_matches = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=h_matches)

    chunk_size = 1 << 20 
    
    print(f"--- SDR Search (Dual Challenge) : {dev.name} ---")
    start_time = time.time()
    
    pbar = tqdm(total=max_keys, unit="keys")
    
    for base in range(0, max_keys, chunk_size):
        current_chunk = min(chunk_size, max_keys - base)
        
        # --- ÉTAPE 2 : Utiliser 'knl' au lieu de 'prg.dst80_search' ---
        knl(queue, (current_chunk,), None, 
            np.uint64(base), 
            np.uint64(c1), np.uint32(t1),
            np.uint64(c2), np.uint32(t2),
            d_matches, d_count)
        
        pbar.update(current_chunk)
            
    queue.finish()
    pbar.close()

    cl.enqueue_copy(queue, h_count, d_count)
    cl.enqueue_copy(queue, h_matches, d_matches)

    end_time = time.time()
    speed = (max_keys / (end_time - start_time)) / 1e6
    print(f"\nTerminé en {end_time - start_time:.2f}s ({speed:.2f} Mkeys/s)")

    if h_count[0] > 0:
        print(f"\n--- {h_count[0]} MATCH(S) TROUVÉ(S) ---")
        for i in range(int(h_count[0])):
            print(f"Key Pair {i+1}:")
            print(f"  KL: 0x{h_matches[i*2]:010x}")
            print(f"  KR: 0x{h_matches[i*2+1]:010x}")
    else:
        print("\nAucun match trouvé.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recherche DST80 avec élimination des faux positifs.")
    parser.add_argument("c1", type=lambda x: int(x, 16), help="Challenge 1 en Hex (ex: 0123456789)")
    parser.add_argument("t1", type=lambda x: int(x, 16), help="Target 1 en Hex (ex: ABCDEF)")
    parser.add_argument("c2", type=lambda x: int(x, 16), help="Challenge 2 en Hex")
    parser.add_argument("t2", type=lambda x: int(x, 16), help="Target 2 en Hex")
    parser.add_argument("max_keys", type=int, help="Nombre total de clés à tester")
    
    args = parser.parse_args()
    
    run_search(args.c1, args.t1, args.c2, args.t2, args.max_keys)
