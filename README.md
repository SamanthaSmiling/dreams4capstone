# Dreams4Capstone

Cross-cultural dream analysis project (USA & Argentina).

## Quick Start

```python
from Step0_data_integration_preprocessing import DreamDataIntegrator

integrator = DreamDataIntegrator()
integrated_data = integrator.integrate_all_data()
processed_data = integrator.preprocess_data(integrated_data)
integrator.save_integrated_data(processed_data)
```

## Files

- `Step0_data_integration_preprocessing.py` - Main data integration script
- `mapping_table.csv` - Field mapping definitions
- `integrated_dream_data.csv` - Output dataset
- `Argentina/` - Argentina survey data
- `USA/` - USA survey data

## Data Processing

1. Load USA data (CSV files)
2. Load Argentina Features (DATA FORM Excel files)
3. Load Argentina Dream Memory (Dream Reports Excel files)
4. Merge Argentina Features + Dream Memory
5. Integrate USA + Argentina data
6. Apply field mappings and normalization
7. Generate numeric codes for categorical fields

## Output

- `integrated_dream_data.csv` - Integrated dataset
- `integrated_dream_data.json` - Metadata
