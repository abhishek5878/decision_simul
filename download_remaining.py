from huggingface_hub import hf_hub_download
import os

# Download the remaining files individually with better error handling
repo_id = "nvidia/Nemotron-Personas-India"
local_dir = "./nemotron_personas_india_data/data"

# List of all expected files based on the pattern
expected_files = {
    'en_IN': 11,
    'hi_Deva_IN': 26,
    'hi_Latn_IN': 12
}

print("Checking for missing files...")
missing = []

for lang, total in expected_files.items():
    for i in range(total):
        filename = f"{lang}-{i:05d}-of-{total:05d}.parquet"
        filepath = os.path.join(local_dir, filename)
        if not os.path.exists(filepath):
            missing.append(f"data/{filename}")
            print(f"  Missing: {filename}")

if not missing:
    print("\n✓ All parquet files are present!")
else:
    print(f"\n{len(missing)} files missing. Downloading them now...")
    
    for file_path in missing:
        try:
            print(f"\nDownloading {file_path}...")
            hf_hub_download(
                repo_id=repo_id,
                filename=file_path,
                repo_type="dataset",
                local_dir="./nemotron_personas_india_data",
                local_dir_use_symlinks=False
            )
            print(f"  ✓ Downloaded {file_path}")
        except Exception as e:
            print(f"  ✗ Failed to download {file_path}: {e}")

print("\n" + "="*60)
print("Checking final status...")
os.system(f"ls {local_dir}/*.parquet | wc -l")
os.system(f"du -sh {local_dir}")


