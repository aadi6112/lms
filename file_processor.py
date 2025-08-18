# file_processor.py - Enhanced with Config-Driven Architecture (Backward Compatible)
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
    """Enhanced file processor with config-driven field extraction"""
    
    def __init__(self, upload_dir: str = "uploads", config_path: str = "config/field_mappings.json"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.config_path = config_path
        
        # Load configuration (with fallback to original behavior)
        self.config = self.load_config()
        
        # Supported file extensions
        self.supported_extensions = {'.xlsx', '.xls', '.json'}
        
        # Original field mappings (for backward compatibility)
        self.legacy_field_mappings = {
            'número de póliza': 'policy_number',
            'numero de poliza': 'policy_number',
            'policy_number': 'policy_number',
            'poliza': 'policy_number',
            'tipo de endoso': 'endorsement_type',
            'endorsement_type': 'endorsement_type',
            'endoso': 'endorsement_type',
            'versión del endoso': 'endorsement_version',
            'version del endoso': 'endorsement_version',
            'endorsement_version': 'endorsement_version',
            'version': 'endorsement_version',
            'concepto id': 'concepto_id',
            'concepto_id': 'concepto_id',
            'id': 'concepto_id',
        }
    
    def load_config(self) -> Dict:
        """Load configuration with fallback to defaults"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(" Loaded enhanced configuration")
                return config
            else:
                logger.info("⚠ Config file not found, using legacy mode")
                return self.get_default_config()
        except Exception as e:
            logger.error(f" Error loading config: {e}, using legacy mode")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Default configuration for backward compatibility"""
        return {
            "field_mappings": {"spanish_to_english": self.legacy_field_mappings},
            "core_fields": {
                "policy_number": {"label": "Policy Number", "type": "text", "group": "core"},
                "endorsement_type": {"label": "Endorsement Type", "type": "text", "group": "core"},
                "endorsement_version": {"label": "Version", "type": "text", "group": "core"},
                "concepto_id": {"label": "Concepto ID", "type": "text", "group": "core"},
                "status": {"label": "Status", "type": "select", "group": "core"}
            },
            "ui_groups": {
                "core": {"label": "Core Information", "icon": "fas fa-info-circle", "order": 1},
                "other": {"label": "Additional Fields", "icon": "fas fa-plus-circle", "order": 2}
            },
            "validation_rules": {},
            "excel_processing": {"auto_detect_structure": True}
        }
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return the file path"""
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
        
        if file_extension not in self.supported_extensions:
            return False, f"Unsupported file type. Supported: {', '.join(self.supported_extensions)}"
        
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            return False, f"File too large. Maximum size: 50MB"
        
        return True, "File is valid"
    
    def normalize_field_name(self, field_name: str) -> str:
        """Enhanced field name normalization using configuration"""
        if not field_name:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = field_name.lower().strip()
        
        # Get mappings from config
        mappings = self.config.get("field_mappings", {}).get("spanish_to_english", {})
        
        # Check for exact match first
        if normalized in mappings:
            return mappings[normalized]
        
        # Check for partial matches (enhanced)
        for spanish_key, english_key in mappings.items():
            if spanish_key in normalized or normalized in spanish_key:
                return english_key
        
        # Return cleaned field name if no mapping found
        cleaned = normalized.replace(' ', '_').replace('ñ', 'n').replace('ó', 'o').replace('í', 'i').replace('é', 'e').replace('á', 'a')
        return cleaned
    
    def get_field_definition(self, field_name: str) -> Dict:
        """Get field definition from config"""
        core_fields = self.config.get("core_fields", {})
        dynamic_fields = self.config.get("dynamic_field_types", {})
        
        if field_name in core_fields:
            return core_fields[field_name]
        elif field_name in dynamic_fields:
            return dynamic_fields[field_name]
        else:
            # Return default field definition
            return {
                "label": field_name.replace('_', ' ').title(),
                "type": "text",
                "validation": "string",
                "group": "other"
            }
    
    def extract_core_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced core field extraction"""
        core_fields = {}
        core_field_names = self.config.get("core_fields", {}).keys()
        
        for original_key, value in data.items():
            normalized_key = self.normalize_field_name(original_key)
            
            if normalized_key in core_field_names:
                # Clean the value
                if isinstance(value, str):
                    core_fields[normalized_key] = value.strip() if value else None
                else:
                    core_fields[normalized_key] = str(value) if value is not None else None
        
        return core_fields
    
    def organize_fields_by_groups(self, fields: Dict[str, Any]) -> Dict[str, Dict]:
        """Organize fields by UI groups for better display"""
        groups = {}
        ui_groups = self.config.get("ui_groups", {})
        
        for field_name, field_value in fields.items():
            field_def = self.get_field_definition(field_name)
            group_name = field_def.get("group", "other")
            
            if group_name not in groups:
                group_info = ui_groups.get(group_name, {
                    "label": group_name.title(),
                    "icon": "fas fa-list",
                    "order": 999
                })
                groups[group_name] = {
                    "info": group_info,
                    "fields": {}
                }
            
            groups[group_name]["fields"][field_name] = {
                "value": field_value,
                "definition": field_def
            }
        
        # Sort groups by order
        return dict(sorted(groups.items(), key=lambda x: x[1]["info"].get("order", 999)))
    
    def detect_excel_structure(self, df: pd.DataFrame) -> str:
        """Enhanced Excel structure detection"""
        if len(df.columns) < 2:
            return "unknown"
        
        # Get Excel processing config
        excel_config = self.config.get("excel_processing", {})
        field_indicators = excel_config.get("field_indicators", ["campo", "field", "parameter"])
        
        # Check first few rows for field indicators
        first_col = df.iloc[:, 0].astype(str).str.lower()
        second_col = df.iloc[:, 1].astype(str).str.lower()
        
        # Look for field indicators
        has_field_indicators = any(
            any(indicator in val for indicator in field_indicators)
            for val in first_col.head(10) if val and val != 'nan'
        )
        
        # Check if second column has field-like names
        field_names = ['numero', 'tipo', 'version', 'poliza', 'endoso', 'ramo', 'elegibilidad']
        has_field_names = any(
            any(name in val for name in field_names)
            for val in second_col.head(20) if val and val != 'nan'
        )
        
        if has_field_indicators or has_field_names:
            logger.info(" Detected field/value table structure")
            return "field_value_table"
        else:
            logger.info(" Detected record-based structure")
            return "record_based"
    
    def process_excel_file(self, file_path: str) -> Dict[str, Any]:
        """Enhanced Excel processing with config-driven extraction"""
        try:
            logger.info(f"Processing Excel file: {file_path}")
            
            # Read Excel file
            excel_data = pd.read_excel(file_path, sheet_name=None)
            
            result = {
                'file_type': 'excel',
                'sheets': {},
                'endorsements': [],
                'metadata': {
                    'total_sheets': len(excel_data),
                    'processed_at': datetime.now().isoformat(),
                    'config_used': Path(self.config_path).exists()
                }
            }
            
            for sheet_name, df in excel_data.items():
                logger.info(f"Processing sheet: {sheet_name}")
                
                # Clean the dataframe
                df = df.dropna(how='all').fillna('')
                
                # Detect structure
                structure_type = self.detect_excel_structure(df)
                
                # Store sheet info
                result['sheets'][sheet_name] = {
                    'columns': list(df.columns),
                    'row_count': len(df),
                    'structure_type': structure_type
                }
                
                # Extract endorsements based on structure
                if structure_type == "field_value_table":
                    endorsements = self.process_field_value_table(df, sheet_name)
                else:
                    endorsements = self.process_record_based_table(df, sheet_name)
                
                result['endorsements'].extend(endorsements)
            
            logger.info(f" Excel processing complete. Found {len(result['endorsements'])} endorsements")
            return result
            
        except Exception as e:
            logger.error(f" Error processing Excel file: {e}")
            raise Exception(f"Failed to process Excel file: {str(e)}")
    
    def process_field_value_table(self, df: pd.DataFrame, sheet_name: str) -> List[Dict]:
        """Enhanced field/value table processing"""
        endorsements = []
        
        try:
            # Get column indices based on config or defaults
            excel_config = self.config.get("excel_processing", {})
            
            # Find field column (usually B = index 1)
            field_col_index = 1 if len(df.columns) > 1 else 0
            field_column = df.iloc[:, field_col_index]
            
            # Find value columns (usually D onwards = index 3+)
            value_col_start = 3 if len(df.columns) > 3 else 2
            value_columns = df.iloc[:, value_col_start:]
            
            logger.info(f"Processing {len(value_columns.columns)} value columns")
            
            # Process each value column as a separate endorsement
            for col_idx, col_name in enumerate(value_columns.columns):
                endorsement_data = {}
                
                # Extract field/value pairs
                for row_idx, field_name in enumerate(field_column):
                    if pd.isna(field_name) or not str(field_name).strip():
                        continue
                    
                    field_name = str(field_name).strip()
                    
                    # Get corresponding value
                    if row_idx < len(value_columns):
                        field_value = value_columns.iloc[row_idx, col_idx]
                        if not pd.isna(field_value) and str(field_value).strip():
                            normalized_field = self.normalize_field_name(field_name)
                            endorsement_data[normalized_field] = str(field_value).strip()
                
                if endorsement_data:
                    # Extract core fields
                    core_fields = self.extract_core_fields(endorsement_data)
                    
                    # Only create endorsement if we have at least one core field
                    if any(core_fields.values()):
                        endorsement = {
                            'core_fields': core_fields,
                            'all_fields': endorsement_data,
                            'grouped_fields': self.organize_fields_by_groups(endorsement_data),
                            'source_sheet': sheet_name,
                            'source_column': str(col_name),
                            'extraction_method': 'field_value_table',
                            'field_count': len(endorsement_data)
                        }
                        endorsements.append(endorsement)
                        logger.info(f"Created endorsement from column {col_name} with {len(endorsement_data)} fields")
            
        except Exception as e:
            logger.error(f" Error processing field/value table: {e}")
        
        return endorsements
    
    def process_record_based_table(self, df: pd.DataFrame, sheet_name: str) -> List[Dict]:
        """Enhanced record-based table processing"""
        endorsements = []
        
        try:
            for idx, row in df.iterrows():
                # Convert row to dictionary, filtering out empty values
                row_data = {}
                for col, value in row.items():
                    if not pd.isna(value) and str(value).strip():
                        normalized_col = self.normalize_field_name(str(col))
                        row_data[normalized_col] = str(value).strip()
                
                if row_data:
                    # Extract core fields
                    core_fields = self.extract_core_fields(row_data)
                    
                    # Only create endorsement if we have at least one core field
                    if any(core_fields.values()):
                        endorsement = {
                            'core_fields': core_fields,
                            'all_fields': row_data,
                            'grouped_fields': self.organize_fields_by_groups(row_data),
                            'source_sheet': sheet_name,
                            'source_row': idx,
                            'extraction_method': 'record_based',
                            'field_count': len(row_data)
                        }
                        endorsements.append(endorsement)
        
        except Exception as e:
            logger.error(f" Error processing record-based table: {e}")
        
        return endorsements
    
    def process_json_file(self, file_path: str) -> Dict[str, Any]:
        """Enhanced JSON processing (same as before but with config support)"""
        try:
            logger.info(f" Processing JSON file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            result = {
                'file_type': 'json',
                'raw_data': json_data,
                'endorsements': [],
                'metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'config_used': Path(self.config_path).exists()
                }
            }
            
            # Handle different JSON structures
            if isinstance(json_data, list):
                for i, item in enumerate(json_data):
                    endorsement = self.process_json_item(item, i)
                    if endorsement:
                        result['endorsements'].append(endorsement)
            elif isinstance(json_data, dict):
                endorsement = self.process_json_item(json_data, 0)
                if endorsement:
                    result['endorsements'].append(endorsement)
            
            logger.info(f" JSON processing complete. Found {len(result['endorsements'])} endorsements")
            return result
            
        except Exception as e:
            logger.error(f" Error processing JSON file: {e}")
            raise Exception(f"Failed to process JSON file: {str(e)}")
    
    def process_json_item(self, item: Any, index: int) -> Optional[Dict]:
        """Process a single JSON item as an endorsement"""
        if not isinstance(item, dict):
            return None
        
        try:
            # Flatten nested dictionaries if needed
            flattened_data = self.flatten_dict(item)
            
            # Normalize field names
            normalized_data = {}
            for key, value in flattened_data.items():
                normalized_key = self.normalize_field_name(key)
                normalized_data[normalized_key] = str(value) if value is not None else ""
            
            # Extract core fields
            core_fields = self.extract_core_fields(normalized_data)
            
            if any(core_fields.values()):
                return {
                    'core_fields': core_fields,
                    'all_fields': normalized_data,
                    'grouped_fields': self.organize_fields_by_groups(normalized_data),
                    'source_index': index,
                    'extraction_method': 'json_direct',
                    'field_count': len(normalized_data)
                }
        
        except Exception as e:
            logger.error(f"❌ Error processing JSON item: {e}")
        
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
        file_extension = Path(original_filename).suffix.lower()
        
        if file_extension in ['.xlsx', '.xls']:
            return self.process_excel_file(file_path)
        elif file_extension == '.json':
            return self.process_json_file(file_path)
        else:
            raise Exception(f"Unsupported file type: {file_extension}")
    
    def get_field_schema(self) -> Dict[str, Any]:
        """Get the complete field schema for frontend"""
        return {
            'core_fields': self.config.get('core_fields', {}),
            'dynamic_field_types': self.config.get('dynamic_field_types', {}),
            'ui_groups': self.config.get('ui_groups', {}),
            'validation_rules': self.config.get('validation_rules', {}),
            'ui_settings': self.config.get('ui_settings', {})
        }
    
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
                        logger.info(f"🗑 Cleaned up old file: {file_path}")
        
        except Exception as e:
            logger.error(f" Error during cleanup: {e}")

# Create global instance (backward compatible)
file_processor = FileProcessor()

# Example usage and testing
if __name__ == "__main__":
    print(" Testing Enhanced File Processor...")
    
    # Test configuration loading
    print(f" Config loaded: {file_processor.config_path}")
    print(f" Enhanced mode: {Path(file_processor.config_path).exists()}")
    
    # Test field mapping
    test_fields = {
        "Número de póliza": "1618805",
        "Tipo de endoso": "Maternidad",
        "Versión del endoso": "904",
        "Ramo": "Salud",
        "Elegibilidad": "SELF, PARTNER, CHILD"
    }
    
    print(" Testing field extraction...")
    core_fields = file_processor.extract_core_fields(test_fields)
    grouped_fields = file_processor.organize_fields_by_groups(test_fields)
    
    print(f"Core fields: {core_fields}")
    print(f" Grouped fields: {list(grouped_fields.keys())}")
    print(" Enhanced file processor ready!")
