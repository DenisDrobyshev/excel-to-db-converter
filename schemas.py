from pydantic import BaseModel, EmailStr, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class FieldType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    EMAIL = "email"

class FieldDefinition(BaseModel):
    name: str
    type: FieldType
    required: bool = False
    unique: bool = False
    validation_rules: List[str] = []

class TableTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fields: List[FieldDefinition]
    validation_rules: Dict[str, Any] = {}

class TableTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    fields: List[Dict[str, Any]]
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class DataTableCreate(BaseModel):
    name: str
    template_id: int

class DataRecordCreate(BaseModel):
    data: Dict[str, Any]

class DataRecordResponse(BaseModel):
    id: int
    data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class ImportResult(BaseModel):
    success: bool
    processed_rows: int
    errors: List[str]
    imported_records: int = 0