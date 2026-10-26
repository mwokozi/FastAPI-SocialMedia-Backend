from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from table_models import User,UserIn,UserRead
from typing import Annotated

from db import async_engine, engine 


oauth2_scheme = OAuth2PasswordBearer ( tokenUrl="token" ) 


router=APIRouter()


@router.post("token/" ) 
async def login ( form : Annotated[ OAuth2PasswordRequestForm, Depends()]  ) :
	pass
