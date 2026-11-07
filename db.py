from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field

from sqlalchemy import URL

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import create_engine, Session, select
from table_models import Permission, Role
import uuid

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



def init_db () -> None:
    role_permissions = {
        "admin": (
            "Post.read",
            "Post.write",
            "Comment.read",
            "Comment.write",
            "Post.read_all",
            "Post.write_all",
            "Broadcast",
        ),
        "end_user": (
            "Post.read",
            "Post.write",
            "Comment.read",
            "Comment.write",
            "Account.public",
            "Account.private",
        ),
    }
    permissions_by_name: dict[str, Permission] = {}

    with Session(engine) as session:
        for permission_name in {
            permission_name
            for permissions in role_permissions.values()
            for permission_name in permissions
        }:
            permission = session.exec(
                select(Permission).where(
                    Permission.permission_name == permission_name
                )
            ).first()
            if permission is None:
                permission = Permission(
                    permission_id=uuid.uuid4(),
                    permission_name=permission_name,
                )
                session.add(permission)
            permissions_by_name[permission_name] = permission

        session.flush()

        existing_role_permissions = set(
            session.exec(select(Role.role_name, Role.permission_id)).all()
        )
        for role_name, permission_names in role_permissions.items():
            for permission_name in permission_names:
                permission = permissions_by_name[permission_name]
                role_permission = (role_name, permission.permission_id)
                if role_permission not in existing_role_permissions:
                    session.add(
                        Role(
                            role_id=uuid.uuid4(),
                            role_name=role_name,
                            permission_id=permission.permission_id,
                        )
                    )

        session.commit()

	
