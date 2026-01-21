# Data Processing Pipeline

## Input

### USA Data
- **Format**: CSV files
- **Files**: 
  - `Dream Initial Survey_March 8, 2024_18.39.csv` (timepoint 1)
  - `Dream Follow Up 1-4_*.csv` (timepoints 2-5)
- **Content**: Features + Dream Memory

### Argentina Data
- **Features**: `DATA FORM 1-5_4P.xlsx` (timepoints 1-5)
- **Dream Memory**: `Dream Reports/Session1-5_English/Spanish_Checked.xlsx`
- **Content**: Separate Features and Dream Memory files

## Core Processing Logic

1. **Load USA data**
   - Extract demographics from Initial Survey
   - Load all CSV files
   - Map fields to unified names
   - Fill demographics from Initial Survey

2. **Load Argentina Features**
   - Read DATA FORM Excel files
   - Extract features by pattern matching
   - Decode numeric codes to natural language

3. **Load Argentina Dream Memory**
   - Read Dream Reports Excel files (English + Spanish)
   - Extract dream text by session

4. **Merge Argentina data**
   - Join Features + Dream Memory by `participant_id` + `timepoint`
   - Preserve both English and Spanish versions

5. **Integrate USA + Argentina**
   - Combine datasets
   - Align columns

6. **Apply mappings**
   - Argentina: numeric codes → natural language
   - USA: normalize mixed formats

7. **Clean age fields**
   - Remove suffixes ("years old", "yo", etc.)

8. **Convert to numeric codes**
   - Natural language → unified numeric codes
   - Generate `*_numeric` columns

## Output

- **`integrated_dream_data.csv`**: Unified dataset
- **`integrated_dream_data.json`**: Metadata (counts, columns, timestamp)

## Features Mapping

### Dream Features
| Unified Name | USA Column | Argentina Pattern |
|-------------|------------|-------------------|
| `dream_feelings` | `Dream_Feelings` | `sentiste al despertar`, `feeling` |
| `dream_talk` | `Dream_Talk` | `hablaste sobre tus sueños` |
| `dream_write` | `Dream_Write` | `escribiste sobre tus sueños` |
| `dream_content` | `Dream_Content` | `pensamientos diarios se reflejaron` |
| `dream_frequency` | `DreamQ_Frequency` | `frecuencia tuviste sueños` |
| `dream_vivid` | `DreamQ_Vivid_1` | `vívidos han sido tus sueños` |
| `dream_bizarre` | `DreamQ_Bizarre_1` | `bizarros han sido tus sueños` |
| `dream_emotional_tone` | `More_EmotionalTone_1` | `tono emocional` |
| `dream_intensity` | `More_DreamIntensity_1` | `intensas.*emociones` |

### Demographics
| Unified Name | USA Column | Argentina Pattern |
|-------------|------------|-------------------|
| `age` | `Demo_Age` | `edad` |
| `education` | `Demo_Education` | `educativo`, `educación` |
| `student` | `Demo_Student` | `estudiante` |
| `gender` | `Demo_Gender` | `género`, `gender` |

### Sleep
| Unified Name | USA Column | Argentina Pattern |
|-------------|------------|-------------------|
| `sleep_quality` | `Sleep_Quality` | `calidad.*sueño`, `sleepq` |
| `sleep_hours` | `Sleep_Hours` | `horas.*dormiste`, `hoursofsleep` |
| `sleep_disturbed` | `Sleep_Disturbed` | `interrumpido.*sueño`, `sleep_interrupted` |

### Mental Health
- **GAD**: Sum of `GAD_Bothered_1-7` (USA) or `GAD score` (Argentina)
- **PHQ**: Sum of `PHQ_Bothered_1-9` (USA) or `PHQ score` (Argentina)

## Details Handling

### Timepoint Conversion
- **USA**: `initial` → 1, `follow up 1-4` → 2-5
- **Argentina**: `session/form 1-5` → 1-5

### Dream Text Cleaning
- Remove JSON metadata
- Filter meaningless responses (< 20 chars)
- Normalize whitespace
- Minimum length: 20 characters

### Sleep Hours
- Remove text ("hours", "hrs", etc.)
- Handle ranges ("7-8" → 7.5)
- Convert to float

### Age Field
- Remove suffixes: "years old", "yo", "y.o.", "or more", "or older"
- Example: "18-24 years old" → "18-24"

### Field Mapping Process
1. **Argentina**: Numeric code → Natural language (via `mapping_table.csv`)
2. **USA**: Normalize mixed formats (numeric codes → natural language if needed)
3. **Unified**: Natural language → Numeric code (generate `*_numeric` columns)

### Mapping Table Structure
- **Field**: Field name (e.g., `AGE`, `Dream_feeling`)
- **Argentina_Code**: Numeric code in Argentina data
- **Natural_Language**: Common natural language representation
- **Numeric_Code**: Unified numeric code for both countries

### Participant ID Handling
- **USA**: `PROLIFIC_PID`, `ProlificID`, or `ResponseId`
- **Argentina**: `codigo`, `Código`, or `code`

### Missing Data
- Demographics: Fill from Initial Survey (USA only)
- Features: Set to `None` if not found
- Dream Memory: Preserve `None` if missing
