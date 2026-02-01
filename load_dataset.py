"""
load_dataset.py - Dataset loading and sampling for Credigo.club Audience Simulation Engine

This module handles:
1. Loading the Nemotron-Personas-India dataset from Hugging Face
2. Random sampling of N personas (default 1000) with reproducibility
3. Data validation and basic preprocessing

Dataset: NVIDIA Nemotron-Personas-India
- 3M total personas (1M English, 1M Hindi Devanagari, 1M Hindi Latin)
- 28 fields covering demographics, geography, interests, and rich persona descriptions

For Credigo.club simulation, we use the English (en_IN) split for clarity in analysis.

Uses Hugging Face datasets library to load the full dataset directly.
"""

import pandas as pd
import glob
import os
import random
from typing import Optional, List, Tuple
import warnings

try:
    from datasets import load_dataset as hf_load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    warnings.warn(
        "Hugging Face datasets library not available. Install with: pip install datasets\n"
        "Falling back to local parquet file loading."
    )

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = "./nemotron_personas_india_data/data"
DEFAULT_SAMPLE_SIZE = 1000
DEFAULT_RANDOM_SEED = 42  # For reproducibility

# Language prefixes in the dataset
LANGUAGE_CONFIGS = {
    "en_IN": "English (India)",
    "hi_Deva_IN": "Hindi (Devanagari)",
    "hi_Latn_IN": "Hindi (Latin/Romanized)"
}

# All 28 fields in the dataset schema
EXPECTED_COLUMNS = [
    'uuid',
    # Persona aspects (7 types of personas)
    'professional_persona', 'linguistic_persona', 'sports_persona',
    'arts_persona', 'travel_persona', 'culinary_persona', 'persona',
    # Background & skills
    'cultural_background', 'linguistic_background',
    'skills_and_expertise', 'skills_and_expertise_list',
    # Interests & goals
    'hobbies_and_interests', 'hobbies_and_interests_list',
    'career_goals_and_ambitions',
    # Demographics
    'sex', 'age', 'marital_status', 'education_level', 'education_degree', 'occupation',
    # Languages
    'first_language', 'second_language', 'third_language',
    # Geography
    'zone', 'state', 'district', 'country'
]


# ============================================================================
# CORE LOADING FUNCTIONS
# ============================================================================

def get_parquet_files(data_dir: str = DATA_DIR, language: str = "en_IN") -> List[str]:
    """
    Get all parquet files for a specific language split.
    
    Args:
        data_dir: Directory containing parquet files
        language: Language split prefix ('en_IN', 'hi_Deva_IN', 'hi_Latn_IN')
    
    Returns:
        Sorted list of parquet file paths
    """
    pattern = os.path.join(data_dir, f"{language}-*.parquet")
    files = sorted(glob.glob(pattern))
    
    if not files:
        raise FileNotFoundError(
            f"No parquet files found for language '{language}' in {data_dir}. "
            f"Expected pattern: {pattern}"
        )
    
    return files


