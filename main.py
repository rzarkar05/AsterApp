from fastapi import FastAPI
import models
from database import engine
from routers import auth, todos, users, finances
from starlette.staticfiles import StaticFiles

app = FastAPI()
#
models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

#Includes prompts recieved from router in auth.py file
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(users.router)
app.include_router(finances.router)