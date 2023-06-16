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
import requests
import pandas as pd
import io
import sys
from markupsafe import Markup


router = APIRouter(
    prefix = '/finances',
    tags = ['finances']
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

def update():
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTr1wAMCjOz5vJVIyyDMzzWoHpA6BYAsxOu7tCWF2m_LyfP4k3YYlL26MeGhk8CJW3J_PJlqEaArb32/pub?gid=1351958327&single=true&output=csv'
    response = requests.get(url)
    df = pd.read_csv(io.StringIO(response.text))
    return df

@router.post("/", response_class=HTMLResponse)
async def start_finance_post(request: Request, name: str = Form(...)):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    return await display_person_analytics(request, name)

@router.get("/all", response_class=HTMLResponse)
async def display_all(request:Request):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    html_table = update().to_html(index=False)
    return templates.TemplateResponse(
        "finances.html",
        {"request": request, "html_table": html_table}
    )

@router.get("/group", response_class=HTMLResponse)
async def display_group(request:Request):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    total_paid_by_group = update().groupby('Type')['Cost'].sum()
    sorted_groups = total_paid_by_group.sort_values(ascending=False)
    top_3_paid_groups = sorted_groups.head(5)
    bottom_3_paid_groups = sorted_groups.tail(5)
    topTable = top_3_paid_groups.to_frame().reset_index().to_html(index=False)
    bottomTable = bottom_3_paid_groups.to_frame().reset_index().to_html(index=False)
    return templates.TemplateResponse(
        "finances.html",
        {"request": request, "topTable": topTable, "bottomTable":bottomTable}
    )

@router.get("/{name}", response_class=HTMLResponse)
async def display_person_analytics(request: Request):
    return templates.TemplateResponse("finances.html", {"request": request})

@router.post("/{name}", response_class=HTMLResponse)
async def display_person_analytics(request: Request, name: str):
    user = await get_curr_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    total_spent = 0
    owed = display_owed(name)
    largest_purchase = 0
    smallest_purchase = 0
    most_spent_type = 0
    least_spent_type = 0
    person_data = update()[update()['Name'] == name]
    if person_data.empty:
        return templates.TemplateResponse(
            "finances.html",
            {"request": request, "error_message": "Person not found"}
        )
    else:
        total_spent = person_data['Cost'].sum()
        largest_purchase = person_data['Cost'].max()
        smallest_purchase = person_data['Cost'].min()
        most_spent_type = person_data['Type'].value_counts().idxmax()
        least_spent_type = person_data['Type'].value_counts().idxmin()
    balance = total_spent-owed
    return templates.TemplateResponse(
        "finances.html",
        {"request": request, 
         "person_name": name, 
         "p_total_spent": total_spent,
         "p_owed": owed,
         "p_balance":balance,
         "p_largest_purchase": largest_purchase,
         "p_smallest_purchase": smallest_purchase,
         "p_most_spent_type": most_spent_type,
         "p_least_spent_type": least_spent_type}
    )


def display_owed(name:str):
    df = update()
    individuals = {}
    unique_names = df['Name'].unique()
    for name1 in unique_names:
        individuals[name1] = 0

    cost_by_category = df.groupby('Type')['Cost'].sum()
    for category, cost in cost_by_category.items():
        if category == 'Groceries-Meat':
            for name in individuals:    
                if(name=='Zarkar'):
                    continue
                else:
                    individuals[name] += cost / 3
        elif category == 'Groceries-Other':
            for name in individuals:
                if(name=='Zarkar'):
                    individuals[name] += cost*0.31
                else:
                    individuals[name] += cost*0.23
        else:
            for name in individuals:
                individuals[name] += cost / 4
    return individuals[name]