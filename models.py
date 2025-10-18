from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    templates = relationship("TableTemplate", back_populates="owner")


class TableTemplate(Base):
    __tablename__ = "table_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    fields = Column(JSON, nullable=False)  # Список полей с их определениями
    validation_rules = Column(JSON, default=dict)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="templates")
    data_tables = relationship("DataTable", back_populates="template")


class DataTable(Base):
    __tablename__ = "data_tables"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    template_id = Column(Integer, ForeignKey("table_templates.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    template = relationship("TableTemplate", back_populates="data_tables")
    records = relationship("DataRecord", back_populates="data_table")


class DataRecord(Base):
    __tablename__ = "data_records"
    
    id = Column(Integer, primary_key=True, index=True)
    data_table_id = Column(Integer, ForeignKey("data_tables.id"))
    data = Column(JSON, nullable=False)  # Все данные записи в JSON
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    data_table = relationship("DataTable", back_populates="records")