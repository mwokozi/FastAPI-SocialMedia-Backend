from fastapi import FastAPI,Depends,status, HTTPException, Request, Header
from fastapi.responses import JSONResponse
#security
from fastapi.security  import OAuth2PasswordBearer ,OAuth2PasswordRequestForm
import jwt 
from jwt.exceptions import InvalidTokenError
from pydantic_settings import BaseSettings, SettingsConfigDict 
from pydantic import BaseModel,SecretStr
#DB
from sqlalchemy.ext.asyncio import async_sessionmaker 
from db import async_engine, engine 
from sqlmodel import Session,select,SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import AsyncGenerator,Annotated 

from table_models import ( User, UserIn , UserRead, Comment, CommentIn, CommentRead, Post, PostIn, PostRead, Friend, FriendRead) 
from contextlib import asynccontextmanager 

from pwdlib import PasswordHash
from fastapi.concurrency import run_in_threadpool 
from datetime import datetime, timedelta, timezone


import uuid
import uvicorn

from logging_conf import setup_logging,request_id_ctx, user_id_ctx
import logging

setup_logging( level="INFO" ) 
logger = logging.getLogger( __name__ ) 

#############################################
# OAuth2 Config 
#############################################
oauth2_scheme=OAuth2PasswordBearer ( tokenUrl= "login" )  #extracts "token" string from JSON header :  { "WWW-Authorization" : f"Bearer{token}" }  

class APISettings ( BaseSettings): 
	host:str
	port : int
	secret_key : SecretStr 
	algorithm : str 
	minutes_to_expiry : int 

	model_config = SettingsConfigDict ( env_file = ".api_env" ) 


settings = APISettings() 

class Token(BaseModel) : 
	access_token : str 
	token_type : str

#################################################
# Lifespan 
#################################################
@asynccontextmanager
async def _lifespan ( app : FastAPI ) :
	#SQLModel.metadata.drop_all(engine)  
	SQLModel.metadata.create_all(engine) 
	app.state.sessionmaker = async_sessionmaker ( async_engine, expire_on_commit = False ) 
	yield 
	await async_engine.dispose() 

async def get_session ( request :Request ) -> AsyncGenerator [ AsyncSession, None ]  : 
	async with request.app.state.sessionmaker() as session : 
		yield session 

SessionDep = Annotated [ AsyncSession, Depends( get_session ) ]  

###############################################################################################
# Helper functions 
###############################################################################################
password_hash = PasswordHash.recommended () # employs Argon2 hashing algo


def create_token (username : str , duration_minutes  = settings.minutes_to_expiry  )-> Token : 
	exp = datetime.now( timezone.utc ) + timedelta (minutes= duration_minutes )   
	_token = jwt.encode ( { "sub" : username , "exp" : exp }, settings.secret_key.get_secret_value(), algorithm= settings.algorithm )  
	token= Token ( access_token = _token, token_type = "bearer" ) 
	return token

async def create_user ( session : AsyncSession ,username : str , password : str ) -> User :
	logger.info(  f"create_user() : Creating user {username}" )
	hashed_password	= await run_in_threadpool( password_hash.hash , password )
	new_user  = User.model_validate ( { "user_name": username, "hashed_password" : hashed_password }) 
	#breakpoint() 
	stmt = pg_insert ( User ).values (  user_name =  username, hashed_password = hashed_password).on_conflict_do_nothing().returning ( User ) 
	result = await session.execute ( stmt ) 
	await session.commit()
	user = result.scalar_one_or_none() 
	if user is None  : 
		raise HTTPException ( status_code=401 , detail = "username alreay exists")
	return user    


async def get_user ( session : AsyncSession , username : str ) -> Optional[UserRead, None]  : 
	logger.info(  f"get_user(): Fetching user {username}" ) 
	stmt = select ( User ).where ( User.user_name == username )
	result = await session.execute ( stmt ) 
	user = result.scalar_one_or_none()
	if user is None:
		HTTPException ( status_code=status.HTTP_401_UNAUTHORIZED, detail=f"User {username} does not exists" ) 
	if user is not  None  and user.disabled : 
		raise HTTPException ( status_code=403, detail="Inactive user" )# need different http code 
	return user
		

