# Data Processing Pipeline - Dream Study Integration

## Overview

This pipeline integrates and preprocesses dream report data from two cross-cultural studies: USA and Argentina. The integrated dataset combines dream narratives (Dream Memory) with associated features (demographics, mental health indicators, sleep quality, etc.) for subsequent NLP analysis and statistical modeling.

## Data Sources

### USA Data
- **Format**: CSV files
- **Structure**: Each file contains both Features and Dream Memory in a single record
- **Files**: Initial survey + 4 follow-up surveys (timepoints 0-4)
- **Language**: English only

### Argentina Data
- **Format**: Excel files (.xlsx)
- **Structure**: **Split across two sources**:
  1. **DATA FORM files** (1-5): Contains Features only (no Dream Memory)
  2. **Dream Reports files**: Contains Dream Memory only (both English and Spanish versions)
- **Files**: 5 sessions (timepoints 1-5)
- **Language**: Spanish (DATA FORM) + English/Spanish (Dream Reports)

## Processing Pipeline

```
┌─────────────────┐
│   USA Data      │───┐
│ (CSV files)     │   │
│ Features +      │   │
│ Dream Memory    │   │
└─────────────────┘   │
                       │
┌─────────────────┐   │    ┌──────────────────┐
│ Argentina DATA  │───┼───▶│   Merge by        │
│ FORM files      │   │    │ participant_id +  │
│ (Features only) │   │    │ timepoint         │
└─────────────────┘   │    └──────────────────┘
                       │              │
┌─────────────────┐   │              ▼
│ Argentina Dream │───┘    ┌──────────────────┐
│ Reports files   │        │  Integrated Data │
│ (Dream Memory   │        │  (CSV + JSON)    │
│  only, EN+ES)   │        └──────────────────┘
└─────────────────┘
```

## Key Processing Steps

### 1. USA Data Loading (`load_usa_data()`)
- Reads CSV files, skipping question text rows
- Extracts both Features and Dream Memory in one pass
- Maps standardized field names (GAD, PHQ, demographics, sleep, dream-related features)

### 2. Argentina Features Loading (`load_argentina_data_forms()`)
- Reads DATA FORM Excel files (timepoints 1-5)
- **Only extracts Features** (no Dream Memory)
- Handles participant ID column name variations (`codigo`, `Código`, `code`)
- Maps Spanish question text to standardized field names using pattern matching

### 3. Argentina Dream Memory Loading (`load_argentina_dream_reports()`)
- Reads Dream Reports Excel files (both English and Spanish versions)
- **Only extracts Dream Memory** (dream_text field)
- Preserves both language versions as separate records
- Cleans dream text (removes meaningless responses, normalizes whitespace)

### 4. Argentina Data Merging (`_merge_argentina_features_and_dreams()`)
- Merges Features (from DATA FORM) with Dream Memory (from Dream Reports)
- **Matching key**: `participant_id` + `timepoint`
- **Strategy**: 
  - Left join on Dream Memory records (preserves all language versions)
  - Adds Features records without matching Dream Memory (for completeness)
- Result: Each Dream Memory record (English/Spanish) gets matched Features when available

### 5. Final Integration (`integrate_all_data()`)
- Combines USA and Argentina datasets
- Ensures column consistency across both sources
- Outputs unified dataset ready for analysis

### 6. Preprocessing (`preprocess_data()`)
- Removes records without dream text (optional, configurable)
- Cleans participant IDs
- Normalizes timepoint values
- Generates summary statistics

## Key Points Addressed

### ✅ **Separation of Concerns**
- **Problem**: Original code tried to read Dream Memory from DATA FORM files, but Dream Memory should come from Dream Reports files
- **Solution**: Separated Features loading (DATA FORM) from Dream Memory loading (Dream Reports)

### ✅ **Language Preservation**
- **Problem**: Need to preserve both English and Spanish versions of Dream Memory from Argentina
- **Solution**: Load both language versions as separate records, each matched with the same Features

### ✅ **Data Merging Logic**
- **Problem**: Features and Dream Memory are in separate files for Argentina, need to merge them correctly
- **Solution**: Implemented merge by `participant_id` + `timepoint` to correctly associate Features with Dream Memory

### ✅ **Participant ID Handling**
- **Problem**: Different files use different column names for participant ID (`codigo`, `Código`, `code`)
- **Solution**: Implemented flexible column name detection with case-insensitive matching

### ✅ **Data Completeness**
- **Problem**: Some participants may have Features but no Dream Memory (or vice versa)
- **Solution**: Preserve both types of records - Features-only records and Dream Memory-only records are both included

### ✅ **Field Mapping**
- **Problem**: Argentina DATA FORM files use Spanish question text as column headers
- **Solution**: Pattern-based field mapping to identify and extract standardized features from Spanish text

## Output

- **CSV file**: `integrated_dream_data.csv` - Complete integrated dataset
- **JSON file**: `integrated_dream_data.json` - Metadata and summary statistics

## Data Statistics (Example Run)

- **Total Features records (Argentina)**: 4,780
- **Total Dream Memory records (Argentina)**: 9,560 (4,784 English + 4,784 Spanish)
- **Merged Argentina records**: 9,568
- **Records with both Features and Dream Memory**: 7,859
- **USA records**: ~2,000 (varies by timepoint)

## Usage

```python
from data_integration_preprocessing import DreamDataIntegrator

integrator = DreamDataIntegrator()
integrated_data = integrator.integrate_all_data()
processed_data = integrator.preprocess_data(integrated_data)
integrator.save_integrated_data(processed_data)
```

