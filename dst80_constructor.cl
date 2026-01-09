#pragma OPENCL EXTENSION cl_khr_global_int32_base_atomics : enable

#define BIT(x,n)             (((x)>>(n)) & 1UL)
#define BIT_SLICE(x,msb,lsb) (((x)&(((1UL<<((msb)+1))-1UL)))>>(lsb))
#define BV2I5(b4,b3,b2,b1,b0) (((b4)<<4)|((b3)<<3)|((b2)<<2)|((b1)<<1)|(b0))
#define BV2I4(b3,b2,b1,b0)    (((b3)<<3)|((b2)<<2)|((b1)<<1)|(b0))
#define KEY_MASK              ((1UL<<39) - 1UL)

static inline uint fa(uint x){ return BIT(0x3A35ACC5UL, x); }
static inline uint fb(uint x){ return BIT(0xAC35742EUL, x); }
static inline uint fc(uint x){ return BIT(0xB81D8BD1UL, x); }
static inline uint fd(uint x){ return BIT(0x5ACC335AUL, x); }
static inline uint fe(uint x){ return BIT(0xE247UL,     x); }
static inline uint fg(uint x){ return BIT(0x4E72UL,    x); }
static inline uint h(uint x) { return (0x1F9826F4UL >> (2*(x))) & 3UL; }

static inline uint f_func(ulong k, ulong s){
    uint fs[16];
    fs[ 0]=fd(BV2I5(BIT(s,32),BIT(k,32),BIT(s,24),BIT(k,24),BIT(s,16)));
    fs[ 1]=fe(BV2I4(BIT(k,16),BIT(s,8),BIT(k,8),BIT(k,0)));
    fs[ 2]=fb(BV2I5(BIT(s,33),BIT(k,33),BIT(s,25),BIT(k,25),BIT(s,17)));
    fs[ 3]=fe(BV2I4(BIT(k,17),BIT(s,9),BIT(k,9),BIT(k,1)));
    fs[ 4]=fd(BV2I5(BIT(s,34),BIT(k,34),BIT(s,26),BIT(k,26),BIT(s,18)));
    fs[ 5]=fc(BV2I5(BIT(k,18),BIT(s,10),BIT(k,10),BIT(s,2),BIT(k,2)));
    fs[ 6]=fb(BV2I5(BIT(s,35),BIT(k,35),BIT(s,27),BIT(k,27),BIT(s,19)));
    fs[ 7]=fa(BV2I5(BIT(k,19),BIT(s,11),BIT(k,11),BIT(s,3),BIT(k,3)));
    fs[ 8]=fd(BV2I5(BIT(s,36),BIT(k,36),BIT(s,28),BIT(k,28),BIT(s,20)));
    fs[ 9]=fc(BV2I5(BIT(k,20),BIT(s,12),BIT(k,12),BIT(s,4),BIT(k,4)));
    fs[10]=fb(BV2I5(BIT(s,37),BIT(k,37),BIT(s,29),BIT(k,29),BIT(s,21)));
    fs[11]=fa(BV2I5(BIT(k,21),BIT(s,13),BIT(k,13),BIT(s,5),BIT(k,5)));
    fs[12]=fd(BV2I5(BIT(s,38),BIT(k,38),BIT(s,30),BIT(k,30),BIT(s,22)));
    fs[13]=fc(BV2I5(BIT(k,22),BIT(s,14),BIT(k,14),BIT(s,6),BIT(k,6)));
    fs[14]=fb(BV2I5(BIT(s,39),BIT(k,39),BIT(s,31),BIT(k,31),BIT(s,23)));
    fs[15]=fa(BV2I5(BIT(k,23),BIT(s,15),BIT(k,15),BIT(s,7),BIT(k,7)));
    
    uint gb0 = fg(BV2I4(fs[3], fs[2], fs[1], fs[0]));
    uint gb1 = fg(BV2I4(fs[7], fs[6], fs[5], fs[4]));
    uint gb2 = fg(BV2I4(fs[11],fs[10],fs[9], fs[8]));
    uint gb3 = fg(BV2I4(fs[15],fs[14],fs[13],fs[12]));
    return h(BV2I4(gb0,gb1,gb2,gb3));
}

static inline ulong p2_fast(ulong x){
    ulong fixed = x & 0xA5A5A5A5A5UL;
    ulong b6 = (x >> 6) & 0x0101010101UL;
    ulong b4 = (x >> 4) & 0x0101010101UL;
    ulong b3 = (x >> 3) & 0x0101010101UL;
    ulong b1 = (x >> 1) & 0x0101010101UL;
    return fixed | (b6 << 3) | (b4 << 1) | (b3 << 6) | (b1 << 4);
}

static inline ulong lfsr_round(ulong x){
    uint feedback = (BIT(x,0)^BIT(x,2)^BIT(x,19)^BIT(x,21))&1UL;
    return (x>>1)|((ulong)feedback<<39);
}

static inline ulong simulate_dst80(ulong kl, ulong kr, ulong challenge) {
    ulong s = challenge;
    for(int r=0; r<200; r++){
        ulong ml = p2_fast(kl);
        if(ml & (1UL << 39)) ml ^= KEY_MASK;
        ulong mr = p2_fast(kr); 
        if(mr & (1UL << 39)) mr ^= KEY_MASK;
        ulong key_merged = ((BIT_SLICE(ml,39,20)<<20)|BIT_SLICE(mr,39,20));
        uint t = f_func(key_merged, s) ^ (s & 3UL);
        s = (s >> 2) | ((ulong)t << 38);
        kr = lfsr_round(kr);
        kl = lfsr_round(kl);
    }
    return s;
}

// ... (garder tout le début du kernel identique jusqu'à dst80_search)

__kernel void dst80_search(
    const ulong global_base,
    const ulong challenge1,
    const uint target1,
    const ulong challenge2,
    const uint target2,
    __global ulong* out_matches,
    __global uint* out_count
){
    size_t gid = get_global_id(0);
    ulong idx = global_base + gid;

    // Valeurs injectées par le script Python
    ulong m1 = 0x2f; // Sera remplacé par le dernier octet (ex: 2f)
    ulong m2 = 0x00; // Sera remplacé par l'avant-dernier (ex: d1)

    // Indexation pour les 3 octets restants (i, j, k)
    ulong i = idx % 255;
    ulong j = (idx / 255) % 255;
    ulong k = (idx / 65025) % 255;

    // Reconstruction exacte : [i][j][k][m2][m1] -> [fd][4a][ed][d1][2f]
    ulong kl_orig = (i << 32) | (j << 24) | (k << 16) | (m2 << 8) | m1;
    
    // KR doit suivre la même symétrie inverse
    ulong kr_orig = (((255 - m1) << 32) | ((255 - m2) << 24) | ((255 - k) << 16) | ((255 - j) << 8) | (255 - i));
    // Simulation
    ulong res1 = simulate_dst80(kl_orig, kr_orig, challenge1);
    if ((uint)(res1 & 0xFFFFFFUL) == target1) {
        ulong res2 = simulate_dst80(kl_orig, kr_orig, challenge2);
        if ((uint)(res2 & 0xFFFFFFUL) == target2) {
            uint pos = atomic_inc(out_count);
            if (pos < 100) {
                out_matches[pos * 2] = kl_orig;
                out_matches[pos * 2 + 1] = kr_orig;
            }
        }
    }
}