async def authenticate_user  (session : AsyncSession ,username : str, password: str ) -> UserRead : 
	logger.info(  f"authenticate_user() : Authenticating user {username}") 
	user = await get_user( session , username  ) 
	pwd_match = await run_in_threadpool ( password_hash.verify, password, user.hashed_password ) 
	if   ( user is None or not pwd_match ) :  
		#breakpoint() 
		raise HTTPException ( status_code=status.HTTP_401_UNAUTHORIZED , detail  = "username or password incorrect" ) 
	return { "user_name" : user.user_name, "created_at" : user.created_at } 

async def get_current_user ( session : SessionDep  , token :  Annotated [ str,  Depends ( oauth2_scheme ) ]      ) -> User: 
	logger.info(  f"get_current_user() : Fetching current user" ) 
	try:
		token_payload = jwt.decode( token, settings.secret_key.get_secret_value(), algorithms=[settings.algorithm ] ) 
	except InvalidTokenError: 
		raise HTTPException ( status_code = status.HTTP_401_UNAUTHORIZED, detail= "bad token: expired or wrong signature" , headers= { "WWW-Authenticate" : "Bearer" } )

	user = await get_user ( session ,token_payload.get( "sub" ) ) 
	user_id_ctx.set(user.user_id ) 
	logger.info(  f"get_current_user() : Successfully fetched current user" )
	return user #{ "user_name" : user.user_name	, "created_at" : user.created_at } 
 
#######################################
#Bind x-request-id from each request header to contextvar so its accessbile by logger 
#######################################
class RequestIdMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        rid = headers.get(b"x-request-id", b"").decode() or uuid.uuid4().hex[:12]
        token = request_id_ctx.set(rid)

        async def send_wrapper(message):                        # replaces the real send
            if message["type"] == "http.response.start":        # only touch the first message
                message.setdefault("headers", [])               # make sure the list exists
                message["headers"].append((b"x-request-id", rid.encode()))  # add our header
            await send(message)                                 # forward to the real send

        try:
            await self.app(scope, receive, send_wrapper)        # app uses the wrapper, not the real send
        finally:
            request_id_ctx.reset(token)

app=FastAPI(  lifespan=_lifespan ) #instantiate fastapi object

app.add_middleware(RequestIdMiddleware)




#########################################
#Define endpoint
#########################################

@app.put("/register/"  ) 
async def register ( session : SessionDep , form : Annotated [  OAuth2PasswordRequestForm, Depends() ]       ) :
	new_user = await create_user ( session ,form.username, form.password )
	return new_user

@app.post( "/login/"  )
async def login ( session: SessionDep, form : Annotated [ OAuth2PasswordRequestForm , Depends() ]   ) :
	authed_user = await authenticate_user( session ,form.username, form.password  ) 
	token = create_token ( authed_user.get ( "user_name" )  ) 
	return token


@app.put ("/befriend/{friend}" ) 
async def add_friend ( session : SessionDep , friend:str, token : Annotated[str, Depends(oauth2_scheme ) ]     ):
	user = await get_current_user ( session, token  ) 
	friend = await get_user( session ,friend ) 
	#stmt = select (User).where ( User.user_name.in_((user.user_name, friend ) )   ) 
	#results = await session.execute( stmt ) 
	#user, friend  = results.scalars()
	#breakpoint()	
	friend_submission = Friend ( user_id = user.user_id, friend_id = friend.user_id ) 
	session.add( friend_submission )
	await session.commit()
	await session.refresh( friend_submission)  
	return JSONResponse ( 

		content =  { "user_name" : user.user_name, "friend_name" : friend.user_name, "since" : datetime.strftime(friend_submission.since, "%Y%m%d %H:%M:%S")   },
		headers = { "WWW-Authenticate" : "Bearer"   }
	)

@app.get("/myfriends", response_model= list[FriendRead]  ) 
async def get_friends ( session : SessionDep, user : Annotated[User, Depends(get_current_user) ]       )  :
	
	sub_query = ( select( User.user_id ).where(User.user_name ==  user.user_name  ) )  
	stmt = select ( Friend.since,User.user_name ).join ( Friend,  User.user_id == Friend.friend_id ).where( Friend.user_id.in_(sub_query) )  
	result = await session.execute( stmt ) 
	friends_extracted = result.all() 
	friends = [ {"friend_name" : friend[1] , "since" : datetime.strftime( friend[0 ] ,"%Y%m%d %H:%M:%S")  } for friend in friends_extracted ]
	return friends 

if __name__ == "__main__" : 
	print(logging.getLogger().handlers, logging.getLogger().level)
	uvicorn.run (app, host = settings.host, port=settings.port ) 










 




	
