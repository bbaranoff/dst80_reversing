# DST80 Reversing & Brute-force Suite

This project provides a high-performance implementation for recovering **TI DST80** (Digital Signature Transponder) keys using OpenCL. It is designed to demonstrate how architectural weaknesses and constructor-specific constants can reduce the theoretical 80-bit security margin to a practical brute-force attack.

## The Theory: Why it is breakable

The DST80 algorithm uses an 80-bit key, traditionally split into two 40-bit halves:  (Key Left) and  (Key Right). However, in many automotive and RFID implementations, the entropy is significantly lower:

* **Symmetry Constraint:** The keys are often generated such that the 3 bytes on the left are a mask/inverse of the 3 bytes on the right (). This immediately divides the search space by two.
* **Constructor Constants:** Out of the 80 bits, roughly **32 bits** are often fixed "constructor constants."
* **Reduced Search Space:** By combining these factors, the complexity drops from  to approximately  or  (depending on the known constants).

### Performance & Strategy (IACR Method)

As described in research papers [![IACR TCHES - Dismantling DST80](https://img.shields.io/badge/IACR_TCHES-Dismantling_DST80-blue?style=for-the-badge&logo=read-the-docs)](https://tches.iacr.org/index.php/TCHES/article/view/8546), the attack follows a tiered approach:

![IACR Algorithm](iacr.png)

1. **Unknown Constants:** On a budget GPU (like an NVIDIA RTX 3050 Ti), recovering a full key with one unknown byte takes about **300 minutes (5 hours)**.
2. **Known Constants:** Once the constructor constants are identified, the search space is reduced to 1 minute.
3. **Cross-Constructor:** If the constructor changes, we reiterate the process once to extract the new constants, then return to 1-minute recovery times.

---

## Hardware Requirements

* **GPU:** Any OpenCL-compatible GPU (NVIDIA, AMD, Intel).
* **Tested On:** NVIDIA GeForce RTX 3050 Ti Laptop GPU.
* **Performance:** ~35 Mkeys/s.

---

## Project Structure

| File | Description |
| --- | --- |
| `dst80_fast.py` | Optimized search using a fixed constructor byte (`0x2f`). |
| `dst80_constructor.py` | Allows passing two specific constructor bytes (`m2`, `m1`) as arguments. |
| `dst80_reverse.py` | Full range search (up to 5 bytes) to identify unknown constructor constants. |
| `*.cl` | OpenCL kernels containing the DST80 cipher simulation logic. |

---

## Usage

### 1. Installation

```bash
pip install -r requirements.txt

```

### 2. Fast Search (Known 1-byte constant)

If you know the suffix (e.g., `0x2f`), use the fast script:

```bash
python dst80_fast.py <c1> <t1> <c2> <t2>

```

### 3. Constructor Search (Known 2-byte constants)

To test specific constructor bytes (e.g., `d1 2f`):

```bash
python dst80_constructor.py <c1> <t1> <c2> <t2> d1 2f

```

### 4. Full Reverse (Discovery Mode)

To search the full space (5 bytes variable) to find the constants:

```bash
python dst80_reverse.py <c1> <t1> <c2> <t2> 4228250625

```

---

## Demo

Below is a successful recovery of a key using the dual-challenge method.

**Next Step:** Would you like me to refine the technical explanation of the bit-masking logic between KL and KR in the "The Theory" section?

![Search Demo](demo.png)
