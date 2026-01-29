# Input Data Directory

This directory contains input data for the AI-driven semiconductor quality control system.

## Supported Data Formats

### Wafer Inspection Images
- **Format**: PNG, JPEG, TIFF
- **Resolution**: Minimum 1024x1024 pixels (recommended)
- **Color Space**: RGB or Grayscale
- **Naming Convention**: `wafer_{batch_id}_{wafer_id}_{timestamp}.png`

### Inspection Data (CSV)
CSV files containing inspection metadata and measurements.

**Required Columns**:
- `wafer_id`: Unique wafer identifier
- `batch_id`: Manufacturing batch identifier
- `timestamp`: Inspection timestamp (ISO 8601 format)
- `defect_count`: Number of defects detected
- `defect_types`: Comma-separated list of defect types
- `severity`: Overall severity level (low, medium, high, critical)

**Optional Columns**:
- `operator_id`: Inspector identifier
- `equipment_id`: Inspection equipment identifier
- `process_step`: Manufacturing process step
- `coordinates`: Defect location coordinates (JSON format)

### Example CSV Structure
```csv
wafer_id,batch_id,timestamp,defect_count,defect_types,severity
W001,B2024001,2024-01-15T10:30:00Z,3,"scratch,particle",medium
W002,B2024001,2024-01-15T10:35:00Z,0,,low
W003,B2024001,2024-01-15T10:40:00Z,5,"pattern_defect,stain",high
```

### JSON Format (Alternative)
For complex inspection data, JSON format is supported:

```json
{
  "wafer_id": "W001",
  "batch_id": "B2024001",
  "timestamp": "2024-01-15T10:30:00Z",
  "defects": [
    {
      "type": "scratch",
      "location": {"x": 512, "y": 768},
      "severity": "medium",
      "size": 25.5
    },
    {
      "type": "particle",
      "location": {"x": 200, "y": 300},
      "severity": "low",
      "size": 5.2
    }
  ],
  "metadata": {
    "equipment_id": "INSP-001",
    "operator_id": "OP-042",
    "process_step": "lithography"
  }
}
```

## Directory Organization

Organize input files by batch:
```
inputs/
├── batch_B2024001/
│   ├── images/
│   │   ├── wafer_B2024001_W001_*.png
│   │   └── wafer_B2024001_W002_*.png
│   └── inspection_data.csv
├── batch_B2024002/
│   ├── images/
│   └── inspection_data.csv
└── README.md
```

## Data Quality Requirements

- **Completeness**: All required fields must be present
- **Accuracy**: Timestamp must be in ISO 8601 format
- **Consistency**: Defect types must match predefined categories in config.yaml
- **Image Quality**: Clear, well-lit images without significant artifacts

## Defect Types

Supported defect types (must match config.yaml):
- `scratch`: Linear marks or scratches
- `particle`: Foreign particles or contamination
- `stain`: Chemical stains or residues
- `pattern_defect`: Pattern transfer issues
- `edge_defect`: Edge chipping or irregularities

## Processing Pipeline

1. Place input files in this directory
2. Run the quality control pipeline
3. Results will be saved to `data/outputs/`
4. Logs will be written to `logs/`

## Notes

- Large image files should be compressed to reduce processing time
- Batch processing is recommended for multiple wafers
- Historical data can be archived after processing
