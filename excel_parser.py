import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime
import json
from schemas import FieldDefinition, FieldType

class ExcelParser:
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
    
    def parse_excel(self, file_path: str, template_fields: List[FieldDefinition]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Парсинг Excel файла и валидация данных по шаблону"""
        try:
            df = pd.read_excel(file_path)
            return self._validate_and_convert_data(df, template_fields)
        except Exception as e:
            raise ValueError(f"Ошибка чтения файла: {str(e)}")
    
    def _validate_and_convert_data(self, df: pd.DataFrame, template_fields: List[FieldDefinition]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Валидация и преобразование данных"""
        errors = []
        valid_records = []
        
        required_fields = [field.name for field in template_fields if field.required]
        
        # Проверка наличия обязательных полей в файле
        missing_columns = set(required_fields) - set(df.columns)
        if missing_columns:
            errors.append(f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}")
            return [], errors
        
        for index, row in df.iterrows():
            record_errors = []
            record_data = {}
            
            for field in template_fields:
                field_name = field.name
                field_value = row.get(field_name)
                
                try:
                    # Преобразование значения в соответствии с типом поля
                    converted_value = self._convert_field_value(field_value, field.type, field.required)
                    
                    # Валидация
                    validation_error = self._validate_field(converted_value, field)
                    if validation_error:
                        record_errors.append(f"Строка {index + 2}, поле '{field_name}': {validation_error}")
                    else:
                        record_data[field_name] = converted_value
                        
                except Exception as e:
                    record_errors.append(f"Строка {index + 2}, поле '{field_name}': {str(e)}")
            
            if not record_errors:
                valid_records.append(record_data)
            else:
                errors.extend(record_errors)
        
        return valid_records, errors
    
    def _convert_field_value(self, value, field_type: FieldType, required: bool):
        """Преобразование значения к нужному типу"""
        if pd.isna(value) or value is None:
            if required:
                raise ValueError("Обязательное поле не может быть пустым")
            return None
        
        try:
            if field_type == FieldType.STRING:
                return str(value)
            elif field_type == FieldType.NUMBER:
                return float(value) if value != '' else None
            elif field_type == FieldType.DATE:
                if isinstance(value, datetime):
                    return value.isoformat()
                return pd.to_datetime(value).isoformat()
            elif field_type == FieldType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes', 'y')
            elif field_type == FieldType.EMAIL:
                email = str(value).strip()
                if '@' not in email:
                    raise ValueError("Некорректный email адрес")
                return email
            return value
        except Exception as e:
            raise ValueError(f"Невозможно преобразовать в {field_type}: {str(e)}")
    
    def _validate_field(self, value, field: FieldDefinition) -> str:
        """Валидация поля по правилам"""
        if field.required and (value is None or value == ''):
            return "Обязательное поле не может быть пустым"
        
        if value is None:
            return ""
        
        # Проверка уникальности будет выполняться на уровне базы данных
        # Здесь можно добавить дополнительные валидации
        
        return ""