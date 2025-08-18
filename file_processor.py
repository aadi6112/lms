# file_processor.py - File Upload & Data Extraction
import os
import json
import pandas as pd
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles file uploads and data extraction for endorsements"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Supported file extensions
        self.supported_extensions = {'.xlsx', '.xls', '.json'}
        
        # Core field mappings for different languages/formats
        self.field_mappings = {
            # Spanish to English mappings from your Excel
            'número de póliza': 'policy_number',
            'numero de poliza': 'policy_number',
            'policy_number': 'policy_number',
            
            
            'tipo de endoso': 'endorsement_type',
            'endorsement_type': 'endorsement_type',
            
            
            'versión del endoso': 'endorsement_version',
            'version del endoso': 'endorsement_version',
            'endorsement_version': 'endorsement_version',
            'version': 'endorsement_version',
            
            'concepto id': 'concepto_id',
            'concepto_id': 'concepto_id',
            'id': 'concepto_id',
            
            # Add more mappings as needed
        }
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return the file path"""
        # Generate unique filename to avoid conflicts
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.upload_dir / unique_filename
        
        try:
            with open(file_path, 'wb') as f:
                f.write(file_content)
            logger.info(f" File saved: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f" Error saving file: {e}")
            raise Exception(f"Failed to save file: {str(e)}")
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """Validate file extension and size"""
        file_extension = Path(filename).suffix.lower()
        
        # Check extension
        if file_extension not in self.supported_extensions:
            return False, f"Unsupported file type. Supported: {', '.join(self.supported_extensions)}"
        
        # Check size (50MB limit)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            return False, f"File too large. Maximum size: 50MB"
        
        return True, "File is valid"
    
    def normalize_field_name(self, field_name: str) -> str:
        """Normalize field names to standard format"""
        if not field_name:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = field_name.lower().strip()
        
        # Check if it matches any of our mappings
        if normalized in self.field_mappings:
            return self.field_mappings[normalized]
        
        # Return the original normalized name if no mapping found
        return normalized.replace(' ', '_')
    
    def extract_core_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract core fields from the data"""
        core_fields = {
            'policy_number': None,
            'endorsement_type': None,
            'endorsement_version': None,
            'endorsement_validity': None,
            'concepto_id': None
        }
        
        # Look for core fields in the data
        for key, value in data.items():
            normalized_key = self.normalize_field_name(key)
            
            if normalized_key in core_fields:
                # Clean the value
                if isinstance(value, str):
                    core_fields[normalized_key] = value.strip() if value else None
                else:
                    core_fields[normalized_key] = str(value) if value is not None else None
        
        return core_fields
    
    def process_excel_file(self, file_path: str) -> Dict[str, Any]:
        """Process Excel file and extract endorsement data"""
        try:
            logger.info(f" Processing Excel file: {file_path}")
            
            # Read Excel file
            excel_data = pd.read_excel(file_path, sheet_name=None)  # Read all sheets
            
            result = {
                'file_type': 'excel',
                'sheets': {},
                'endorsements': [],
                'metadata': {
                    'total_sheets': len(excel_data),
                    'processed_at': datetime.now().isoformat()
                }
            }
            
            for sheet_name, df in excel_data.items():
                logger.info(f" Processing sheet: {sheet_name}")
                
                # Clean the dataframe
                df = df.dropna(how='all')  # Remove empty rows
                df = df.fillna('')  # Replace NaN with empty strings
                
                # Convert to records (list of dictionaries)
                records = df.to_dict('records')
                
                # Store sheet data
                result['sheets'][sheet_name] = {
                    'columns': list(df.columns),
                    'row_count': len(records),
                    'data': records
                }
                
                # Try to extract endorsements from this sheet
                endorsements = self.extract_endorsements_from_records(records, sheet_name)
                result['endorsements'].extend(endorsements)
            
            logger.info(f" Excel processing complete. Found {len(result['endorsements'])} endorsements")
            return result
            
        except Exception as e:
            logger.error(f" Error processing Excel file: {e}")
            raise Exception(f"Failed to process Excel file: {str(e)}")
    
    def extract_endorsements_from_records(self, records: List[Dict], source_sheet: str = None) -> List[Dict]:
        """Extract individual endorsements from records"""
        endorsements = []
        
        # Look for patterns that indicate this is endorsement data
        if not records:
            return endorsements
        
        # Check if this looks like a parameter table (Field/Value structure)
        first_record = records[0]
        columns = list(first_record.keys())
        
        # Pattern 1: Field/Value table (like your screenshot)
        if self.is_field_value_table(records, columns):
            endorsement = self.process_field_value_table(records, source_sheet)
            if endorsement:
                endorsements.append(endorsement)
        
        # Pattern 2: Each row is an endorsement
        else:
            for i, record in enumerate(records):
                endorsement = self.process_record_as_endorsement(record, source_sheet, i)
                if endorsement:
                    endorsements.append(endorsement)
        
        return endorsements
    
    def is_field_value_table(self, records: List[Dict], columns: List[str]) -> bool:
        """Check if this is a field/value table structure"""
        # Look for column names that suggest field/value structure
        field_indicators = ['field', 'campo', 'parameter', 'parametro']
        value_indicators = ['value', 'valor', 'data', 'dato']
        
        column_names_lower = [col.lower() for col in columns]
        
        has_field_column = any(indicator in ' '.join(column_names_lower) for indicator in field_indicators)
        has_value_columns = any(indicator in ' '.join(column_names_lower) for indicator in value_indicators)
        
        # Also check if first column looks like field names and others like values
        if len(columns) >= 2:
            first_col_values = [str(record.get(columns[0], '')).lower() for record in records[:5]]
            field_like_values = any(
                any(term in value for term in ['policy', 'poliza', 'endoso', 'tipo', 'version'])
                for value in first_col_values
            )
            
            return has_field_column or has_value_columns or field_like_values
        
        return False
    
    def process_field_value_table(self, records: List[Dict], source_sheet: str = None) -> Optional[Dict]:
        """Process field/value table structure into endorsement data"""
        try:
            columns = list(records[0].keys()) if records else []
            if len(columns) < 2:
                return None
            
            # Assume first column is field names, others are values
            field_column = columns[0]
            value_columns = columns[1:]
            
            # Extract multiple endorsements (one per value column)
            endorsements = []
            
            for value_col in value_columns:
                endorsement_data = {}
                
                # Build the endorsement data from field/value pairs
                for record in records:
                    field_name = str(record.get(field_column, '')).strip()
                    field_value = record.get(value_col, '')
                    
                    if field_name and field_value:
                        normalized_field = self.normalize_field_name(field_name)
                        endorsement_data[normalized_field] = str(field_value).strip()
                
                if endorsement_data:
                    # Extract core fields
                    core_fields = self.extract_core_fields(endorsement_data)
                    
                    # Create complete endorsement
                    endorsement = {
                        'core_fields': core_fields,
                        'all_fields': endorsement_data,
                        'source_sheet': source_sheet,
                        'source_column': value_col,
                        'extraction_method': 'field_value_table'
                    }
                    
                    endorsements.append(endorsement)
            
            # For now, return the first endorsement (can be modified to handle multiple)
            return endorsements[0] if endorsements else None
            
        except Exception as e:
            logger.error(f" Error processing field/value table: {e}")
            return None
    
    def process_record_as_endorsement(self, record: Dict, source_sheet: str = None, row_index: int = 0) -> Optional[Dict]:
        """Process a single record as an endorsement"""
        try:
            # Filter out empty values
            clean_record = {k: v for k, v in record.items() if v and str(v).strip()}
            
            if not clean_record:
                return None
            
            # Extract core fields
            core_fields = self.extract_core_fields(clean_record)
            
            # Check if we found at least some core fields
            if not any(core_fields.values()):
                return None
            
            endorsement = {
                'core_fields': core_fields,
                'all_fields': clean_record,
                'source_sheet': source_sheet,
                'source_row': row_index,
                'extraction_method': 'record_based'
            }
            
            return endorsement
            
        except Exception as e:
            logger.error(f" Error processing record as endorsement: {e}")
            return None
    
    def process_json_file(self, file_path: str) -> Dict[str, Any]:
        """Process JSON file and extract endorsement data"""
        try:
            logger.info(f" Processing JSON file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            result = {
                'file_type': 'json',
                'raw_data': json_data,
                'endorsements': [],
                'metadata': {
                    'processed_at': datetime.now().isoformat()
                }
            }
            
            # Handle different JSON structures
            if isinstance(json_data, list):
                # Array of endorsements
                for i, item in enumerate(json_data):
                    endorsement = self.process_json_item_as_endorsement(item, i)
                    if endorsement:
                        result['endorsements'].append(endorsement)
            
            elif isinstance(json_data, dict):
                # Single endorsement or nested structure
                endorsement = self.process_json_item_as_endorsement(json_data, 0)
                if endorsement:
                    result['endorsements'].append(endorsement)
            
            logger.info(f" JSON processing complete. Found {len(result['endorsements'])} endorsements")
            return result
            
        except Exception as e:
            logger.error(f" Error processing JSON file: {e}")
            raise Exception(f"Failed to process JSON file: {str(e)}")
    
    def process_json_item_as_endorsement(self, item: Any, index: int = 0) -> Optional[Dict]:
        """Process a JSON item as an endorsement"""
        try:
            if not isinstance(item, dict):
                return None
            
            # Flatten nested dictionaries if needed
            flattened_data = self.flatten_dict(item)
            
            # Extract core fields
            core_fields = self.extract_core_fields(flattened_data)
            
            endorsement = {
                'core_fields': core_fields,
                'all_fields': flattened_data,
                'source_index': index,
                'extraction_method': 'json_direct'
            }
            
            return endorsement
            
        except Exception as e:
            logger.error(f" Error processing JSON item: {e}")
            return None
    
    def flatten_dict(self, data: Dict, prefix: str = '', separator: str = '_') -> Dict:
        """Flatten nested dictionary"""
        flattened = {}
        
        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self.flatten_dict(value, new_key, separator))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Handle list of dictionaries
                for i, item in enumerate(value):
                    flattened.update(self.flatten_dict(item, f"{new_key}_{i}", separator))
            else:
                flattened[new_key] = value
        
        return flattened
    
    def process_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Main method to process any supported file type"""
        file_extension = Path(original_filename).suffix.lower()
        
        if file_extension in ['.xlsx', '.xls']:
            return self.process_excel_file(file_path)
        elif file_extension == '.json':
            return self.process_json_file(file_path)
        else:
            raise Exception(f"Unsupported file type: {file_extension}")
    
    def cleanup_old_files(self, days_old: int = 30):
        """Clean up old uploaded files"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            for file_path in self.upload_dir.glob("*"):
                if file_path.is_file():
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_modified < cutoff_date:
                        file_path.unlink()
                        logger.info(f"Cleaned up old file: {file_path}")
        
        except Exception as e:
            logger.error(f" Error during cleanup: {e}")

# Create global instance
file_processor = FileProcessor()

# Example usage and testing
if __name__ == "__main__":
    print(" Testing File Processor...")
    
    # Test field mapping
    test_fields = {
        "Número de póliza": "1618805",
        "Tipo de endoso": "Maternidad",
        "Versión del endoso": "904"
    }
    
    print(" Testing field extraction...")
    core_fields = file_processor.extract_core_fields(test_fields)
    print(f" Core fields extracted: {core_fields}")
    
    print(" File processor ready!")