def load_full_dataset(
    data_dir: str = DATA_DIR,
    language: str = "en_IN",
    columns: Optional[List[str]] = None,
    verbose: bool = True,
    use_huggingface: bool = True
) -> pd.DataFrame:
    """
    Load the complete dataset for a given language split.
    
    For 1M+ records, this uses Hugging Face datasets library for efficient loading.
    Falls back to local parquet files if Hugging Face is not available.
    
    Args:
        data_dir: Directory containing parquet files (fallback only)
        language: Language split to load ('en_IN', 'hi_Deva_IN', 'hi_Latn_IN')
        columns: Specific columns to load (None = all columns)
        verbose: Print loading progress
        use_huggingface: Whether to use Hugging Face datasets library (default True)
    
    Returns:
        Complete DataFrame with all records
    """
    # Try Hugging Face first if available and requested
    if use_huggingface and HF_AVAILABLE:
        try:
            if verbose:
                print(f"📂 Loading {LANGUAGE_CONFIGS.get(language, language)} dataset from Hugging Face...")
                print(f"   Dataset: nvidia/Nemotron-Personas-India")
                print(f"   Split: {language}")
            
            # Load dataset from Hugging Face
            # The dataset uses language as the split name, not config
            if verbose:
                print(f"   Downloading dataset from Hugging Face (this may take a few minutes)...")
                print(f"   Progress will be shown below:")
            
            # Load with progress tracking
            # The datasets library automatically shows download progress bars
            from datasets import DownloadConfig
            from tqdm import tqdm
            
            # Configure download with progress tracking
            download_config = DownloadConfig(
                resume_download=True,
                max_retries=3
            )
            
            if verbose:
                print(f"   ⏳ Downloading dataset (the datasets library will show progress bars)...")
                print(f"   📊 You'll see download percentages automatically displayed below:")
                print()
            
            dataset = hf_load_dataset(
                "nvidia/Nemotron-Personas-India", 
                split=language,
                download_config=download_config
            )
            
            if verbose:
                print(f"   ✅ Loaded {len(dataset):,} personas from Hugging Face")
            
            # Convert to pandas DataFrame
            # For large datasets, convert in chunks to avoid memory issues
            if len(dataset) > 100000:
                if verbose:
                    print(f"   Converting to pandas DataFrame (large dataset, this may take a moment)...")
                
                # Convert in batches
                batch_size = 100000
                dfs = []
                for i in range(0, len(dataset), batch_size):
                    batch = dataset.select(range(i, min(i + batch_size, len(dataset))))
                    batch_df = batch.to_pandas()
                    if columns:
                        batch_df = batch_df[columns]
                    dfs.append(batch_df)
                    if verbose and (i + batch_size) % 500000 == 0:
                        print(f"   Converted {min(i + batch_size, len(dataset)):,} / {len(dataset):,} records")
                
                full_df = pd.concat(dfs, ignore_index=True)
            else:
                full_df = dataset.to_pandas()
                if columns:
                    full_df = full_df[columns]
            
            if verbose:
                print(f"✅ Loaded {len(full_df):,} total personas")
                print(f"   Columns: {len(full_df.columns)}")
                mem_mb = full_df.memory_usage(deep=True).sum() / (1024 * 1024)
                print(f"   Memory usage: {mem_mb:.1f} MB")
            
            return full_df
            
        except Exception as e:
            if verbose:
                print(f"⚠️  Warning: Failed to load from Hugging Face: {e}")
                print(f"   Falling back to local parquet files...")
            # Fall through to local file loading
    
    # Fallback to local parquet files
    if verbose:
        print(f"📂 Loading {LANGUAGE_CONFIGS.get(language, language)} dataset from local files...")
    
    files = get_parquet_files(data_dir, language)
    
    if verbose:
        print(f"   Found {len(files)} parquet file(s)")
    
    # Load all parquet files
    dfs = []
    total_rows = 0
    
    for i, file in enumerate(files):
        try:
            df = pd.read_parquet(file, columns=columns)
            dfs.append(df)
            total_rows += len(df)
            
            if verbose and (i + 1) % 3 == 0:
                print(f"   Loaded {i + 1}/{len(files)} files ({total_rows:,} rows)")
        except Exception as e:
            warnings.warn(f"Error loading {file}: {e}")
            continue
    
    if not dfs:
        raise RuntimeError("Failed to load any parquet files")
    
    # Concatenate all DataFrames
    full_df = pd.concat(dfs, ignore_index=True)
    
    if verbose:
        print(f"✅ Loaded {len(full_df):,} total personas")
        print(f"   Columns: {len(full_df.columns)}")
        mem_mb = full_df.memory_usage(deep=True).sum() / (1024 * 1024)
        print(f"   Memory usage: {mem_mb:.1f} MB")
    
    return full_df


