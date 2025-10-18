from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import shutil
from typing import List, Optional

import models
import schemas
import crud
from database import SessionLocal, engine, get_db
from auth import get_current_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash, get_current_user_web
from excel_parser import ExcelParser
from datetime import timedelta

# Создание таблиц
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Excel to Database Converter", version="1.0.0")

# Монтирование статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Создание директории для загрузок
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Создание начального пользователя
def create_initial_user():
    db = SessionLocal()
    try:
        user = crud.get_user_by_email(db, "admin@example.com")
        if not user:
            db_user = models.User(
                email="admin@example.com",
                hashed_password=get_password_hash("password"),
                full_name="Administrator"
            )
            db.add(db_user)
            db.commit()
            print("Создан начальный пользователь: admin@example.com / password")
        else:
            print("Начальный пользователь уже существует")
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
    finally:
        db.close()

create_initial_user()

# Роуты для веб-интерфейса
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_web(request, db)
    if not user:
        return RedirectResponse("/")
    
    user_templates = crud.get_templates_by_user(db, user.id)
    return templates.TemplateResponse("templates.html", {
        "request": request,
        "templates": user_templates,
        "user": user
    })

@app.get("/templates/create", response_class=HTMLResponse)
async def create_template_form(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_web(request, db)
    if not user:
        return RedirectResponse("/")
    
    return templates.TemplateResponse("create_template.html", {
        "request": request,
        "user": user
    })

@app.get("/templates/{template_id}/upload", response_class=HTMLResponse)
async def upload_form(request: Request, template_id: int, db: Session = Depends(get_db)):
    user = await get_current_user_web(request, db)
    if not user:
        return RedirectResponse("/")
    
    template = crud.get_template_by_id(db, template_id, user.id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "template": template,
        "user": user
    })

@app.get("/tables/{table_id}/view", response_class=HTMLResponse)
async def view_data(request: Request, table_id: int, db: Session = Depends(get_db)):
    user = await get_current_user_web(request, db)
    if not user:
        return RedirectResponse("/")
    
    data_table = db.query(models.DataTable).filter(
        models.DataTable.id == table_id,
        models.DataTable.created_by == user.id
    ).first()
    
    if not data_table:
        raise HTTPException(status_code=404, detail="Таблица не найдена")
    
    records = crud.get_records_by_data_table(db, table_id)
    
    return templates.TemplateResponse("data_view.html", {
        "request": request,
        "data_table": data_table,
        "records": records,
        "user": user
    })

# API роуты
@app.post("/api/login")
async def login(login_data: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверные учетные данные"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Устанавливаем cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1800,
        expires=1800,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}

@app.post("/api/register")
async def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    user = crud.create_user(db, user_data)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@app.post("/api/templates", response_model=schemas.TableTemplateResponse)
async def create_template(
    template: schemas.TableTemplateCreate,
    db: Session = Depends(get_db)
):
    # Упрощенная аутентификация для демо
    user = crud.get_user_by_email(db, "admin@example.com")
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    return crud.create_table_template(db, template, user.id)

@app.get("/api/templates", response_model=List[schemas.TableTemplateResponse])
async def get_templates(db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, "admin@example.com")
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    return crud.get_templates_by_user(db, user.id)

@app.get("/api/templates/{template_id}", response_model=schemas.TableTemplateResponse)
async def get_template(template_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, "admin@example.com")
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    template = crud.get_template_by_id(db, template_id, user.id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return template

@app.post("/api/templates/{template_id}/upload")
async def upload_excel(
    template_id: int,
    table_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, "admin@example.com")
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    # Проверка шаблона
    template = crud.get_template_by_id(db, template_id, user.id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    # Сохранение файла
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Парсинг Excel
    parser = ExcelParser()
    try:
        field_definitions = [schemas.FieldDefinition(**field) for field in template.fields]
        records, errors = parser.parse_excel(file_path, field_definitions)
        
        if errors and not records:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "processed_rows": 0,
                    "errors": errors,
                    "imported_records": 0
                }
            )
        
        # Создание таблицы данных
        data_table = crud.create_data_table(db, schemas.DataTableCreate(
            name=table_name,
            template_id=template_id
        ), user.id)
        
        # Сохранение записей
        imported_count = 0
        for record_data in records:
            record = schemas.DataRecordCreate(data=record_data)
            crud.create_data_record(db, record, data_table.id, user.id)
            imported_count += 1
        
        # Очистка файла
        os.remove(file_path)
        
        return {
            "success": True,
            "processed_rows": len(records) + len(errors),
            "errors": errors,
            "imported_records": imported_count,
            "data_table_id": data_table.id
        }
        
    except Exception as e:
        # Очистка файла в случае ошибки
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tables/{table_id}/records", response_model=List[schemas.DataRecordResponse])
async def get_table_records(
    table_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, "admin@example.com")
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    data_table = db.query(models.DataTable).filter(
        models.DataTable.id == table_id,
        models.DataTable.created_by == user.id
    ).first()
    
    if not data_table:
        raise HTTPException(status_code=404, detail="Таблица не найдена")
    
    return crud.get_records_by_data_table(db, table_id, skip, limit)

@app.put("/api/records/{record_id}")
async def update_record(
    record_id: int,
    record_data: schemas.DataRecordCreate,
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, "admin@example.com")
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    updated_record = crud.update_data_record(db, record_id, record_data.data, user.id)
    if not updated_record:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return updated_record

@app.delete("/api/records/{record_id}")
async def delete_record(record_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, "admin@example.com")
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    deleted = crud.delete_data_record(db, record_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return {"message": "Запись удалена"}

@app.get("/api/templates/{template_id}/tables")
async def get_template_tables(template_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, "admin@example.com")
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    template = crud.get_template_by_id(db, template_id, user.id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    return crud.get_data_tables_by_template(db, template_id, user.id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)