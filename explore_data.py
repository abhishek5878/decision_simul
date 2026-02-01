import pandas as pd
import glob
import os

print("Exploring Nemotron-Personas-India dataset")
print("=" * 60)

# Find all parquet files
data_dir = "./nemotron_personas_india_data/data"
parquet_files = sorted(glob.glob(f"{data_dir}/*.parquet"))

print(f"\nTotal files: {len(parquet_files)}")
print(f"Data size: ", end="")
os.system(f"du -sh {data_dir}")

# Group by language
languages = {}
for f in parquet_files:
    basename = os.path.basename(f)
    lang = basename.split('-')[0]
    if lang not in languages:
        languages[lang] = []
    languages[lang].append(f)

print(f"\nLanguages found: {list(languages.keys())}")
for lang, files in languages.items():
    print(f"  {lang}: {len(files)} files")

# Load and preview first file from each language
print("\n" + "=" * 60)
print("SAMPLE DATA FROM EACH LANGUAGE:")
print("=" * 60)

for lang in languages.keys():
    print(f"\n### {lang} ###")
    df = pd.read_parquet(languages[lang][0])
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst example:")
    print("-" * 60)
    for col in df.columns:
        val = df.iloc[0][col]
        if isinstance(val, str) and len(val) > 200:
            print(f"{col}: {val[:200]}...")
        else:
            print(f"{col}: {val}")
    print()

print("\n" + "=" * 60)
print("✓ Dataset exploration complete!")


