import pandas as pd
import numpy as np
import os

# Paths
BASE_DATA = '/jhdx0003008/data/XScale-Energetics/processed/triple_fusion_weighted_v1.csv'
EXPERT_V7 = '/jhdx0003008/workspace/projects_core/XScale-Energetics/outputs/v7.1_final_hybrid_predictions.csv'
SMILES_MAP = '/jhdx0003008/data/XScale-Energetics/processed/smiles_map_v8_final.csv'
CRYSTAL_DATA = '/jhdx0003008/data/XScale-Energetics/processed/main_benchmark_v4_3d_enriched.csv'
ATOMIC_3D = '/jhdx0003008/data/XScale-Energetics/processed/atomic_3d_features_v1.csv'
OUTPUT_FILE = '/jhdx0003008/data/XScale-Energetics/processed/integrated_3d_sota_v8.csv'

def clean_series(s):
    return s.astype(str).str.replace(u'\xa0', u' ', regex=True).str.strip().str.replace(u'\r', u'', regex=True)

def prepare_v8_final_hardened():
    print('>>> Phase 8.2: Hardened Multi-modal Integration with Index Alignment...')
    
    # 1. Load Base/Expert without naive 'Name' dropping. Use strict index matching since 
    # Expert predictions have exact chronological alignment.
    df_base = pd.read_csv(BASE_DATA)
    df_expert = pd.read_csv(EXPERT_V7)
    
    # Force chronological index as the key. No Name-dropped duplicates!
    df_base['Merge_Idx'] = range(len(df_base))
    df_expert['Merge_Idx'] = range(len(df_expert))
    
    df_merged = pd.merge(df_base, df_expert[['Merge_Idx', 'Pred_Ensemble_v7_1']], on='Merge_Idx', how='left')
    df_merged = df_merged.drop(columns=['Merge_Idx'])
    print(f'Stage 1 (Expert Merge via Index): {df_merged.shape}')
    
    # 2. Join with SMILES Map
    df_map = pd.read_csv(SMILES_MAP).drop_duplicates(subset=['Unique_Key'])
    df_merged['Unique_Key_Match'] = clean_series(df_merged['Unique_Key'])
    df_map['Unique_Key_Match'] = clean_series(df_map['Unique_Key'])
    
    df_merged = pd.merge(df_merged, df_map[['Unique_Key_Match', 'SMILES']], on='Unique_Key_Match', how='left')
    df_merged = df_merged.drop(columns=['Unique_Key_Match'])
    print(f'Stage 2 (SMILES Map): {df_merged.shape}')
    
    # 3. Join with Crystal Descriptors
    df_crystal = pd.read_csv(CRYSTAL_DATA)
    df_crystal['SMILES_Clean'] = clean_series(df_crystal['Clean_SMILES'])
    df_merged['SMILES_Clean'] = clean_series(df_merged['SMILES'])
    
    crystal_cols = ['SMILES_Clean', 'Crystal_Density', 'Packing_Fraction', 'UnitCell_Volume']
    # Safely select present columns
    act_cols = [c for c in crystal_cols if c in df_crystal.columns]
    
    df_crystal_clean = df_crystal[act_cols].drop_duplicates(subset=['SMILES_Clean'])
    df_merged = pd.merge(df_merged, df_crystal_clean, on='SMILES_Clean', how='left')
    df_merged = df_merged.drop(columns=['SMILES_Clean'])
    print(f'Stage 3 (Crystal Merge): {df_merged.shape}')
    
    # 4. Atomic 3D Aggregation
    print('>>> Running Atomic Aggregation (183k rows)...')
    df_atomic = pd.read_csv(ATOMIC_3D, header=None, low_memory=False)
    unique_keys_raw = clean_series(df_atomic.iloc[:, -3])
    df_atomic['Unique_Key_Clean'] = unique_keys_raw
    atomic_cols = df_atomic.columns[:-4]
    
    for col in atomic_cols:
        df_atomic[col] = pd.to_numeric(df_atomic[col], errors='coerce')
        
    df_atomic_agg = df_atomic.groupby('Unique_Key_Clean')[atomic_cols].agg(['mean', 'std']).reset_index()
    df_atomic_agg.columns = [f'atomic_3d_{c[0]}_{c[1]}' if c[0] != 'Unique_Key_Clean' else 'Unique_Key_Clean' for c in df_atomic_agg.columns]
    
    df_merged['Unique_Key_Clean'] = clean_series(df_merged['Unique_Key'])
    df_merged = pd.merge(df_merged, df_atomic_agg, on='Unique_Key_Clean', how='left')
    df_merged = df_merged.drop(columns=['Unique_Key_Clean'])
    print(f'Stage 4 (Atomic Agg): {df_merged.shape}')
    
    # Final Hardening
    num_final = [c for c in df_merged.columns if c not in ['SMILES', 'Name', 'Unique_Key', 'Target_IS']]
    df_merged[num_final] = df_merged[num_final].apply(pd.to_numeric, errors='coerce')
    df_merged[num_final] = df_merged[num_final].fillna(df_merged[num_final].mean())
    df_merged = df_merged.drop_duplicates(subset=['Unique_Key'])
    
    print(f'Final Success! Integrated Matrix: {df_merged.shape}')
    df_merged.to_csv(OUTPUT_FILE, index=False)

if __name__ == "__main__":
    prepare_v8_final_hardened()
