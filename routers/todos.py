from typing import Annotated
from fastapi import Depends, FastAPI, Form, HTTPException, Path, APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models import Todos, Users
from database import SessionLocal, engine
from starlette import status
from .auth import get_curr_user
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import models
from starlette.responses import RedirectResponse


router = APIRouter(
    prefix = '/todos',
    tags = ['todos']
)

models.Base.metadata.create_all(bind=engine)

templates =  Jinja2Templates(directory="templates")

#opens and closes a connection to the Sessions database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request:Request, db: Session=Depends(get_db)):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todos = db.query(Todos).filter(Todos.owner_id==user.get('id')).all()
    return templates.TemplateResponse("home.html",{"request":request, "todos": todos, "user":user})

@router.get("/add-todo", response_class=HTMLResponse)
async def add_new_todo(request:Request):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("add-todo.html", {"request":request, "user":user})

@router.post("/add-todo", response_class=HTMLResponse)
async def create_todo(request:Request, title:str = Form(...), description:str = Form(...), db: Session=Depends(get_db)):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = Todos()
    todo_model.title = title
    todo_model.description = description
    todo_model.complete = False
    todo_model.owner_id = user.get('id')
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request:Request, todo_id: int, db: Session=Depends(get_db)):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo = db.query(Todos).filter(Todos.id==todo_id).first()
    return templates.TemplateResponse("edit-todo.html", {"request":request, "todo": todo, "user":user})

@router.post("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def update_todo(request:Request, todo_id: int, title: str=Form(...), description:str=Form(...), db: Session=Depends(get_db)):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(Todos).filter(Todos.id==todo_id).first()
    todo_model.title = title
    todo_model.description = description
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/delete/{todo_id}")
async def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/complete/{todo_id}", response_class=HTMLResponse)
async def complete_todo(request:Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    todo = db.query(Todos).filter(Todos.id==todo_id).first()
    todo.complete = not todo.complete
    db.add(todo)
    db.commit()
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


