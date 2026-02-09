import pandas as pd
import numpy as np
from pathlib import Path
import re
import json
from datetime import datetime

class DreamDataIntegrator:
    
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = Path(__file__).parent
        else:
            self.base_dir = Path(base_dir)
        
        self.usa_dir = self.base_dir / "USA"
        self.argentina_dir = self.base_dir / "Argentina"
        self.argentina_reports_dir = self.argentina_dir / "Dream Reports"
        
        self.field_mapping = {
            'dream_memory': {
                'usa': 'DreamMemory',
                'argentina_english': ['Dream_recall_en_1', 'Dream_recall_en_2', 'Dream_recall_en_3', 
                                     'Dream_recall_en_4', 'Dream_recall_en_5'],
                'argentina_spanish': ['Dream_recall_spa_1', 'Dream_recall_spa_2', 'Dream_recall_spa_3',
                                     'Dream_recall_spa_4', 'Dream_recall_spa_5']
            }
        }
        self.mapping_tables = self._load_mapping_tables()
    
    def _load_mapping_tables(self):
        """Load mapping tables from CSV"""
        mapping_tables = {}
        mapping_csv = self.base_dir / "mapping_table.csv"
        if mapping_csv.exists():
            try:
                df_mapping = pd.read_csv(mapping_csv)
                unique_fields = df_mapping['Field'].unique()
                for field in unique_fields:
                    field_df = df_mapping[df_mapping['Field'] == field].copy()
                    if not field_df.empty:
                        arg_to_natural = {}
                        for _, row in field_df.iterrows():
                            try:
                                arg_code = int(float(row['Argentina_Code']))
                                natural = str(row['Natural_Language']).strip()
                                arg_to_natural[arg_code] = natural
                            except (ValueError, TypeError):
                                continue
                        field_key = str(field).lower().strip()
                        mapping_tables[field_key] = {
                            'arg_to_natural': arg_to_natural,
                            'original_field_name': field
                        }
            except Exception:
                pass
        return mapping_tables
    
    def clean_dream_text(self, text):
        """Clean dream text"""
        if pd.isna(text) or text is None:
            return None
        text = str(text).strip()
        if text.startswith('{') and 'ImportId' in text:
            return None
        meaningless_responses = [
            'no', 'none', 'n/a', 'na', 'no dreams', 'no dream',
            "i don't remember", "don't remember", "can't remember",
            "haven't remembered", "no dreams that i remember",
            "none that i remember", "i haven't remembered",
            "no dreams i remember", "no dreams remembered"
        ]
        text_lower = text.lower()
        if any(response in text_lower for response in meaningless_responses):
            if len(text) < 20:
                return None
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        if len(text) < 20:
            return None
        return text
    
    def extract_timepoint_from_filename(self, filename):
        """Extract timepoint from filename"""
        filename_lower = filename.lower()
        if 'initial' in filename_lower:
            return 1
        elif 'follow up 1' in filename_lower or 'month1' in filename_lower:
            return 2
        elif 'follow up 2' in filename_lower or 'month2' in filename_lower:
            return 3
        elif 'follow up 3' in filename_lower or 'month3' in filename_lower:
            return 4
        elif 'follow up 4' in filename_lower or 'month4' in filename_lower:
            return 5
        elif 'follow up 5' in filename_lower or 'month5' in filename_lower:
            return 6
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
    
    def clean_sleep_hours(self, value):
        """Clean sleep hours and convert to numeric"""
        if pd.isna(value) or value is None:
            return None
        value_str = str(value).strip()
        value_str = value_str.replace('hours', '').replace('hour', '').replace('hrs', '').replace('hr', '')
        value_str = value_str.strip()
        if '-' in value_str:
            parts = value_str.split('-')
            try:
                val1 = float(parts[0].strip())
                val2 = float(parts[1].strip())
                return (val1 + val2) / 2
            except (ValueError, IndexError):
                pass
        import re
        numbers = re.findall(r'\d+\.?\d*', value_str)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return None
    
    def _get_mapping_field_name(self, unified_name):
        """Map unified field name to mapping table field name"""
        unified_lower = str(unified_name).lower().strip()
        field_name_mapping = {
            'dream_feelings': 'Dream_feeling',
            'dream_talk': 'Dream_someone',
            'dream_write': 'Dream_write',
            'dream_content': 'Dream_thoughts',
            'dream_frequency': 'DreamQ_Frequency',
            'dream_vivid': 'DreamQ_Vivid_1',
            'dream_bizarre': 'DreamQ_Bizarre_1',
            'dream_emotional_tone': 'EmotionalTone_1',
            'dream_intensity': 'DreamIntensity_1',
            'sleep_quality': 'SleepQ',
            'sleep_disturbed': 'Sleep_Interrupted',
            'age': 'AGE',
            'education': 'EDUCATION',
            'student': 'STUDENT',
            'gender': 'GENDER'
        }
        if unified_lower in field_name_mapping:
            mapped_name = field_name_mapping[unified_lower]
            if mapped_name.lower() in self.mapping_tables:
                return mapped_name.lower()
        if unified_lower in self.mapping_tables:
            return unified_lower
        unified_no_underscore = unified_lower.replace('_', '')
        for key in self.mapping_tables.keys():
            key_no_underscore = key.lower().replace('_', '')
            if unified_no_underscore == key_no_underscore:
                return key
        return None
    
    def decode_argentina_to_natural(self, value, field_name):
        """Decode Argentina numeric code to natural language"""
        if pd.isna(value) or value is None:
            return None
        mapping_field = self._get_mapping_field_name(field_name)
        if mapping_field is None:
            return str(value).strip()
        try:
            code = int(float(str(value).strip()))
            mapping = self.mapping_tables[mapping_field]['arg_to_natural']
            result = mapping.get(code, None)
            if result is None:
                return str(value).strip()
            return result
        except (ValueError, TypeError):
            return str(value).strip()
    
    def decode_argentina_field(self, series, field_name):
        """Decode pandas Series from Argentina codes to natural language"""
        if series is None or len(series) == 0:
            return None
        return series.apply(lambda x: self.decode_argentina_to_natural(x, field_name))
    
    def normalize_usa_field_value(self, value, field_name):
        """Normalize USA field values"""
        if pd.isna(value) or value is None:
            return None
        value_str = str(value).strip()
        try:
            code = int(float(value_str))
            mapping_field = self._get_mapping_field_name(field_name)
            if mapping_field and mapping_field in self.mapping_tables:
                mapping = self.mapping_tables[mapping_field]['arg_to_natural']
                result = mapping.get(code, None)
                if result is not None:
                    return result
        except (ValueError, TypeError):
            pass
        return value_str
    
    def clean_age_field(self, age_value):
        """Clean age field - remove suffixes"""
        if pd.isna(age_value) or age_value is None:
            return None
        age_str = str(age_value).strip()
        suffixes_to_remove = [
            ' years old', 'years old', ' year old', 'year old',
            ' yo', 'yo', ' y.o.', 'y.o.',
            ' or more', ' or older'
        ]
        for suffix in suffixes_to_remove:
            if age_str.lower().endswith(suffix.lower()):
                age_str = age_str[:-len(suffix)].strip()
        return age_str
    
    
    def load_usa_data(self):
        """Load CSV data from USA folder"""
        demographics_dict = {}
        initial_survey_files = [f for f in self.usa_dir.glob("*.csv") if 'initial' in f.name.lower()]
        for csv_file in initial_survey_files:
            try:
                df_initial = pd.read_csv(csv_file, skiprows=[1])
                participant_id_col = None
                if 'PROLIFIC_PID' in df_initial.columns:
                    participant_id_col = 'PROLIFIC_PID'
                elif 'ProlificID' in df_initial.columns:
                    participant_id_col = 'ProlificID'
                else:
                    participant_id_col = 'ResponseId'
                demo_fields = {
                    'age': 'Demo_Age',
                    'education': 'Demo_Education',
                    'student': 'Demo_Student',
                    'gender': 'Demo_Gender'
                }
                for idx, row in df_initial.iterrows():
                    pid = str(row[participant_id_col]).strip() if pd.notna(row[participant_id_col]) else None
                    if pid and pid != 'nan':
                        demographics_dict[pid] = {}
                        for unified_name, original_name in demo_fields.items():
                            if original_name in df_initial.columns:
                                demographics_dict[pid][unified_name] = row[original_name]
                            else:
                                demographics_dict[pid][unified_name] = None
            except Exception:
                pass
        all_data = []
        csv_files = sorted(self.usa_dir.glob("*.csv"))
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, skiprows=[1])
                timepoint = self.extract_timepoint_from_filename(csv_file.name)
                num_rows = len(df)
                unified_df = pd.DataFrame(index=range(num_rows))
                unified_df['source_file'] = csv_file.name
                unified_df['country'] = 'USA'
                unified_df['language'] = 'English'
                unified_df['timepoint'] = timepoint
                participant_id_col = None
                if 'PROLIFIC_PID' in df.columns:
                    participant_id_col = 'PROLIFIC_PID'
                    unified_df['participant_id'] = df['PROLIFIC_PID']
                elif 'ProlificID' in df.columns:
                    participant_id_col = 'ProlificID'
                    unified_df['participant_id'] = df['ProlificID']
                else:
                    participant_id_col = 'ResponseId'
                    unified_df['participant_id'] = df.get('ResponseId', None)
                if 'DreamMemory' in df.columns:
                    unified_df['dream_text'] = df['DreamMemory'].apply(self.clean_dream_text)
                else:
                    unified_df['dream_text'] = None
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
                        unified_df[unified_name] = df[original_name].apply(
                            lambda x: self.normalize_usa_field_value(x, unified_name)
                        )
                    else:
                        unified_df[unified_name] = None
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
                demo_fields = {
                    'age': 'Demo_Age',
                    'education': 'Demo_Education',
                    'student': 'Demo_Student',
                    'gender': 'Demo_Gender'
                }
                for unified_name, original_name in demo_fields.items():
                    if original_name in df.columns:
                        unified_df[unified_name] = df[original_name].apply(
                            lambda x: self.normalize_usa_field_value(x, unified_name)
                        )
                    else:
                        unified_df[unified_name] = None
                for idx, row in unified_df.iterrows():
                    pid = str(row['participant_id']).strip() if pd.notna(row['participant_id']) else None
                    if pid and pid != 'nan' and pid in demographics_dict:
                        for demo_field in ['age', 'education', 'student', 'gender']:
                            if pd.isna(unified_df.loc[idx, demo_field]) or unified_df.loc[idx, demo_field] is None:
                                value = demographics_dict[pid].get(demo_field, None)
                                unified_df.loc[idx, demo_field] = self.normalize_usa_field_value(value, demo_field) if value else None
                sleep_fields = {
                    'sleep_quality': 'Sleep_Quality',
                    'sleep_hours': 'Sleep_Hours',
                    'sleep_disturbed': 'Sleep_Disturbed'
                }
                for unified_name, original_name in sleep_fields.items():
                    if original_name in df.columns:
                        if unified_name == 'sleep_hours':
                            unified_df[unified_name] = df[original_name].apply(self.clean_sleep_hours)
                        else:
                            unified_df[unified_name] = df[original_name].apply(
                                lambda x: self.normalize_usa_field_value(x, unified_name)
                            )
                    else:
                        unified_df[unified_name] = None
                all_data.append(unified_df)
            except Exception:
                pass
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def load_argentina_data_forms(self):
        """Load Argentina DATA FORM files - Features only"""
        all_data = []
        if not self.argentina_dir.exists():
            return pd.DataFrame()
        try:
            import openpyxl
        except ImportError:
            return pd.DataFrame()
        data_form_files = sorted([f for f in self.argentina_dir.glob("DATA FORM *.xlsx")])
        for excel_file in data_form_files:
            timepoint_match = re.search(r'FORM (\d+)', excel_file.name)
            if timepoint_match:
                timepoint = int(timepoint_match.group(1))
            else:
                continue
            try:
                df = pd.read_excel(excel_file, skiprows=[0])
                num_rows = len(df)
                unified_df = pd.DataFrame(index=range(num_rows))
                unified_df['source_file'] = excel_file.name
                unified_df['country'] = 'Argentina'
                unified_df['language'] = 'Spanish'
                unified_df['timepoint'] = timepoint
                participant_id_col = None
                for col in df.columns:
                    col_lower = str(col).lower()
                    if col_lower == 'codigo' or col_lower == 'código' or col_lower == 'code':
                        participant_id_col = col
                        break
                if participant_id_col:
                    unified_df['participant_id'] = df[participant_id_col].astype(str).str.strip().values
                else:
                    unified_df['participant_id'] = None
                unified_df['dream_text'] = None
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
                            unified_df[unified_name] = self.decode_argentina_field(df[col], unified_name).values
                            found = True
                            break
                    if not found:
                        unified_df[unified_name] = None
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
                            unified_df[unified_name] = df[col].apply(
                                lambda x: self.decode_argentina_to_natural(x, unified_name)
                            ).values
                            found = True
                            break
                    if not found:
                        unified_df[unified_name] = None
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
                            if unified_name == 'sleep_hours':
                                unified_df[unified_name] = df[col].apply(self.clean_sleep_hours).values
                            else:
                                unified_df[unified_name] = self.decode_argentina_field(df[col], unified_name).values
                            found = True
                            break
                    if not found:
                        unified_df[unified_name] = None
                
                all_data.append(unified_df)
            except Exception:
                pass
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def load_argentina_dream_reports(self):
        """Load Argentina Dream Reports - Dream Memory only"""
        all_data = []
        if not self.argentina_reports_dir.exists():
            return pd.DataFrame()
        try:
            import openpyxl
        except ImportError:
            return pd.DataFrame()
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
        feature_fields = ['dream_feelings', 'dream_talk', 'dream_write', 'dream_content',
                         'dream_frequency', 'dream_vivid', 'dream_bizarre',
                         'dream_emotional_tone', 'dream_intensity',
                         'gad_total', 'phq_total', 'age', 'education', 'student', 'gender',
                         'sleep_quality', 'sleep_hours', 'sleep_disturbed']
        for session_num in sorted(sessions.keys()):
            session_files = sessions[session_num]
            if 'english' in session_files:
                excel_file = session_files['english']
                language = 'English'
                dream_col = f'Dream_recall_en_{session_num}'
                try:
                    df = pd.read_excel(excel_file)
                    num_rows = len(df)
                    unified_df = pd.DataFrame(index=range(num_rows))
                    unified_df['source_file'] = excel_file.name
                    unified_df['country'] = 'Argentina'
                    unified_df['language'] = language
                    unified_df['timepoint'] = session_num
                    if 'code' in df.columns:
                        unified_df['participant_id'] = df['code'].astype(str).str.strip().values
                    elif 'codigo' in df.columns:
                        unified_df['participant_id'] = df['codigo'].astype(str).str.strip().values
                    else:
                        unified_df['participant_id'] = None
                    if dream_col in df.columns:
                        unified_df['dream_text'] = df[dream_col].apply(self.clean_dream_text).values
                    else:
                        dream_cols = [col for col in df.columns if 'dream' in str(col).lower()]
                        if dream_cols:
                            unified_df['dream_text'] = df[dream_cols[0]].apply(self.clean_dream_text).values
                        else:
                            unified_df['dream_text'] = None
                    for field in feature_fields:
                        unified_df[field] = None
                    all_data.append(unified_df)
                except Exception:
                    pass
            if 'spanish' in session_files:
                excel_file = session_files['spanish']
                language = 'Spanish'
                dream_col = f'Dream_recall_spa_{session_num}'
                try:
                    df = pd.read_excel(excel_file)
                    num_rows = len(df)
                    unified_df = pd.DataFrame(index=range(num_rows))
                    unified_df['source_file'] = excel_file.name
                    unified_df['country'] = 'Argentina'
                    unified_df['language'] = language
                    unified_df['timepoint'] = session_num
                    if 'code' in df.columns:
                        unified_df['participant_id'] = df['code'].astype(str).str.strip().values
                    elif 'codigo' in df.columns:
                        unified_df['participant_id'] = df['codigo'].astype(str).str.strip().values
                    else:
                        unified_df['participant_id'] = None
                    if dream_col in df.columns:
                        unified_df['dream_text'] = df[dream_col].apply(self.clean_dream_text).values
                    else:
                        dream_cols = [col for col in df.columns if 'dream' in str(col).lower() or 'sueño' in str(col).lower()]
                        if dream_cols:
                            unified_df['dream_text'] = df[dream_cols[0]].apply(self.clean_dream_text).values
                        else:
                            unified_df['dream_text'] = None
                    for field in feature_fields:
                        unified_df[field] = None
                    all_data.append(unified_df)
                except Exception:
                    pass
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def integrate_all_data(self):
        """Integrate all data"""
        usa_data = self.load_usa_data()
        argentina_data_forms = self.load_argentina_data_forms()
        argentina_dream_reports = self.load_argentina_dream_reports()
        argentina_data = self._merge_argentina_features_and_dreams(
            argentina_data_forms, argentina_dream_reports
        )
        if not usa_data.empty and not argentina_data.empty:
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
            return pd.DataFrame()
        integrated_data = self._apply_argentina_mappings(integrated_data)
        integrated_data = self._normalize_usa_data(integrated_data)
        integrated_data = self._clean_age_fields(integrated_data)
        return integrated_data
    
    def _apply_argentina_mappings(self, df):
        """Apply mapping to Argentina data fields"""
        df = df.copy()
        argentina_mask = df['country'] == 'Argentina'
        fields_to_map = [
            'dream_feelings', 'dream_talk', 'dream_write', 'dream_content',
            'dream_frequency', 'dream_vivid', 'dream_bizarre',
            'dream_emotional_tone', 'dream_intensity',
            'age', 'education', 'student', 'gender',
            'sleep_quality', 'sleep_disturbed'
        ]
        for field in fields_to_map:
            if field not in df.columns:
                continue
            arg_data = df.loc[argentina_mask, field]
            if arg_data.notna().sum() == 0:
                continue
            numeric_count = 0
            for val in arg_data.dropna().head(100):
                try:
                    float(str(val))
                    numeric_count += 1
                except:
                    pass
            if numeric_count > len(arg_data.dropna().head(100)) * 0.5:
                df.loc[argentina_mask, field] = self.decode_argentina_field(
                    df.loc[argentina_mask, field], field
                )
        return df
    
    def _normalize_usa_data(self, df):
        """Normalize USA data"""
        df = df.copy()
        usa_mask = df['country'] == 'USA'
        fields_to_normalize = [
            'dream_feelings', 'dream_talk', 'dream_write', 'dream_content',
            'dream_frequency', 'dream_vivid', 'dream_bizarre',
            'dream_emotional_tone', 'dream_intensity',
            'sleep_quality', 'sleep_disturbed'
        ]
        for field in fields_to_normalize:
            if field not in df.columns:
                continue
            usa_data = df.loc[usa_mask, field]
            if usa_data.notna().sum() == 0:
                continue
            numeric_count = 0
            for val in usa_data.dropna().head(100):
                try:
                    float(str(val))
                    numeric_count += 1
                except:
                    pass
            if numeric_count > 0:
                df.loc[usa_mask, field] = df.loc[usa_mask, field].apply(
                    lambda x: self.normalize_usa_field_value(x, field)
                )
        return df
    
    def _clean_age_fields(self, df):
        """Clean age fields"""
        df = df.copy()
        if 'age' in df.columns:
            df['age'] = df['age'].apply(self.clean_age_field)
        return df
    
    def _merge_argentina_features_and_dreams(self, features_df, dreams_df):
        """Merge Argentina Features and Dream Memory"""
        if features_df.empty and dreams_df.empty:
            return pd.DataFrame()
        if features_df.empty:
            return dreams_df
        if dreams_df.empty:
            return features_df
        features_df = features_df.copy()
        dreams_df = dreams_df.copy()
        features_df['participant_id'] = features_df['participant_id'].astype(str).str.strip()
        dreams_df['participant_id'] = dreams_df['participant_id'].astype(str).str.strip()
        features_df['timepoint'] = pd.to_numeric(features_df['timepoint'], errors='coerce')
        dreams_df['timepoint'] = pd.to_numeric(dreams_df['timepoint'], errors='coerce')
        features_df['merge_key'] = features_df['participant_id'] + '_' + features_df['timepoint'].astype(str)
        dreams_df['merge_key'] = dreams_df['participant_id'] + '_' + dreams_df['timepoint'].astype(str)
        feature_columns = [
            'dream_feelings', 'dream_talk', 'dream_write', 'dream_content',
            'dream_frequency', 'dream_vivid', 'dream_bizarre', 
            'dream_emotional_tone', 'dream_intensity',
            'gad_total', 'phq_total',
            'age', 'education', 'student', 'gender',
            'sleep_quality', 'sleep_hours', 'sleep_disturbed'
        ]
        features_to_merge = features_df[['merge_key'] + feature_columns].copy()
        merged_df = dreams_df.merge(
            features_to_merge,
            on='merge_key',
            how='left',
            suffixes=('', '_features')
        )
        for col in feature_columns:
            if col + '_features' in merged_df.columns:
                merged_df[col] = merged_df[col + '_features'].where(
                    merged_df[col + '_features'].notna(), 
                    merged_df[col]
                )
                merged_df = merged_df.drop(columns=[col + '_features'])
        merged_df = merged_df.drop(columns=['merge_key'])
        features_without_dreams = features_df[
            ~features_df['merge_key'].isin(dreams_df['merge_key'])
        ].copy()
        if not features_without_dreams.empty:
            features_without_dreams = features_without_dreams.drop(columns=['merge_key'])
            merged_df = pd.concat([merged_df, features_without_dreams], ignore_index=True)
        return merged_df
    
    def preprocess_data(self, df):
        """Preprocess data"""
        df = df[df['dream_text'].notna()].copy()
        if 'participant_id' in df.columns:
            df['participant_id'] = df['participant_id'].astype(str).str.strip()
            df['participant_id'] = df['participant_id'].replace('nan', None)
        if 'timepoint' in df.columns:
            df['timepoint'] = pd.to_numeric(df['timepoint'], errors='coerce')
        return df
    
    def save_integrated_data(self, df, output_file=None):
        """Save integrated data"""
        if output_file is None:
            output_file = self.base_dir / "integrated_dream_data_v0.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
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
        return output_file


def main():
    """Main function"""
    integrator = DreamDataIntegrator()
    integrated_data = integrator.integrate_all_data()
    if integrated_data.empty:
        return
    processed_data = integrator.preprocess_data(integrated_data)
    integrator.save_integrated_data(processed_data)


if __name__ == "__main__":
    main()