def sample_personas(
    df: pd.DataFrame,
    n: int = DEFAULT_SAMPLE_SIZE,
    seed: int = DEFAULT_RANDOM_SEED,
    stratify_by: Optional[str] = None
) -> pd.DataFrame:
    """
    Randomly sample N personas from the dataset with reproducibility.
    
    Args:
        df: Full dataset DataFrame
        n: Number of personas to sample
        seed: Random seed for reproducibility
        stratify_by: Optional column for stratified sampling (e.g., 'zone', 'state')
    
    Returns:
        Sampled DataFrame with n rows
    """
    # Ensure we don't try to sample more than available
    n = min(n, len(df))
    
    if stratify_by and stratify_by in df.columns:
        # Stratified sampling - maintain proportions by group
        # Use random seed for reproducibility
        random.seed(seed)
        
        sampled_dfs = []
        group_counts = df[stratify_by].value_counts(normalize=True)
        
        for group, proportion in group_counts.items():
            group_df = df[df[stratify_by] == group]
            group_n = max(1, int(n * proportion))  # At least 1 per group
            sample_n = min(group_n, len(group_df))
            sampled_dfs.append(group_df.sample(n=sample_n, random_state=seed))
        
        sampled = pd.concat(sampled_dfs, ignore_index=True)
        
        # Adjust if we have too many/too few
        if len(sampled) > n:
            sampled = sampled.sample(n=n, random_state=seed)
        elif len(sampled) < n:
            # Add more from unsampled
            remaining = df[~df.index.isin(sampled.index)]
            extra_needed = n - len(sampled)
            if len(remaining) >= extra_needed:
                extra = remaining.sample(n=extra_needed, random_state=seed)
                sampled = pd.concat([sampled, extra], ignore_index=True)
    else:
        # Simple random sampling
        sampled = df.sample(n=n, random_state=seed)
    
    return sampled.reset_index(drop=True)


def validate_dataset(df: pd.DataFrame) -> dict:
    """
    Validate dataset schema and data quality.
    
    Returns:
        Dictionary with validation results
    """
    validation = {
        "total_rows": len(df),
        "columns_present": list(df.columns),
        "missing_columns": [],
        "null_counts": {},
        "unique_values": {},
        "is_valid": True
    }
    
    # Check for expected columns
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            validation["missing_columns"].append(col)
            validation["is_valid"] = False
    
    # Check null counts for key columns
    key_columns = ['uuid', 'age', 'sex', 'state', 'occupation', 'education_level']
    for col in key_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            validation["null_counts"][col] = null_count
            if null_count > len(df) * 0.1:  # More than 10% nulls
                validation["is_valid"] = False
    
    # Get unique value counts for key categorical columns
    categorical_cols = ['zone', 'state', 'sex', 'marital_status', 'education_level']
    for col in categorical_cols:
        if col in df.columns:
            validation["unique_values"][col] = df[col].nunique()
    
    return validation


# ============================================================================
# HIGH-LEVEL API
# ============================================================================

