"""
Data Integration and Preprocessing Script
Integrate and preprocess data from USA and Argentina folders
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
import json
from datetime import datetime

class DreamDataIntegrator:
    """Dream Data Integrator"""
    
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)
        
        self.usa_dir = self.base_dir / "USA"
        self.argentina_dir = self.base_dir / "Argentina"
        self.argentina_reports_dir = self.argentina_dir / "Dream Reports"
        
        # Field mapping configuration
        self.field_mapping = {
            'dream_memory': {
                'usa': 'DreamMemory',
                'argentina_english': ['Dream_recall_en_1', 'Dream_recall_en_2', 'Dream_recall_en_3', 
                                     'Dream_recall_en_4', 'Dream_recall_en_5'],
                'argentina_spanish': ['Dream_recall_spa_1', 'Dream_recall_spa_2', 'Dream_recall_spa_3',
                                     'Dream_recall_spa_4', 'Dream_recall_spa_5']
            }
        }
    
    def clean_dream_text(self, text):
        """Clean dream text"""
        if pd.isna(text) or text is None:
            return None
        
        text = str(text).strip()
        
        # Remove JSON metadata
        if text.startswith('{') and 'ImportId' in text:
            return None
        
        # Remove common meaningless responses
        meaningless_responses = [
            'no', 'none', 'n/a', 'na', 'no dreams', 'no dream',
            "i don't remember", "don't remember", "can't remember",
            "haven't remembered", "no dreams that i remember",
            "none that i remember", "i haven't remembered",
            "no dreams i remember", "no dreams remembered"
        ]
        
        text_lower = text.lower()
        if any(response in text_lower for response in meaningless_responses):
            if len(text) < 20:  # If very short and contains these words, it may be a meaningless response
                return None
        
        # Remove extra spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # If text is too short (less than 10 characters), it may not be a valid dream description
        if len(text) < 20:
            return None
        
        return text
    
    def extract_timepoint_from_filename(self, filename):
        """Extract timepoint from filename"""
        filename_lower = filename.lower()
        
        # USA files
        if 'initial' in filename_lower:
            return 0
        elif 'follow up 1' in filename_lower or 'month1' in filename_lower:
            return 1
        elif 'follow up 2' in filename_lower or 'month2' in filename_lower:
            return 2
        elif 'follow up 3' in filename_lower or 'month3' in filename_lower:
            return 3
        elif 'follow up 4' in filename_lower or 'month4' in filename_lower:
            return 4
        elif 'follow up 5' in filename_lower or 'month5' in filename_lower:
            return 5
        
        # Argentina files
        if 'session1' in filename_lower or 'form 1' in filename_lower:
            return 1
        elif 'session2' in filename_lower or 'form 2' in filename_lower:
            return 2
        elif 'session3' in filename_lower or 'form 3' in filename_lower:
            return 3
        elif 'session4' in filename_lower or 'form 4' in filename_lower:
            return 4
        elif 'session5' in filename_lower or 'form 5' in filename_lower:
            return 5
        
        return None
    
    def load_usa_data(self):
        """Load CSV data from USA folder"""
        print("=" * 80)
        print("Loading USA data...")
        print("=" * 80)
        
        all_data = []
        csv_files = sorted(self.usa_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            print(f"\nProcessing file: {csv_file.name}")
            try:
                # Read CSV file, skip second row (question text row)
                df = pd.read_csv(csv_file, skiprows=[1])
                
                # Extract timepoint
                timepoint = self.extract_timepoint_from_filename(csv_file.name)
                
                # Create unified data structure, using number of rows from original data
                num_rows = len(df)
                unified_df = pd.DataFrame(index=range(num_rows))
                
                # Basic information
                unified_df['source_file'] = csv_file.name
                unified_df['country'] = 'USA'
                unified_df['language'] = 'English'
                unified_df['timepoint'] = timepoint
                
                # Participant ID
                if 'PROLIFIC_PID' in df.columns:
                    unified_df['participant_id'] = df['PROLIFIC_PID']
                elif 'ProlificID' in df.columns:
                    unified_df['participant_id'] = df['ProlificID']
                else:
                    unified_df['participant_id'] = df.get('ResponseId', None)
                
                # Dream text
                if 'DreamMemory' in df.columns:
                    unified_df['dream_text'] = df['DreamMemory'].apply(self.clean_dream_text)
                else:
                    unified_df['dream_text'] = None
                
                # Other dream-related fields
                dream_fields = {
                    'dream_feelings': 'Dream_Feelings',
                    'dream_talk': 'Dream_Talk',
                    'dream_write': 'Dream_Write',
                    'dream_content': 'Dream_Content',
                    'dream_frequency': 'DreamQ_Frequency',
                    'dream_vivid': 'DreamQ_Vivid_1',
                    'dream_bizarre': 'DreamQ_Bizarre_1',
                    'dream_emotional_tone': 'More_EmotionalTone_1',
                    'dream_intensity': 'More_DreamIntensity_1'
                }
                
                for unified_name, original_name in dream_fields.items():
                    if original_name in df.columns:
                        unified_df[unified_name] = df[original_name]
                    else:
                        unified_df[unified_name] = None
                
                # Mental health indicators
                if 'GAD_Bothered_1' in df.columns:
                    gad_cols = [col for col in df.columns if col.startswith('GAD_Bothered_')]
                    if gad_cols:
                        unified_df['gad_total'] = df[gad_cols].apply(
                            lambda x: sum([int(v) if pd.notna(v) and str(v).isdigit() else 0 
                                         for v in x]), axis=1
                        )
                
                if 'PHQ_Bothered_1' in df.columns:
                    phq_cols = [col for col in df.columns if col.startswith('PHQ_Bothered_')]
                    if phq_cols:
                        unified_df['phq_total'] = df[phq_cols].apply(
                            lambda x: sum([int(v) if pd.notna(v) and str(v).isdigit() else 0 
                                         for v in x]), axis=1
                        )
                
                # Demographic information
                demo_fields = {
                    'age': 'Demo_Age',
                    'education': 'Demo_Education',
                    'student': 'Demo_Student',
                    'gender': 'Demo_Gender'
                }
                
                for unified_name, original_name in demo_fields.items():
                    if original_name in df.columns:
                        unified_df[unified_name] = df[original_name]
                
                # Sleep information
                sleep_fields = {
                    'sleep_quality': 'Sleep_Quality',
                    'sleep_hours': 'Sleep_Hours',
                    'sleep_disturbed': 'Sleep_Disturbed'
                }
                
                for unified_name, original_name in sleep_fields.items():
                    if original_name in df.columns:
                        unified_df[unified_name] = df[original_name]
                
                all_data.append(unified_df)
                print(f"  Loaded {len(unified_df)} records")
                
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            print(f"\nUSA data total: {len(result)} records")
            print(f"Records with dream text: {result['dream_text'].notna().sum()}")
            return result
        else:
            return pd.DataFrame()
    
    def load_argentina_data_forms(self):
        """Load Argentina DATA FORM files - Features only (no Dream Memory)"""
        print("\n" + "=" * 80)
        print("Loading Argentina DATA FORM files (Features only)...")
        print("=" * 80)
        
        all_data = []
        
        if not self.argentina_dir.exists():
            print("Argentina folder does not exist")
            return pd.DataFrame()
        
        # Check openpyxl version
        try:
            import openpyxl
            openpyxl_version = openpyxl.__version__
            version_parts = [int(x) for x in openpyxl_version.split('.')]
            if version_parts < [3, 1, 0]:
                print(f"Warning: openpyxl version {openpyxl_version} is too low")
                return pd.DataFrame()
        except ImportError:
            print("Warning: openpyxl not installed")
            return pd.DataFrame()
        
        # Find all DATA FORM files
        data_form_files = sorted([f for f in self.argentina_dir.glob("DATA FORM *.xlsx")])
        
        for excel_file in data_form_files:
            # Extract timepoint from filename
            timepoint_match = re.search(r'FORM (\d+)', excel_file.name)
            if timepoint_match:
                timepoint = int(timepoint_match.group(1))
            else:
                continue
            
            print(f"\nProcessing DATA FORM {timepoint}: {excel_file.name}")
            try:
                # Read Excel file - first row is questions, second row onwards is data
                df = pd.read_excel(excel_file, skiprows=[0])
                
                num_rows = len(df)
                unified_df = pd.DataFrame(index=range(num_rows))
                
                # Basic information
                unified_df['source_file'] = excel_file.name
                unified_df['country'] = 'Argentina'
                unified_df['language'] = 'Spanish'  # DATA FORM files are in Spanish
                unified_df['timepoint'] = timepoint
                
                # Participant ID - normalize to handle 'codigo', 'Código', and 'code'
                participant_id_col = None
                for col in df.columns:
                    col_lower = str(col).lower()
                    if col_lower == 'codigo' or col_lower == 'código' or col_lower == 'code':
                        participant_id_col = col
                        break
                
                if participant_id_col:
                    unified_df['participant_id'] = df[participant_id_col].astype(str).str.strip().values
                else:
                    print(f"  Warning: Could not find participant ID column in {excel_file.name}")
                    print(f"    Available columns (first 5): {list(df.columns)[:5]}")
                    unified_df['participant_id'] = None
                
                # NOTE: We do NOT load dream_text from DATA FORM files
                # Dream Memory should come from Dream Reports files only
                unified_df['dream_text'] = None
                
                # Map dream-related fields (Features)
                field_mappings = {
                    'dream_feelings': ['sentiste al despertar', 'feeling'],
                    'dream_talk': ['hablaste sobre tus sueños'],
                    'dream_write': ['escribiste sobre tus sueños'],
                    'dream_content': ['pensamientos diarios se reflejaron'],
                    'dream_frequency': ['frecuencia tuviste sueños'],
                    'dream_vivid': ['vívidos han sido tus sueños'],
                    'dream_bizarre': ['bizarros han sido tus sueños'],
                    'dream_emotional_tone': ['tono emocional'],
                    'dream_intensity': ['intensas.*emociones']
                }
                
                for unified_name, patterns in field_mappings.items():
                    found = False
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(pattern.lower() in col_str for pattern in patterns):
                            unified_df[unified_name] = df[col].values
                            found = True
                            break
                    if not found:
                        unified_df[unified_name] = None
                
                # Mental health indicators - GAD and PHQ scores
                gad_score_col = None
                phq_score_col = None
                for col in df.columns:
                    col_str = str(col).lower()
                    if 'gad' in col_str and ('score' in col_str or 'final' in col_str):
                        if 'score' in col_str:
                            gad_score_col = col
                    if 'phq' in col_str and ('score' in col_str or 'final' in col_str):
                        if 'score' in col_str:
                            phq_score_col = col
                
                if gad_score_col:
                    unified_df['gad_total'] = pd.to_numeric(df[gad_score_col], errors='coerce').values
                else:
                    unified_df['gad_total'] = None
                
                if phq_score_col:
                    unified_df['phq_total'] = pd.to_numeric(df[phq_score_col], errors='coerce').values
                else:
                    unified_df['phq_total'] = None
                
                # Demographic information
                demo_mappings = {
                    'age': ['edad'],
                    'education': ['educativo', 'educación'],
                    'student': ['estudiante'],
                    'gender': ['género', 'gender']
                }
                
                for unified_name, patterns in demo_mappings.items():
                    found = False
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(pattern.lower() in col_str for pattern in patterns):
                            unified_df[unified_name] = df[col].values
                            found = True
                            break
                    if not found:
                        unified_df[unified_name] = None
                
                # Sleep information
                sleep_mappings = {
                    'sleep_quality': ['calidad.*sueño', 'sleepq'],
                    'sleep_hours': ['horas.*dormiste', 'hoursofsleep'],
                    'sleep_disturbed': ['interrumpido.*sueño', 'sleep_interrupted']
                }
                
                for unified_name, patterns in sleep_mappings.items():
                    found = False
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(re.search(pattern.lower(), col_str) for pattern in patterns):
                            unified_df[unified_name] = df[col].values
                            found = True
                            break
                    if not found:
                        unified_df[unified_name] = None
                
                all_data.append(unified_df)
                print(f"  Loaded {len(unified_df)} records (Features only)")
                
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            print(f"\nArgentina DATA FORM total: {len(result)} records (Features only)")
            return result
        else:
            return pd.DataFrame()
    
    def load_argentina_dream_reports(self):
        """Load Argentina Dream Reports data - Dream Memory only (English and Spanish versions)"""
        print("\n" + "=" * 80)
        print("Loading Argentina Dream Reports data (Dream Memory only)...")
        print("=" * 80)
        
        all_data = []
        
        if not self.argentina_reports_dir.exists():
            print("Dream Reports folder does not exist")
            return pd.DataFrame()
        
        # Check openpyxl version, try to upgrade if version is too old
        openpyxl_ok = False
        try:
            import openpyxl
            openpyxl_version = openpyxl.__version__
            version_parts = [int(x) for x in openpyxl_version.split('.')]
            if version_parts >= [3, 1, 0]:
                openpyxl_ok = True
            else:
                print(f"Warning: openpyxl version {openpyxl_version} is too low, needs 3.1.0 or higher")
                print("Trying to upgrade openpyxl...")
                import subprocess
                import sys
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "openpyxl"], 
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    import importlib
                    importlib.reload(openpyxl)
                    openpyxl_version = openpyxl.__version__
                    version_parts = [int(x) for x in openpyxl_version.split('.')]
                    if version_parts >= [3, 1, 0]:
                        openpyxl_ok = True
                        print(f"openpyxl upgraded to version {openpyxl_version}")
                except:
                    print("Cannot automatically upgrade openpyxl, please run: pip install --upgrade openpyxl")
        except ImportError:
            print("Warning: openpyxl not installed, trying to install...")
            import subprocess
            import sys
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import openpyxl
                openpyxl_ok = True
                print("openpyxl installed successfully")
            except:
                print("Cannot install openpyxl, please run: pip install openpyxl")
        
        if not openpyxl_ok:
            print("Cannot read Excel files, skipping Argentina Dream Reports loading")
            return pd.DataFrame()
        
        # Organize files by session, keeping English and Spanish versions
        sessions = {}
        for excel_file in sorted(self.argentina_reports_dir.glob("*.xlsx")):
            session_match = re.search(r'Session(\d+)', excel_file.name)
            if session_match:
                session_num = int(session_match.group(1))
                if session_num not in sessions:
                    sessions[session_num] = {}
                
                if 'English' in excel_file.name:
                    sessions[session_num]['english'] = excel_file
                elif 'Spanish' in excel_file.name:
                    sessions[session_num]['spanish'] = excel_file
        
        # Process each session, loading English and Spanish versions separately
        for session_num in sorted(sessions.keys()):
            session_files = sessions[session_num]
            
            # Process English version
            if 'english' in session_files:
                excel_file = session_files['english']
                language = 'English'
                dream_col = f'Dream_recall_en_{session_num}'
                
                print(f"\nProcessing Session {session_num} (English): {excel_file.name}")
                try:
                    df = pd.read_excel(excel_file)
                    num_rows = len(df)
                    unified_df = pd.DataFrame(index=range(num_rows))
                    
                    # Basic information
                    unified_df['source_file'] = excel_file.name
                    unified_df['country'] = 'Argentina'
                    unified_df['language'] = language
                    unified_df['timepoint'] = session_num
                    
                    # Participant ID - normalize to handle both 'code' and 'codigo'
                    if 'code' in df.columns:
                        unified_df['participant_id'] = df['code'].astype(str).str.strip().values
                    elif 'codigo' in df.columns:
                        unified_df['participant_id'] = df['codigo'].astype(str).str.strip().values
                    else:
                        print(f"  Warning: Could not find participant ID column")
                        unified_df['participant_id'] = None
                    
                    # Dream text - this is the main purpose of Dream Reports
                    if dream_col in df.columns:
                        unified_df['dream_text'] = df[dream_col].apply(self.clean_dream_text).values
                    else:
                        # Try to find any column containing 'dream'
                        dream_cols = [col for col in df.columns if 'dream' in str(col).lower()]
                        if dream_cols:
                            unified_df['dream_text'] = df[dream_cols[0]].apply(self.clean_dream_text).values
                        else:
                            unified_df['dream_text'] = None
                    
                    # NOTE: Features should come from DATA FORM files, not Dream Reports
                    # Set all feature fields to None
                    unified_df['dream_feelings'] = None
                    unified_df['dream_talk'] = None
                    unified_df['dream_write'] = None
                    unified_df['dream_content'] = None
                    unified_df['dream_frequency'] = None
                    unified_df['dream_vivid'] = None
                    unified_df['dream_bizarre'] = None
                    unified_df['dream_emotional_tone'] = None
                    unified_df['dream_intensity'] = None
                    unified_df['gad_total'] = None
                    unified_df['phq_total'] = None
                    unified_df['age'] = None
                    unified_df['education'] = None
                    unified_df['student'] = None
                    unified_df['gender'] = None
                    unified_df['sleep_quality'] = None
                    unified_df['sleep_hours'] = None
                    unified_df['sleep_disturbed'] = None
                    
                    all_data.append(unified_df)
                    print(f"  Loaded {len(unified_df)} records")
                    print(f"  Records with dream text: {unified_df['dream_text'].notna().sum()}")
                    
                except Exception as e:
                    print(f"  Error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Process Spanish version
            if 'spanish' in session_files:
                excel_file = session_files['spanish']
                language = 'Spanish'
                dream_col = f'Dream_recall_spa_{session_num}'
                
                print(f"\nProcessing Session {session_num} (Spanish): {excel_file.name}")
                try:
                    df = pd.read_excel(excel_file)
                    num_rows = len(df)
                    unified_df = pd.DataFrame(index=range(num_rows))
                    
                    # Basic information
                    unified_df['source_file'] = excel_file.name
                    unified_df['country'] = 'Argentina'
                    unified_df['language'] = language
                    unified_df['timepoint'] = session_num
                    
                    # Participant ID - normalize to handle both 'code' and 'codigo'
                    if 'code' in df.columns:
                        unified_df['participant_id'] = df['code'].astype(str).str.strip().values
                    elif 'codigo' in df.columns:
                        unified_df['participant_id'] = df['codigo'].astype(str).str.strip().values
                    else:
                        print(f"  Warning: Could not find participant ID column")
                        unified_df['participant_id'] = None
                    
                    # Dream text - this is the main purpose of Dream Reports
                    if dream_col in df.columns:
                        unified_df['dream_text'] = df[dream_col].apply(self.clean_dream_text).values
                    else:
                        # Try to find any column containing 'dream' or 'sueño'
                        dream_cols = [col for col in df.columns if 'dream' in str(col).lower() or 'sueño' in str(col).lower()]
                        if dream_cols:
                            unified_df['dream_text'] = df[dream_cols[0]].apply(self.clean_dream_text).values
                        else:
                            unified_df['dream_text'] = None
                    
                    # NOTE: Features should come from DATA FORM files, not Dream Reports
                    # Set all feature fields to None
                    unified_df['dream_feelings'] = None
                    unified_df['dream_talk'] = None
                    unified_df['dream_write'] = None
                    unified_df['dream_content'] = None
                    unified_df['dream_frequency'] = None
                    unified_df['dream_vivid'] = None
                    unified_df['dream_bizarre'] = None
                    unified_df['dream_emotional_tone'] = None
                    unified_df['dream_intensity'] = None
                    unified_df['gad_total'] = None
                    unified_df['phq_total'] = None
                    unified_df['age'] = None
                    unified_df['education'] = None
                    unified_df['student'] = None
                    unified_df['gender'] = None
                    unified_df['sleep_quality'] = None
                    unified_df['sleep_hours'] = None
                    unified_df['sleep_disturbed'] = None
                    
                    all_data.append(unified_df)
                    print(f"  Loaded {len(unified_df)} records")
                    print(f"  Records with dream text: {unified_df['dream_text'].notna().sum()}")
                    
                except Exception as e:
                    print(f"  Error: {e}")
                    import traceback
                    traceback.print_exc()
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            print(f"\nArgentina Dream Reports total: {len(result)} records (Dream Memory only)")
            print(f"Records with dream text: {result['dream_text'].notna().sum()}")
            return result
        else:
            return pd.DataFrame()
    
    def integrate_all_data(self):
        """Integrate all data"""
        print("\n" + "=" * 80)
        print("Starting data integration...")
        print("=" * 80)
        
        # Load USA data (contains both Features and Dream Memory)
        usa_data = self.load_usa_data()
        
        # Load Argentina DATA FORM data (Features only)
        argentina_data_forms = self.load_argentina_data_forms()
        
        # Load Argentina Dream Reports data (Dream Memory only, English and Spanish)
        argentina_dream_reports = self.load_argentina_dream_reports()
        
        # Merge Argentina Features and Dream Memory
        argentina_data = self._merge_argentina_features_and_dreams(
            argentina_data_forms, argentina_dream_reports
        )
        
        # Combine USA and Argentina data
        if not usa_data.empty and not argentina_data.empty:
            # Ensure columns are consistent
            all_columns = set(usa_data.columns) | set(argentina_data.columns)
            for col in all_columns:
                if col not in usa_data.columns:
                    usa_data[col] = None
                if col not in argentina_data.columns:
                    argentina_data[col] = None
            
            integrated_data = pd.concat([usa_data, argentina_data], ignore_index=True)
        elif not usa_data.empty:
            integrated_data = usa_data
        elif not argentina_data.empty:
            integrated_data = argentina_data
        else:
            print("Warning: no data loaded")
            return pd.DataFrame()
        
        print("\n" + "=" * 80)
        print("Data integration completed")
        print("=" * 80)
        print(f"Total records: {len(integrated_data)}")
        print(f"Records with dream text: {integrated_data['dream_text'].notna().sum()}")
        print(f"USA records: {(integrated_data['country'] == 'USA').sum()}")
        print(f"Argentina records: {(integrated_data['country'] == 'Argentina').sum()}")
        
        return integrated_data
    
    def _merge_argentina_features_and_dreams(self, features_df, dreams_df):
        """
        Merge Argentina Features (from DATA FORM) and Dream Memory (from Dream Reports)
        based on participant_id and timepoint.
        
        Strategy:
        1. For each Dream Memory record (English and Spanish), try to find matching Features
        2. If match found: merge Features into Dream Memory record
        3. If no match: keep Dream Memory record with Features as None
        4. Also keep Features records that don't have matching Dream Memory (for completeness)
        """
        print("\n" + "=" * 80)
        print("Merging Argentina Features and Dream Memory...")
        print("=" * 80)
        
        if features_df.empty and dreams_df.empty:
            return pd.DataFrame()
        
        if features_df.empty:
            print("  No Features data, returning Dream Memory only")
            return dreams_df
        
        if dreams_df.empty:
            print("  No Dream Memory data, returning Features only")
            return features_df
        
        # Normalize participant_id for matching
        features_df = features_df.copy()
        dreams_df = dreams_df.copy()
        
        features_df['participant_id'] = features_df['participant_id'].astype(str).str.strip()
        dreams_df['participant_id'] = dreams_df['participant_id'].astype(str).str.strip()
        
        # Ensure timepoint is numeric
        features_df['timepoint'] = pd.to_numeric(features_df['timepoint'], errors='coerce')
        dreams_df['timepoint'] = pd.to_numeric(dreams_df['timepoint'], errors='coerce')
        
        # Create merge keys
        features_df['merge_key'] = features_df['participant_id'] + '_' + features_df['timepoint'].astype(str)
        dreams_df['merge_key'] = dreams_df['participant_id'] + '_' + dreams_df['timepoint'].astype(str)
        
        # Get all feature columns (excluding basic info and dream_text)
        feature_columns = [
            'dream_feelings', 'dream_talk', 'dream_write', 'dream_content',
            'dream_frequency', 'dream_vivid', 'dream_bizarre', 
            'dream_emotional_tone', 'dream_intensity',
            'gad_total', 'phq_total',
            'age', 'education', 'student', 'gender',
            'sleep_quality', 'sleep_hours', 'sleep_disturbed'
        ]
        
        # Merge: left join on dreams_df to preserve all Dream Memory records
        # This ensures we keep both English and Spanish versions
        # Select only feature columns from features_df to avoid column conflicts
        features_to_merge = features_df[['merge_key'] + feature_columns].copy()
        
        merged_df = dreams_df.merge(
            features_to_merge,
            on='merge_key',
            how='left',
            suffixes=('', '_features')
        )
        
        # Fill in feature columns from the merge
        for col in feature_columns:
            if col + '_features' in merged_df.columns:
                # Use merged values where available, otherwise keep original None from dreams_df
                # dreams_df columns should be None, but we prioritize features_df values
                merged_df[col] = merged_df[col + '_features'].where(
                    merged_df[col + '_features'].notna(), 
                    merged_df[col]
                )
                merged_df = merged_df.drop(columns=[col + '_features'])
        
        # Drop merge_key
        merged_df = merged_df.drop(columns=['merge_key'])
        
        # Also add Features records that don't have matching Dream Memory
        # (for cases where Features exist but no Dream Memory was reported)
        features_without_dreams = features_df[
            ~features_df['merge_key'].isin(dreams_df['merge_key'])
        ].copy()
        
        if not features_without_dreams.empty:
            # These records have Features but no Dream Memory
            features_without_dreams = features_without_dreams.drop(columns=['merge_key'])
            # dream_text is already None from load_argentina_data_forms
            merged_df = pd.concat([merged_df, features_without_dreams], ignore_index=True)
            print(f"  Added {len(features_without_dreams)} Features records without Dream Memory")
        
        print(f"  Merged {len(merged_df)} Argentina records")
        print(f"  Records with Features: {merged_df[feature_columns[0]].notna().sum()}")
        print(f"  Records with Dream Memory: {merged_df['dream_text'].notna().sum()}")
        print(f"  Records with both: {(merged_df['dream_text'].notna() & merged_df[feature_columns[0]].notna()).sum()}")
        
        return merged_df
    
    def preprocess_data(self, df):
        """Preprocess data"""
        print("\n" + "=" * 80)
        print("Starting data preprocessing...")
        print("=" * 80)
        
        # Remove records without dream text (if this is the main analysis target)
        original_count = len(df)
        df = df[df['dream_text'].notna()].copy()
        removed_count = original_count - len(df)
        print(f"Removed {removed_count} records without dream text")
        
        # Data cleaning
        print("\nData cleaning:")
        
        # Clean participant_id
        if 'participant_id' in df.columns:
            df['participant_id'] = df['participant_id'].astype(str).str.strip()
            df['participant_id'] = df['participant_id'].replace('nan', None)
        
        # Ensure timepoint is an integer
        if 'timepoint' in df.columns:
            df['timepoint'] = pd.to_numeric(df['timepoint'], errors='coerce')
        
        # Statistics
        print(f"\nPost-processing statistics:")
        print(f"  Total records: {len(df)}")
        print(f"  Unique participants: {df['participant_id'].nunique() if 'participant_id' in df.columns else 'N/A'}")
        print(f"  Country distribution:")
        print(df['country'].value_counts().to_string())
        print(f"\n  Timepoint distribution:")
        print(df['timepoint'].value_counts().sort_index().to_string())
        print(f"\n  Dream text length statistics:")
        text_lengths = df['dream_text'].str.len()
        print(f"    Average length: {text_lengths.mean():.1f} characters")
        print(f"    Median: {text_lengths.median():.1f} characters")
        print(f"    Shortest: {text_lengths.min()} characters")
        print(f"    Longest: {text_lengths.max()} characters")
        
        return df
    
    def save_integrated_data(self, df, output_file=None):
        """Save integrated data"""
        if output_file is None:
            output_file = self.base_dir / "integrated_dream_data.csv"
        
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\nIntegrated data saved to: {output_file}")
        
        # Save as JSON format (for metadata)
        json_file = output_file.with_suffix('.json')
        metadata = {
            'total_records': len(df),
            'countries': df['country'].value_counts().to_dict(),
            'timepoints': df['timepoint'].value_counts().to_dict(),
            'columns': list(df.columns),
            'created_at': datetime.now().isoformat()
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Metadata saved to: {json_file}")
        
        return output_file


def main():
    """Main function"""
    integrator = DreamDataIntegrator()
    
    # Integrate data
    integrated_data = integrator.integrate_all_data()
    
    if integrated_data.empty:
        print("Error: no data to integrate")
        return
    
    # Preprocess data
    processed_data = integrator.preprocess_data(integrated_data)
    
    # Save data
    integrator.save_integrated_data(processed_data)
    
    print("\n" + "=" * 80)
    print("Data integration and preprocessing completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()

