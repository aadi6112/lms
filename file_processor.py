# file_processor.py - Enhanced File Processor with Multi-Combination Support
import os
import json
import pandas as pd
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import re

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileProcessor:
    """Enhanced file processor with multi-combination support and comprehensive debugging"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Supported file extensions
        self.supported_extensions = {'.xlsx', '.xls', '.json'}
        
        # Enhanced Spanish field mappings (case-insensitive)
        self.core_field_mappings = {
            # Policy number variations
            'número de póliza': 'policy_number',
            'numero de poliza': 'policy_number',
            'numero de póliza': 'policy_number',
            'número de poliza': 'policy_number',
            'policy_number': 'policy_number',
            'poliza': 'policy_number',
            'póliza': 'policy_number',
            
            # Endorsement type variations
            'nombre del endoso': 'endorsement_type',
            'tipo de endoso': 'endorsement_type',
            'endorsement_type': 'endorsement_type',
            'endoso': 'endorsement_type',
            
            # Version variations
            'versión del endoso inicial': 'endorsement_version',
            'version del endoso inicial': 'endorsement_version',
            'versión del endoso': 'endorsement_version',
            'version del endoso': 'endorsement_version',
            'endorsement_version': 'endorsement_version',
            'version': 'endorsement_version',
            'versión': 'endorsement_version'
        }
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return the file path"""
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.upload_dir / unique_filename
        
        try:
            with open(file_path, 'wb') as f:
                f.write(file_content)
            logger.info(f"✅ File saved: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"❌ Error saving file: {e}")
            raise Exception(f"Failed to save file: {str(e)}")
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """Validate file extension and size"""
        file_extension = Path(filename).suffix.lower()
        
        if file_extension not in self.supported_extensions:
            return False, f"Unsupported file type. Supported: {', '.join(self.supported_extensions)}"
        
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            return False, f"File too large. Maximum size: 50MB"
        
        return True, "File is valid"
    
    def detect_excel_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced Excel structure detection with detailed debugging"""
        logger.info("🔍 Starting Excel structure detection...")
        
        structure_info = {
            'type': 'unknown',
            'campo_column': None,
            'data_start_column': None,
            'combination_columns': [],
            'combination_count': 0,
            'debug_info': {}
        }
        
        try:
            logger.info(f"📊 DataFrame shape: {df.shape}")
            logger.info(f"📊 DataFrame columns: {list(df.columns)}")
            
            # Debug: Show first few rows of all columns
            logger.info("📋 First 5 rows sample:")
            for i in range(min(5, len(df))):
                row_data = []
                for j in range(min(6, len(df.columns))):  # Show first 6 columns
                    value = df.iloc[i, j]
                    col_name = df.columns[j] if j < len(df.columns) else f"Col_{j}"
                    row_data.append(f"{col_name}='{value}'")
                logger.info(f"   Row {i}: {', '.join(row_data)}")
            
            # Look for "Campo" in column B (index 1)
            if len(df.columns) > 1:
                logger.info("🔍 Checking Column B for 'Campo' indicators...")
                col_b_values = df.iloc[:, 1].astype(str).str.lower()
                logger.info(f"   Column B values (first 10): {list(col_b_values.head(10))}")
                
                # Check for "campo" or field name patterns
                campo_indicators = ['campo', 'field', 'parameter']
                spanish_field_patterns = ['número', 'nombre', 'versión', 'ramo', 'año']
                
                has_campo = False
                
                # Check for explicit campo indicators
                for indicator in campo_indicators:
                    if any(indicator in val for val in col_b_values.head(10)):
                        has_campo = True
                        logger.info(f"✅ Found '{indicator}' indicator in Column B")
                        break
                
                # Check for Spanish field patterns if no explicit campo found
                if not has_campo:
                    logger.info("🔍 Looking for Spanish field patterns...")
                    spanish_field_count = 0
                    for pattern in spanish_field_patterns:
                        if any(pattern in val for val in col_b_values.head(15)):
                            spanish_field_count += 1
                            logger.info(f"   Found Spanish field pattern: '{pattern}'")
                    
                    if spanish_field_count >= 2:  # At least 2 Spanish patterns
                        has_campo = True
                        logger.info(f"✅ Detected Spanish field structure (found {spanish_field_count} patterns)")
                
                if has_campo:
                    structure_info['campo_column'] = 1
                    structure_info['type'] = 'campo_combinations'
                    
                    # Find data columns starting from column C (index 2) or D (index 3)
                    logger.info("🔍 Checking for combination columns starting from column C...")
                    
                    for col_idx in range(2, len(df.columns)):  # Start from column C
                        col_header = str(df.columns[col_idx]).strip()
                        col_data = df.iloc[:, col_idx].dropna()
                        
                        # Check if column has meaningful data
                        non_empty_data = [str(val).strip() for val in col_data if str(val).strip() and str(val) != 'nan']
                        
                        logger.info(f"   Column {col_idx} ({col_header}): {len(non_empty_data)} meaningful values")
                        
                        if len(non_empty_data) >= 3:  # Has sufficient meaningful data
                            structure_info['combination_columns'].append(col_idx)
                            logger.info(f"   ✅ Added Column {col_idx} as combination column")
                            # Show sample data
                            sample_data = non_empty_data[:3]
                            logger.info(f"      Sample data: {sample_data}")
                    
                    structure_info['combination_count'] = len(structure_info['combination_columns'])
                    structure_info['data_start_column'] = structure_info['combination_columns'][0] if structure_info['combination_columns'] else None
                    
                    logger.info(f"📋 Campo/Combination structure detected:")
                    logger.info(f"   - Campo column: {structure_info['campo_column']}")
                    logger.info(f"   - Combination columns: {structure_info['combination_columns']}")
                    logger.info(f"   - Total combinations: {structure_info['combination_count']}")
                    
                    return structure_info
                else:
                    logger.warning("⚠️ No Campo structure detected in Column B")
            
            # Fallback to record-based processing
            structure_info['type'] = 'record_based'
            logger.info("📊 Falling back to record-based structure")
            
        except Exception as e:
            logger.error(f"❌ Error detecting structure: {e}")
            import traceback
            traceback.print_exc()
            structure_info['type'] = 'unknown'
            structure_info['debug_info']['error'] = str(e)
        
        return structure_info
    
    def extract_core_fields_from_combination(self, combination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced core fields extraction with fuzzy matching"""
        logger.info("🔍 Extracting core fields from combination...")
        logger.info(f"📝 Input data has {len(combination_data)} fields")
        
        # Debug: Show all available fields
        logger.info("📋 Available fields:")
        for field_name, field_value in list(combination_data.items())[:10]:  # Show first 10
            logger.info(f"   '{field_name}' = '{field_value}'")
        
        core_fields = {}
        
        # Enhanced field matching with fuzzy logic
        for spanish_field, english_field in self.core_field_mappings.items():
            logger.debug(f"🔍 Looking for '{spanish_field}' -> '{english_field}'")
            
            # Try exact match first (case-insensitive)
            for field_name, field_value in combination_data.items():
                if spanish_field.lower() == field_name.lower().strip():
                    logger.info(f"✅ Exact match found: '{field_name}' = '{field_value}'")
                    core_fields[english_field] = self.process_field_value(field_value, english_field)
                    break
            
            # If no exact match, try partial matching
            if english_field not in core_fields:
                for field_name, field_value in combination_data.items():
                    field_name_clean = field_name.lower().strip()
                    
                    # Check if key words match
                    if english_field == 'policy_number':
                        if any(word in field_name_clean for word in ['póliza', 'poliza', 'policy']):
                            logger.info(f"✅ Partial match for policy: '{field_name}' = '{field_value}'")
                            core_fields[english_field] = self.process_field_value(field_value, english_field)
                            break
                    elif english_field == 'endorsement_type':
                        if any(word in field_name_clean for word in ['endoso', 'endorsement', 'nombre']):
                            logger.info(f"✅ Partial match for endorsement: '{field_name}' = '{field_value}'")
                            core_fields[english_field] = self.process_field_value(field_value, english_field)
                            break
                    elif english_field == 'endorsement_version':
                        if any(word in field_name_clean for word in ['versión', 'version']):
                            logger.info(f"✅ Partial match for version: '{field_name}' = '{field_value}'")
                            core_fields[english_field] = self.process_field_value(field_value, english_field)
                            break
        
        logger.info(f"✅ Extracted core fields: {core_fields}")
        
        # Validation: Check if we have minimum viable data
        has_policy = core_fields.get('policy_number') and str(core_fields['policy_number']).strip()
        has_type = core_fields.get('endorsement_type') and str(core_fields['endorsement_type']).strip()
        
        logger.info(f"📋 Validation - Has policy: {has_policy}, Has type: {has_type}")
        
        return core_fields
    
    def process_field_value(self, field_value: Any, field_type: str) -> Any:
        """Process field value based on its type"""
        if not field_value or str(field_value).strip() in ['', 'nan', 'None', 'null']:
            return None
        
        if field_type == 'policy_number':
            # Enhanced policy number extraction
            try:
                cleaned_value = str(field_value).strip()
                # Try to extract numbers from the string
                numbers = re.findall(r'\d+', cleaned_value)
                if numbers:
                    return numbers[0]  # Return first number found
                else:
                    return cleaned_value  # Return as-is if no numbers found
            except:
                return str(field_value).strip()
        else:
            return str(field_value).strip()
    
    def process_campo_combinations_structure(self, df: pd.DataFrame, structure_info: Dict) -> List[Dict]:
        """Enhanced Campo/Combinations processing with detailed logging"""
        logger.info("🚀 Processing Campo/Combinations structure...")
        endorsements = []
        
        try:
            campo_col = structure_info['campo_column']
            combination_columns = structure_info['combination_columns']
            
            logger.info(f"📋 Processing setup:")
            logger.info(f"   Campo column: {campo_col}")
            logger.info(f"   Combination columns: {combination_columns}")
            
            # Get field names from Campo column (skip empty rows)
            campo_series = df.iloc[:, campo_col]
            field_names = []
            field_row_mapping = {}
            
            for idx, field in enumerate(campo_series):
                if pd.notna(field) and str(field).strip():
                    clean_field = str(field).strip()
                    field_names.append(clean_field)
                    field_row_mapping[clean_field] = idx
            
            logger.info(f"📝 Found {len(field_names)} field names in Campo column")
            logger.info(f"📝 Field names sample: {field_names[:10]}")
            
            # Process each combination column
            for col_idx, combination_col in enumerate(combination_columns):
                combination_number = col_idx + 1
                combination_data = {}
                
                logger.info(f"🔄 Processing combination {combination_number} (column index {combination_col})...")
                
                # Extract values for this combination
                values_found = 0
                for field_name in field_names:
                    row_idx = field_row_mapping[field_name]
                    
                    try:
                        if row_idx < len(df):
                            field_value = df.iloc[row_idx, combination_col]
                            
                            if pd.notna(field_value) and str(field_value).strip() and str(field_value) != 'nan':
                                clean_value = str(field_value).strip()
                                combination_data[field_name] = clean_value
                                values_found += 1
                                logger.debug(f"   '{field_name}' = '{clean_value}'")
                    except (IndexError, KeyError) as e:
                        logger.debug(f"   Skipped '{field_name}': {e}")
                        continue
                
                logger.info(f"📊 Combination {combination_number}: found {values_found} field values")
                
                # Create endorsement if we have sufficient data
                if values_found >= 3:  # Minimum threshold
                    # Extract core fields
                    core_fields = self.extract_core_fields_from_combination(combination_data)
                    
                    # Check if we have minimum viable endorsement
                    has_required_data = (
                        core_fields.get('policy_number') or 
                        core_fields.get('endorsement_type') or
                        len(combination_data) >= 5
                    )
                    
                    if has_required_data:
                        endorsement = {
                            'combination_number': combination_number,
                            'core_fields': core_fields,
                            'all_fields': combination_data,
                            'spanish_fields': combination_data,
                            'field_count': len(combination_data),
                            'extraction_method': 'campo_combinations',
                            'combination_id': f"combo_{combination_number}",
                            'debug_info': {
                                'values_found': values_found,
                                'column_index': combination_col
                            }
                        }
                        
                        endorsements.append(endorsement)
                        logger.info(f"✅ Created endorsement for combination {combination_number}")
                        logger.info(f"   Core fields: {core_fields}")
                    else:
                        logger.warning(f"⚠️ Combination {combination_number} lacks required data")
                        logger.warning(f"   Core fields: {core_fields}")
                else:
                    logger.warning(f"⚠️ Combination {combination_number} has insufficient data ({values_found} values)")
        
        except Exception as e:
            logger.error(f"❌ Error processing campo combinations: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info(f"✅ Campo processing complete: {len(endorsements)} endorsements created")
        return endorsements
    
    def process_record_based_table(self, df: pd.DataFrame, sheet_name: str) -> List[Dict]:
        """Fallback record-based processing"""
        logger.info(f"📊 Processing record-based table for sheet: {sheet_name}")
        endorsements = []
        
        try:
            for idx, row in df.iterrows():
                row_data = {}
                for col, value in row.items():
                    if pd.notna(value) and str(value).strip() and str(value) != 'nan':
                        row_data[str(col).strip()] = str(value).strip()
                
                if len(row_data) >= 3:  # Minimum data threshold
                    core_fields = self.extract_core_fields_from_combination(row_data)
                    
                    if core_fields.get('policy_number') or core_fields.get('endorsement_type'):
                        endorsement = {
                            'combination_number': 1,
                            'core_fields': core_fields,
                            'all_fields': row_data,
                            'spanish_fields': row_data,
                            'field_count': len(row_data),
                            'extraction_method': 'record_based',
                            'source_row': idx,
                            'combination_id': f"row_{idx}"
                        }
                        endorsements.append(endorsement)
                        logger.info(f"✅ Created endorsement from row {idx}")
        
        except Exception as e:
            logger.error(f"❌ Error processing record-based table: {e}")
        
        logger.info(f"✅ Record-based processing complete: {len(endorsements)} endorsements")
        return endorsements
    
    def process_excel_file(self, file_path: str) -> Dict[str, Any]:
        """Main Excel processing method with comprehensive debugging"""
        logger.info(f"📊 Starting Excel file processing: {file_path}")
        
        try:
            # Read Excel file
            excel_data = pd.read_excel(file_path, sheet_name=None, header=None)
            logger.info(f"📋 Successfully read Excel file with {len(excel_data)} sheets")
            
            result = {
                'file_type': 'excel',
                'sheets': {},
                'endorsements': [],
                'metadata': {
                    'total_sheets': len(excel_data),
                    'processed_at': datetime.now().isoformat(),
                    'processing_method': 'enhanced_debug',
                    'file_path': file_path
                }
            }
            
            for sheet_name, df in excel_data.items():
                logger.info(f"\n📋 Processing sheet: '{sheet_name}'")
                logger.info(f"   Original shape: {df.shape}")
                
                # Clean the dataframe but preserve structure
                df = df.dropna(how='all', axis=0)  # Remove completely empty rows
                df = df.fillna('')  # Fill NaN with empty string
                logger.info(f"   Shape after cleaning: {df.shape}")
                
                # Detect structure
                structure_info = self.detect_excel_structure(df)
                
                # Store sheet information
                result['sheets'][sheet_name] = {
                    'columns': list(df.columns),
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'structure_info': structure_info
                }
                
                # Extract endorsements based on detected structure
                sheet_endorsements = []
                if structure_info['type'] == 'campo_combinations':
                    logger.info("📋 Using Campo/Combinations processing method")
                    sheet_endorsements = self.process_campo_combinations_structure(df, structure_info)
                else:
                    logger.info("📋 Using record-based processing method")
                    sheet_endorsements = self.process_record_based_table(df, sheet_name)
                
                result['endorsements'].extend(sheet_endorsements)
                logger.info(f"📊 Sheet '{sheet_name}' produced {len(sheet_endorsements)} endorsements")
            
            logger.info(f"\n✅ Excel processing COMPLETE!")
            logger.info(f"   Total endorsements created: {len(result['endorsements'])}")
            logger.info(f"   Processing method: {result['metadata']['processing_method']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR processing Excel file: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to process Excel file: {str(e)}")
    
    def process_json_file(self, file_path: str) -> Dict[str, Any]:
        """Process JSON file with combination support"""
        try:
            logger.info(f"📄 Processing JSON file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            result = {
                'file_type': 'json',
                'raw_data': json_data,
                'endorsements': [],
                'metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'processing_method': 'enhanced_json'
                }
            }
            
            # Handle different JSON structures
            if isinstance(json_data, dict):
                if 'combinations' in json_data:
                    combinations = json_data['combinations']
                    for idx, combo in enumerate(combinations):
                        endorsement = self.process_json_combination(combo, idx + 1)
                        if endorsement:
                            result['endorsements'].append(endorsement)
                else:
                    endorsement = self.process_json_combination(json_data, 1)
                    if endorsement:
                        result['endorsements'].append(endorsement)
            elif isinstance(json_data, list):
                for idx, item in enumerate(json_data):
                    endorsement = self.process_json_combination(item, idx + 1)
                    if endorsement:
                        result['endorsements'].append(endorsement)
            
            logger.info(f"✅ JSON processing complete. Found {len(result['endorsements'])} endorsements")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing JSON file: {e}")
            raise Exception(f"Failed to process JSON file: {str(e)}")
    
    def process_json_combination(self, data: Dict, combination_number: int) -> Optional[Dict]:
        """Process a single JSON combination"""
        try:
            if not isinstance(data, dict):
                return None
            
            # Flatten nested dictionaries if needed
            flattened_data = self.flatten_dict(data) if any(isinstance(v, dict) for v in data.values()) else data
            
            # Extract core fields
            core_fields = self.extract_core_fields_from_combination(flattened_data)
            
            if core_fields.get('policy_number') or core_fields.get('endorsement_type'):
                return {
                    'combination_number': combination_number,
                    'core_fields': core_fields,
                    'all_fields': flattened_data,
                    'spanish_fields': flattened_data,
                    'field_count': len(flattened_data),
                    'extraction_method': 'json_combination',
                    'combination_id': f"json_combo_{combination_number}"
                }
        
        except Exception as e:
            logger.error(f"❌ Error processing JSON combination: {e}")
        
        return None
    
    def flatten_dict(self, data: Dict, prefix: str = '', separator: str = '_') -> Dict:
        """Flatten nested dictionary"""
        flattened = {}
        
        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self.flatten_dict(value, new_key, separator))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                for i, item in enumerate(value):
                    flattened.update(self.flatten_dict(item, f"{new_key}_{i}", separator))
            else:
                flattened[new_key] = value
        
        return flattened
    
    def process_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Main method to process any supported file type"""
        logger.info(f"🚀 Starting file processing: {original_filename}")
        file_extension = Path(original_filename).suffix.lower()
        
        if file_extension in ['.xlsx', '.xls']:
            return self.process_excel_file(file_path)
        elif file_extension == '.json':
            return self.process_json_file(file_path)
        else:
            raise Exception(f"Unsupported file type: {file_extension}")


# Create global instance
file_processor = FileProcessor()

if __name__ == "__main__":
    print("🚀 Testing Enhanced File Processor with Complete Multi-Combination Support...")
    print("✨ Enhanced file processor with comprehensive debugging ready!")
    
    # Test with a sample file if provided
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        try:
            result = file_processor.process_file(test_file, test_file)
            print(f"\n📊 Test Results:")
            print(f"   File type: {result['file_type']}")
            print(f"   Endorsements created: {len(result['endorsements'])}")
            print(f"   Processing method: {result['metadata']['processing_method']}")
        except Exception as e:
            print(f"❌ Test failed: {e}")