def load_and_sample(
    n: int = DEFAULT_SAMPLE_SIZE,
    seed: int = DEFAULT_RANDOM_SEED,
    language: str = "en_IN",
    data_dir: str = DATA_DIR,
    validate: bool = True,
    verbose: bool = True,
    use_huggingface: bool = True
) -> Tuple[pd.DataFrame, dict]:
    """
    Main entry point: Load dataset and return a reproducible random sample.
    
    This is the recommended function for running simulations.
    
    Args:
        n: Number of personas to sample (default 1000)
        seed: Random seed for reproducibility (default 42)
        language: Language split to use (default 'en_IN')
        data_dir: Path to data directory
        validate: Whether to run validation checks
        verbose: Print progress information
    
    Returns:
        Tuple of (sampled_dataframe, metadata_dict)
    
    Example:
        >>> sample_df, meta = load_and_sample(n=1000, seed=42)
        >>> print(f"Loaded {len(sample_df)} personas from {meta['total_available']:,} total")
    """
    if verbose:
        print("=" * 60)
        print("🎯 CREDIGO.CLUB AUDIENCE SIMULATION ENGINE")
        print("   Loading Nemotron-Personas-India Dataset")
        print("=" * 60)
    
    # Load the full dataset
    full_df = load_full_dataset(data_dir, language, verbose=verbose, use_huggingface=use_huggingface)
    
    # Validate if requested
    validation_result = {}
    if validate:
        validation_result = validate_dataset(full_df)
        if verbose:
            if validation_result["is_valid"]:
                print("✅ Dataset validation passed")
            else:
                print("⚠️  Dataset validation warnings:")
                if validation_result["missing_columns"]:
                    print(f"   Missing columns: {validation_result['missing_columns']}")
    
    # Sample personas
    if verbose:
        print(f"\n🎲 Sampling {n:,} personas (seed={seed})...")
    
    sampled_df = sample_personas(full_df, n=n, seed=seed)
    
    if verbose:
        print(f"✅ Sampled {len(sampled_df):,} personas")
        
        # Quick stats on sample
        print(f"\n📊 Sample Distribution:")
        if 'zone' in sampled_df.columns:
            zone_dist = sampled_df['zone'].value_counts()
            print(f"   By Zone: {dict(zone_dist)}")
        if 'sex' in sampled_df.columns:
            sex_dist = sampled_df['sex'].value_counts()
            print(f"   By Sex: {dict(sex_dist)}")
        if 'age' in sampled_df.columns:
            print(f"   Age Range: {sampled_df['age'].min()} - {sampled_df['age'].max()} "
                  f"(mean: {sampled_df['age'].mean():.1f})")
    
    # Build metadata
    metadata = {
        "total_available": len(full_df),
        "sample_size": len(sampled_df),
        "random_seed": seed,
        "language": language,
        "validation": validation_result,
        "columns": list(sampled_df.columns)
    }
    
    if verbose:
        print("\n" + "=" * 60)
    
    return sampled_df, metadata


def get_dataset_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a summary statistics table for the dataset.
    
    Useful for understanding the sample composition before simulation.
    """
    summary_data = []
    
    # Demographic summaries
    if 'age' in df.columns:
        summary_data.append({
            "category": "Age",
            "metric": "Distribution",
            "value": f"Min: {df['age'].min()}, Max: {df['age'].max()}, Mean: {df['age'].mean():.1f}"
        })
    
    categorical_cols = {
        'zone': 'Geographic Zone',
        'state': 'State',
        'sex': 'Gender',
        'marital_status': 'Marital Status',
        'education_level': 'Education Level'
    }
    
    for col, name in categorical_cols.items():
        if col in df.columns:
            top_values = df[col].value_counts().head(3)
            summary_data.append({
                "category": name,
                "metric": "Top Values",
                "value": ", ".join([f"{k}: {v}" for k, v in top_values.items()])
            })
    
    return pd.DataFrame(summary_data)


# ============================================================================
# MAIN EXECUTION (for standalone testing)
# ============================================================================

if __name__ == "__main__":
    """
    Test loading and sampling when run directly.
    
    Usage:
        python load_dataset.py
    """
    print("\n🧪 Running load_dataset.py test...\n")
    
    try:
        # Load and sample 1000 personas
        sample_df, metadata = load_and_sample(n=1000, seed=42, verbose=True)
        
        print("\n📋 Sample Schema:")
        print(sample_df.dtypes)
        
        print("\n📋 First Persona Preview:")
        print("-" * 60)
        first = sample_df.iloc[0]
        preview_cols = ['age', 'sex', 'state', 'occupation', 'education_level', 'career_goals_and_ambitions']
        for col in preview_cols:
            if col in first.index:
                val = first[col]
                if isinstance(val, str) and len(val) > 100:
                    val = val[:100] + "..."
                print(f"  {col}: {val}")
        
        print("\n✅ Test complete!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nMake sure to download the dataset first using:")
        print("  python download_remaining.py")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise
