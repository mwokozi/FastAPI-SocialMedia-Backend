from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field

from sqlalchemy import URL

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import create_engine


##########################################
# Load DB Settings from env file 
##########################################

class DBSettings ( BaseSettings ): 
	user: str 
	password : SecretStr
	host : str 
	port : int 
	name : str 
	max_maxoverflow : int 
	min_maxoverflow : int 
	min_poolsize : int 
	max_poolsize : int 
	model_config = SettingsConfigDict ( env_file= ".db_env", env_prefix = "PG_DB_" ) 
	

db_settings = DBSettings() 

##########################################
#Build DB Connection URL 
##########################################

ASYNC_DB_URL= URL.create ( "postgresql+asyncpg", 
			username=db_settings.user,
			password = db_settings.password.get_secret_value(),
			host = db_settings.host,
			port = db_settings.port,
			database =db_settings.name 
			) 

SYNC_DB_URL= URL.create ( "postgresql", 
			username=db_settings.user,
			password = db_settings.password.get_secret_value(),
			host = db_settings.host,
			port = db_settings.port,
			database =db_settings.name 
			) 

#print ( f"{ASYNC_DB_URL=}\n {SYNC_DB_URL=}" )   		

#######################################################
# Create DB Engine
#######################################################

async_engine = create_async_engine ( ASYNC_DB_URL,
				    	echo= True,
					pool_pre_ping = True,
					pool_size  = db_settings.min_poolsize,
					max_overflow= db_settings.min_maxoverflow 

				)

engine = create_engine ( SYNC_DB_URL, echo= True ) 



	
