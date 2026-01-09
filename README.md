# DST80 Reversing & Brute-force Suite

Based on DST80 (non reversed) found here [![Gist - DST80 Reference](https://img.shields.io/badge/Gist-DST80_Reference-lightgrey?style=for-the-badge&logo=github)](https://gist.github.com/rqu1/f236b68a2b3efd9b22eacd3f7003cd15)


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

![Search Demo](demo.png)

### Key Symmetry & Masking Logic

The core of this brute-force efficiency lies in the relationship between the Left Key () and Right Key (). In the target implementations, these two 40-bit halves are not independent. They are constructed as a **mirrored mask** of each other.

To successfully recover the key, the tool reconstructs the 80-bit space by generating  as a transformation of  for every attempt:

1. ** Generation:** We iterate through the unknown bytes (e.g., `i, j, k, l`) and append the known constructor bytes (e.g., `m`).
2. ** Mirroring:** For each byte in , the corresponding byte in  is calculated as `255 - byte` (a bitwise NOT in the 8-bit range).

**Why this is mandatory:**
If you attempt to brute-force  and  as independent 40-bit values, the search space becomes , which is cryptographically secure. By enforcing this **Constructor Masking** during the search, we align with the manufacturer's internal key generation logic, collapsing the search space to a manageable  or  range.

