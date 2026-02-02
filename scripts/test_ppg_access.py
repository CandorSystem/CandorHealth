"""
Test access to various PhysioNet PPG datasets.
Run this in Vertex AI notebook to find what data you can actually access.
"""

import wfdb
import numpy as np

print("=" * 70)
print("TESTING PHYSIONET PPG DATA ACCESS")
print("=" * 70)

# Known PPG-containing databases to try
datasets_to_try = [
    # Public PPG datasets
    ("mimic3wdb-matched/1.0/p00/p000020", "83404", "MIMIC-III Waveform (matched)"),
    ("bidmc-ppg-and-respiration-dataset/1.0.0", "bidmc01", "BIDMC PPG"),
    ("but-ppg/1.0.0", "01", "BUT PPG"),
    ("pulse-transit-time-ppg/1.0.0", "s1_walk", "Pulse Transit Time PPG"),
    ("wrist-ppg-during-exercise/1.0.0", "s1_run", "Wrist PPG Exercise"),
    ("vortal/1.0.0", "Case01", "VORTAL"),
    
    # MIMIC databases (may require credentials)
    ("mimic4wdb/0.1.0/waves/p100/p10014354/81739927", "81739927", "MIMIC-IV Waveform"),
    
    # Capnobase
    ("capnobase/1.0.0", "0009_8min", "CapnoBase"),
]

print("\nTrying to access various datasets...\n")

accessible = []
need_credentials = []
not_found = []

for pn_dir, record_name, description in datasets_to_try:
    try:
        print(f"Trying: {description}")
        print(f"  Path: {pn_dir}/{record_name}")
        
        # Try to read the record
        record = wfdb.rdrecord(record_name, pn_dir=pn_dir)
        
        print(f"  ✓ SUCCESS!")
        print(f"    Signals: {record.sig_name}")
        print(f"    Sample rate: {record.fs} Hz")
        print(f"    Duration: {record.sig_len / record.fs:.1f} seconds")
        
        # Check for PPG/PLETH signal
        ppg_channels = [i for i, name in enumerate(record.sig_name) 
                       if 'ppg' in name.lower() or 'pleth' in name.lower()]
        if ppg_channels:
            print(f"    PPG channel(s): {[record.sig_name[i] for i in ppg_channels]}")
        
        accessible.append((pn_dir, record_name, description, record.sig_name))
        print()
        
    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "credential" in error_str.lower():
            print(f"  ⚠ Requires credentials")
            need_credentials.append((pn_dir, record_name, description))
        elif "404" in error_str:
            print(f"  ✗ Not found (path may have changed)")
            not_found.append((pn_dir, record_name, description))
        else:
            print(f"  ✗ Error: {error_str[:50]}")
            not_found.append((pn_dir, record_name, description))
        print()

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"\n✓ Accessible ({len(accessible)}):")
for pn_dir, record, desc, signals in accessible:
    print(f"  - {desc}: {signals}")

print(f"\n⚠ Need Credentials ({len(need_credentials)}):")
for pn_dir, record, desc in need_credentials:
    print(f"  - {desc}")

print(f"\n✗ Not Found ({len(not_found)}):")
for pn_dir, record, desc in not_found:
    print(f"  - {desc}")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("""
For datasets requiring credentials:
1. Go to https://physionet.org/
2. Create an account
3. Complete the credentialing process
4. Accept the data use agreement for specific datasets

For MIMIC data specifically:
1. Complete CITI training
2. Sign data use agreement
3. Use your credentials when accessing data
""")
