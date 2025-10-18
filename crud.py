from sqlalchemy.orm import Session
from sqlalchemy import and_
import models
import schemas
from auth import get_password_hash, verify_password
from typing import List, Optional

# User CRUD
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Template CRUD
def create_table_template(db: Session, template: schemas.TableTemplateCreate, user_id: int):
    db_template = models.TableTemplate(
        name=template.name,
        description=template.description,
        fields=[field.dict() for field in template.fields],
        validation_rules=template.validation_rules,
        created_by=user_id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def get_templates_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.TableTemplate).filter(
        models.TableTemplate.created_by == user_id
    ).offset(skip).limit(limit).all()

def get_template_by_id(db: Session, template_id: int, user_id: int):
    return db.query(models.TableTemplate).filter(
        and_(
            models.TableTemplate.id == template_id,
            models.TableTemplate.created_by == user_id
        )
    ).first()

# Data Table CRUD
def create_data_table(db: Session, data_table: schemas.DataTableCreate, user_id: int):
    db_data_table = models.DataTable(
        name=data_table.name,
        template_id=data_table.template_id,
        created_by=user_id
    )
    db.add(db_data_table)
    db.commit()
    db.refresh(db_data_table)
    return db_data_table

def get_data_tables_by_template(db: Session, template_id: int, user_id: int):
    return db.query(models.DataTable).filter(
        and_(
            models.DataTable.template_id == template_id,
            models.DataTable.created_by == user_id
        )
    ).all()

def get_data_table_by_id(db: Session, table_id: int, user_id: int):
    return db.query(models.DataTable).filter(
        and_(
            models.DataTable.id == table_id,
            models.DataTable.created_by == user_id
        )
    ).first()

# Data Record CRUD
def create_data_record(db: Session, record: schemas.DataRecordCreate, data_table_id: int, user_id: int):
    db_record = models.DataRecord(
        data=record.data,
        data_table_id=data_table_id,
        created_by=user_id
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_records_by_data_table(db: Session, data_table_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.DataRecord).filter(
        models.DataRecord.data_table_id == data_table_id
    ).offset(skip).limit(limit).all()

def update_data_record(db: Session, record_id: int, data: dict, user_id: int):
    db_record = db.query(models.DataRecord).filter(
        and_(
            models.DataRecord.id == record_id,
            models.DataRecord.created_by == user_id
        )
    ).first()
    if db_record:
        db_record.data = data
        db.commit()
        db.refresh(db_record)
    return db_record

def delete_data_record(db: Session, record_id: int, user_id: int):
    db_record = db.query(models.DataRecord).filter(
        and_(
            models.DataRecord.id == record_id,
            models.DataRecord.created_by == user_id
        )
    ).first()
    if db_record:
        db.delete(db_record)
        db.commit()
    return db_record