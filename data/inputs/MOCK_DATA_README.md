# Mock Data Documentation

This directory contains **mock/dummy datasets** for development. These will be replaced with real data from STEP teams later.

## Generated Files

### 1. step1_data.csv (280 KB)
**Source**: STEP 1 Team - Sensor data from etching process
**Rows**: 1,252 wafers
**Schema**:
```
- wafer_id: Unique wafer identifier (W0001-W1252)
- lot_id: Lot identifier, 25 wafers per lot (L001-L051)
- recipe: Etching recipe version (Etch_v3.2)
- chamber: Processing chamber (A, B, or C)
- timestamp: ISO 8601 timestamp
- etch_rate: Etching rate (3.2-4.2 µm/min)
- pressure: Chamber pressure (145-165 mTorr)
- temperature: Chamber temperature (58-63°C)
- rf_power: RF power (1800-1900 W)
- gas_flow: Gas flow rate (235-255 sccm)
- sensor6-10: Additional sensor readings
```

**Anomalies**: ~15% of wafers have elevated etch_rate (>3.7) or pressure (>158)

### 2. wm811k_proxy.csv (79 KB)
**Source**: STEP 2 Team - Wafer map pattern matching
**Rows**: 1,252 mappings (one per wafer)
**Schema**:
```
- wafer_id: Links to step1_data.csv
- matched_wm811k_id: ID from WM-811K dataset
- pattern_type: Pattern classification (Edge-Ring, Center, Random)
- severity: Pattern severity score (0.3-0.9)
- defect_density: Number of defects (100-400)
- confidence: Matching confidence (0.65-0.85)
```

**Pattern Distribution**:
- Random: 62.6% (784 wafers)
- Center: 21.3% (267 wafers)
- Edge-Ring: 16.1% (201 wafers)

### 3. carinthia_proxy.csv (64 KB)
**Source**: STEP 3 Team - SEM defect classification
**Rows**: 1,252 mappings (one per wafer)
**Schema**:
```
- wafer_id: Links to step1_data.csv
- matched_carinthia_id: ID from Carinthia dataset
- defect_type: Defect classification (Particle, Scratch, Residue)
- defect_count: Number of defects (5-30)
- location_pattern: Defect location (edge, center, random)
- confidence: Classification confidence (0.7-0.9)
```

**Defect Distribution**:
- Residue: 39.6% (496 wafers)
- Particle: 38.9% (487 wafers)
- Scratch: 21.5% (269 wafers)

## Data Relationships

All three datasets are linked by `wafer_id`. The mock data includes correlations:
- High etch_rate → Edge-Ring patterns
- High pressure → Particle defects
- High temperature → Residue defects

## Regenerating Mock Data

To regenerate with different parameters:
```bash
python scripts/generate_mock_data.py
```

## Replacing with Real Data

When real data arrives from STEP teams:
1. Verify the schema matches expectations
2. Copy real files to `data/inputs/`
3. Overwrite: step1_data.csv, wm811k_proxy.csv, carinthia_proxy.csv
4. Delete this MOCK_DATA_README.md file

**No code changes needed!** The pipeline reads from these CSV files.

## Time Coverage

- Start: 2026-01-10 08:00:00
- End: 2026-01-23 08:45:00
- Duration: 13 days
- Frequency: 1 wafer every 15 minutes
