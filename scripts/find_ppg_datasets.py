"""
Script to explore available PhysioNet PPG datasets.
Run this in your Vertex AI notebook to find accessible data.
"""

import wfdb

# List all available PhysioNet databases
print("=" * 70)
print("AVAILABLE PHYSIONET DATABASES")
print("=" * 70)

try:
    dbs = wfdb.get_dbs()
    
    # Filter for PPG-related databases
    ppg_keywords = ['ppg', 'pulse', 'pleth', 'oxim', 'spo2', 'wearable', 'vital']
    
    print("\n--- Potentially PPG-Related Databases ---\n")
    
    for db in dbs:
        db_name = db[0].lower()
        db_desc = db[1] if len(db) > 1 else ""
        
        if any(kw in db_name or kw in db_desc.lower() for kw in ppg_keywords):
            print(f"  {db[0]}")
            print(f"    {db_desc[:80]}...")
            print()
    
    print("\n--- All Databases (first 50) ---\n")
    for db in dbs[:50]:
        print(f"  {db[0]}: {db[1][:60] if len(db) > 1 else 'No description'}...")

except Exception as e:
    print(f"Error listing databases: {e}")

print("\n" + "=" * 70)
print("To load a specific database, try:")
print("  wfdb.get_record_list('database-name')")
print("=" * 70)
