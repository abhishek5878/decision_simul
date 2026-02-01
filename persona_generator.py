"""
PERSONA GENERATOR FOR CREDIGO.CLUB SIMULATION
==============================================

This module generates/samples 1 million (10 lakh) diverse Indian personas
for testing Credigo.club's product-market fit across segments.

Strategy:
---------
1. Load existing Nemotron-Personas-India dataset (46 parquet files, ~212k personas)
2. Analyze distributions (age, location, education, occupation, languages)
3. Derive critical features for credit card simulation:
   - Digital literacy proxy (education + age + urban/rural)
   - Aspirational intensity (career goals + occupation + age)
   - Financial sophistication (occupation + education)
   - Risk orientation (from persona descriptions)
   - English proficiency (education + second language)
   - Trust orientation (cultural background)
4. Oversample with slight variations to reach 1M while preserving distributions
5. Export to efficient format for simulation engine

Output: personas_1m.parquet with all fields + derived features
"""

import pandas as pd
import numpy as np
import glob
import os
from tqdm import tqdm
import json
import re

class PersonaGenerator:
    """Generates/samples 1M diverse Indian personas for simulation"""
    
    def __init__(self, data_dir="./nemotron_personas_india_data/data"):
        self.data_dir = data_dir
        self.personas_df = None
        self.target_count = 1_000_000  # 10 lakh
        
    def load_existing_data(self):
        """Load all available parquet files from downloaded dataset"""
        print("="*80)
        print("STEP 1: LOADING NEMOTRON-PERSONAS-INDIA DATASET")
        print("="*80)
        
        parquet_files = sorted(glob.glob(f"{self.data_dir}/*.parquet"))
        print(f"\nFound {len(parquet_files)} parquet files")
        
        # Load all files efficiently
        dfs = []
        for file in tqdm(parquet_files, desc="Loading parquet files"):
            df = pd.read_parquet(file)
            dfs.append(df)
        
        self.personas_df = pd.concat(dfs, ignore_index=True)
        print(f"\n✓ Loaded {len(self.personas_df):,} personas")
        print(f"  Memory usage: {self.personas_df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        
        # Show distribution summary
        print(f"\n--- Quick Stats ---")
        print(f"Age range: {self.personas_df['age'].min()} - {self.personas_df['age'].max()}")
        print(f"Languages: {self.personas_df['first_language'].nunique()} unique")
        print(f"States: {self.personas_df['state'].nunique()} unique")
        print(f"Education levels: {self.personas_df['education_level'].nunique()}")
        print(f"Occupations: {self.personas_df['occupation'].nunique()}")
        
        return self.personas_df
    
    def derive_features(self):
        """
        Derive critical features for credit card simulation
        
        Key derived features:
        - digital_literacy_score: 0-100, based on education + age + urban
        - aspirational_intensity: 0-100, based on career goals + age + occupation
        - financial_sophistication: 0-100, based on occupation + education
        - english_proficiency: 0-100, based on education + second language
        - risk_orientation: low/medium/high (from occupation + age)
        - trust_score: 0-100 (conservative vs open to new things)
        - zone_category: metro/tier2/rural
        """
        print("\n" + "="*80)
        print("STEP 2: DERIVING SIMULATION FEATURES")
        print("="*80)
        
        df = self.personas_df.copy()
        
        # 1. DIGITAL LITERACY SCORE (0-100)
        print("\n[1/7] Computing digital_literacy_score...")
        digital_base = 0
        
        # Education contribution (0-40 points)
        education_map = {
            'Illiterate': 0,
            'Below Primary': 5,
            'Primary': 10,
            'Middle': 15,
            'Secondary': 20,
            'Higher Secondary': 25,
            'Graduate': 35,
            'Post Graduate': 40
        }
        df['edu_score'] = df['education_level'].map(education_map).fillna(20)
        
        # Age penalty (younger = more digital, 0-25 points)
        df['age_score'] = np.clip(25 - (df['age'] - 18) * 0.3, 0, 25)
        
        # Urban boost (0-35 points)
        zone_map = {'Urban': 35, 'Semi-Urban': 20, 'Rural': 5}
        df['zone_score'] = df['zone'].map(zone_map).fillna(15)
        
        df['digital_literacy_score'] = np.clip(
            df['edu_score'] + df['age_score'] + df['zone_score'],
            0, 100
        ).astype(int)
        
        # 2. ASPIRATIONAL INTENSITY (0-100)
        print("[2/7] Computing aspirational_intensity...")
        
        # Occupation contribution (0-40)
        aspirational_occupations = {
            'IT Professional': 40,
            'Business Owner': 35,
            'Engineer': 35,
            'Doctor': 35,
            'Teacher': 25,
            'Government Employee': 20,
            'Student': 30,
            'No Occupation / Retired / Homemaker': 10
        }
        df['occ_aspiration'] = df['occupation'].apply(
            lambda x: 30 if any(word in str(x) for word in ['IT', 'Engineer', 'Business', 'Professional']) else 15
        )
        
        # Age factor (younger = more aspirational, 0-30)
        df['age_aspiration'] = np.clip(30 - (df['age'] - 20) * 0.4, 0, 30)
        
        # Career goals intensity (0-30) - from text length/keywords
        df['goals_aspiration'] = df['career_goals_and_ambitions'].apply(
            lambda x: min(30, len(str(x)) / 30) if pd.notna(x) else 10
        )
        
        df['aspirational_intensity'] = np.clip(
            df['occ_aspiration'] + df['age_aspiration'] + df['goals_aspiration'],
            0, 100
        ).astype(int)
        
        # 3. FINANCIAL SOPHISTICATION (0-100)
        print("[3/7] Computing financial_sophistication...")
        
        # Education (0-40)
        df['fin_edu'] = df['edu_score']
        
        # Occupation (0-40)
        financial_occupations = ['Business', 'IT', 'Engineer', 'Doctor', 'Lawyer', 'Manager', 'Consultant']
        df['fin_occ'] = df['occupation'].apply(
            lambda x: 40 if any(word in str(x) for word in financial_occupations) else 20
        )
        
        # Urban premium (0-20)
        df['fin_urban'] = df['zone'].map({'Urban': 20, 'Semi-Urban': 10, 'Rural': 5}).fillna(10)
        
        df['financial_sophistication'] = np.clip(
            df['fin_edu'] + df['fin_occ'] + df['fin_urban'],
            0, 100
        ).astype(int)
        
        # 4. ENGLISH PROFICIENCY (0-100)
        print("[4/7] Computing english_proficiency...")
        
        # Education base (0-50)
        df['eng_edu'] = np.clip(df['edu_score'] * 1.25, 0, 50)
        
        # Second language is English (0-30)
        df['eng_second'] = df['second_language'].apply(
            lambda x: 30 if 'English' in str(x) or 'english' in str(x) else 0
        )
        
        # Urban boost (0-20)
        df['eng_urban'] = df['zone'].map({'Urban': 20, 'Semi-Urban': 10, 'Rural': 5}).fillna(10)
        
        df['english_proficiency'] = np.clip(
            df['eng_edu'] + df['eng_second'] + df['eng_urban'],
            0, 100
        ).astype(int)
        
        # 5. RISK ORIENTATION (categorical: low/medium/high)
        print("[5/7] Computing risk_orientation...")
        
        # Calculate risk score (0-100)
        risk_score = 0
        
        # Age factor (younger = more risk-tolerant)
        risk_score = np.clip(50 - (df['age'] - 25) * 0.8, 0, 50)
        
        # Occupation factor
        risk_occupations = {'Business Owner': 30, 'IT Professional': 25, 'Student': 20}
        risk_score += df['occupation'].apply(
            lambda x: 25 if 'Business' in str(x) else (20 if 'IT' in str(x) else 10)
        )
        
        # Marital status (single = more risk)
        risk_score += df['marital_status'].apply(
            lambda x: 15 if 'Never' in str(x) or 'Single' in str(x) else 5
        )
        
        # Categorize
        df['risk_orientation'] = pd.cut(
            risk_score,
            bins=[0, 30, 60, 100],
            labels=['low', 'medium', 'high']
        ).astype(str)
        
        # 6. TRUST SCORE (0-100) - openness to new things
        print("[6/7] Computing trust_score...")
        
        # Education (higher = more trust in systems)
        trust_base = df['edu_score']
        
        # Urban (more exposure to new products)
        trust_base += df['zone_score']
        
        # Age (younger = more trusting of tech)
        trust_base += np.clip(30 - (df['age'] - 20) * 0.5, 0, 30)
        
        # Hobby breadth (more hobbies = more open)
        df['hobby_count'] = df['hobbies_and_interests_list'].apply(
            lambda x: len(eval(x)) if pd.notna(x) and x != '' else 3
        )
        trust_base += np.clip(df['hobby_count'] * 2, 0, 15)
        
        df['trust_score'] = np.clip(trust_base, 0, 100).astype(int)
        
        # 7. ZONE CATEGORY (metro/tier2/rural) - simplified
        print("[7/7] Computing zone_category...")
        
        # Metro cities
        metro_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Bengaluru', 'Hyderabad', 'Chennai', 
                       'Kolkata', 'Pune', 'Ahmadabad', 'Ahmedabad']
        
        df['zone_category'] = 'tier2'  # default
        df.loc[df['zone'] == 'Rural', 'zone_category'] = 'rural'
        df.loc[df['district'].apply(lambda x: any(city in str(x) for city in metro_cities)), 
               'zone_category'] = 'metro'
        
        # Clean up temporary columns
        temp_cols = ['edu_score', 'age_score', 'zone_score', 'occ_aspiration', 
                    'age_aspiration', 'goals_aspiration', 'fin_edu', 'fin_occ', 
                    'fin_urban', 'eng_edu', 'eng_second', 'eng_urban', 'hobby_count']
        df = df.drop(columns=[col for col in temp_cols if col in df.columns])
        
        self.personas_df = df
        
        print("\n✓ Feature derivation complete!")
        print(f"\nFeature summary:")
        print(f"  digital_literacy_score: mean={df['digital_literacy_score'].mean():.1f}")
        print(f"  aspirational_intensity: mean={df['aspirational_intensity'].mean():.1f}")
        print(f"  financial_sophistication: mean={df['financial_sophistication'].mean():.1f}")
        print(f"  english_proficiency: mean={df['english_proficiency'].mean():.1f}")
        print(f"  risk_orientation: {df['risk_orientation'].value_counts().to_dict()}")
        print(f"  trust_score: mean={df['trust_score'].mean():.1f}")
        print(f"  zone_category: {df['zone_category'].value_counts().to_dict()}")
        
        return df
    
    def generate_million_personas(self):
        """
        Generate 1M personas by intelligently oversampling from existing dataset
        
        Strategy:
        - We have ~212k real personas
        - Need 1M total
        - Oversample ~5x with slight variations to preserve realism
        - Add gaussian noise to numerical scores (±5 points)
        - Keep core attributes the same
        """
        print("\n" + "="*80)
        print("STEP 3: SCALING TO 1 MILLION PERSONAS")
        print("="*80)
        
        current_count = len(self.personas_df)
        needed = self.target_count
        
        print(f"\nCurrent personas: {current_count:,}")
        print(f"Target: {needed:,}")
        print(f"Multiplication factor: {needed/current_count:.1f}x")
        
        if current_count >= needed:
            print(f"\n✓ Already have enough! Sampling {needed:,} personas...")
            final_df = self.personas_df.sample(n=needed, random_state=42).reset_index(drop=True)
        else:
            print(f"\nOversampling with variations...")
            
            # Calculate how many times to replicate
            replications = int(np.ceil(needed / current_count))
            
            dfs_to_concat = [self.personas_df]
            
            for rep in tqdm(range(1, replications), desc="Generating variations"):
                # Create variation by adding noise to derived scores
                df_varied = self.personas_df.copy()
                
                # Add small random noise to numerical scores (±5 points)
                noise_cols = ['digital_literacy_score', 'aspirational_intensity', 
                             'financial_sophistication', 'english_proficiency', 'trust_score']
                
                for col in noise_cols:
                    noise = np.random.randint(-5, 6, size=len(df_varied))
                    df_varied[col] = np.clip(df_varied[col] + noise, 0, 100)
                
                # Randomly flip risk orientation occasionally (5% chance)
                risk_flip_mask = np.random.random(len(df_varied)) < 0.05
                risk_options = ['low', 'medium', 'high']
                df_varied.loc[risk_flip_mask, 'risk_orientation'] = np.random.choice(
                    risk_options, size=risk_flip_mask.sum()
                )
                
                # Generate new UUIDs for variations
                df_varied['uuid'] = df_varied['uuid'].apply(
                    lambda x: x + f"_var{rep}" if pd.notna(x) else f"generated_var{rep}_{np.random.randint(1e6)}"
                )
                
                dfs_to_concat.append(df_varied)
            
            # Concatenate all variations
            expanded_df = pd.concat(dfs_to_concat, ignore_index=True)
            
            # Sample exactly 1M
            final_df = expanded_df.sample(n=needed, random_state=42).reset_index(drop=True)
        
        print(f"\n✓ Generated {len(final_df):,} personas!")
        
        # Add sequential persona_id for easy reference
        final_df['persona_id'] = range(1, len(final_df) + 1)
        
        self.personas_df = final_df
        return final_df
    
    def export_personas(self, output_file="personas_1m.parquet"):
        """Export final persona dataset for simulation"""
        print("\n" + "="*80)
        print("STEP 4: EXPORTING PERSONAS")
        print("="*80)
        
        print(f"\nExporting to {output_file}...")
        
        # Select key columns for simulation (drop very long text fields to save space)
        export_cols = [
            'persona_id', 'uuid', 'age', 'sex', 'marital_status', 
            'education_level', 'education_degree', 'occupation',
            'first_language', 'second_language', 'third_language',
            'zone', 'zone_category', 'state', 'district', 'country',
            'persona',  # Keep short persona summary
            'digital_literacy_score', 'aspirational_intensity',
            'financial_sophistication', 'english_proficiency',
            'risk_orientation', 'trust_score'
        ]
        
        # Keep only columns that exist
        export_cols = [col for col in export_cols if col in self.personas_df.columns]
        
        export_df = self.personas_df[export_cols]
        
        # Export as parquet (compressed, fast)
        export_df.to_parquet(output_file, compression='snappy', index=False)
        
        file_size_mb = os.path.getsize(output_file) / 1024**2
        
        print(f"✓ Exported {len(export_df):,} personas")
        print(f"  File size: {file_size_mb:.1f} MB")
        print(f"  Columns: {len(export_cols)}")
        print(f"  Location: {output_file}")
        
        # Print final distribution summary
        print("\n" + "="*80)
        print("FINAL PERSONA DISTRIBUTIONS")
        print("="*80)
        
        print("\n--- Age Distribution ---")
        age_bins = [0, 18, 25, 35, 45, 55, 65, 100]
        age_labels = ['<18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']
        age_dist = pd.cut(export_df['age'], bins=age_bins, labels=age_labels).value_counts(sort=False)
        for label, count in age_dist.items():
            print(f"  {label}: {count:,} ({count/len(export_df)*100:.1f}%)")
        
        print("\n--- Zone Distribution ---")
        zone_dist = export_df['zone_category'].value_counts()
        for zone, count in zone_dist.items():
            print(f"  {zone}: {count:,} ({count/len(export_df)*100:.1f}%)")
        
        print("\n--- Education Distribution ---")
        edu_dist = export_df['education_level'].value_counts().head(5)
        for edu, count in edu_dist.items():
            print(f"  {edu}: {count:,} ({count/len(export_df)*100:.1f}%)")
        
        print("\n--- Key Score Distributions ---")
        print(f"  Digital Literacy: {export_df['digital_literacy_score'].describe()[['mean', '50%', 'std']].to_dict()}")
        print(f"  Aspirational: {export_df['aspirational_intensity'].describe()[['mean', '50%', 'std']].to_dict()}")
        print(f"  Financial Soph: {export_df['financial_sophistication'].describe()[['mean', '50%', 'std']].to_dict()}")
        print(f"  Trust Score: {export_df['trust_score'].describe()[['mean', '50%', 'std']].to_dict()}")
        
        print("\n" + "="*80)
        print("✓ PERSONA GENERATION COMPLETE!")
        print("="*80)
        
        return export_df


def main():
    """Main execution function"""
    print("\n" + "🚀"*40)
    print("CREDIGO.CLUB SIMULATION - PERSONA GENERATOR")
    print("Generating 1,000,000 diverse Indian personas")
    print("🚀"*40 + "\n")
    
    # Initialize generator
    generator = PersonaGenerator()
    
    # Step 1: Load existing data
    generator.load_existing_data()
    
    # Step 2: Derive simulation features
    generator.derive_features()
    
    # Step 3: Scale to 1M
    generator.generate_million_personas()
    
    # Step 4: Export
    final_personas = generator.export_personas("personas_1m.parquet")
    
    print("\n✓ Ready for simulation!")
    print(f"  Load personas: pd.read_parquet('personas_1m.parquet')")
    print(f"  Next step: Run simulation_engine.py")
    
    return final_personas


if __name__ == "__main__":
    final_personas = main()

