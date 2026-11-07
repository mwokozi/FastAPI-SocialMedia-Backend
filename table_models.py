from sqlmodel import SQLModel, Field
from sqlalchemy import Column, text, UUID, ForeignKey
from datetime import datetime ,timezone, UTC 
from pydantic import BaseModel, SecretStr
from sqlalchemy.dialects.postgresql import JSONB
import uuid
from typing import Literal
from enum import Enum
max_date_utc = datetime.combine ( datetime.max.date() , datetime.max.time(), UTC ) 
min_date_utc = datetime.combine ( datetime.min.date() , datetime.min.time(), UTC ) 

#######################
## Enum
########################
class StatusEnum ( Enum ) : 
	pending = "pending"
	accepted = "accepted"
	declined = "declined"
	terminated = "terminated"




#########################################
# Base Models
########################################
class BaseUser ( SQLModel ) : 
	user_name : str = Field (unique= True, index = True ) 
	hashed_password : str
	created_at : datetime = Field( default_factory = lambda: datetime.now( timezone.utc ) )
	disabled : bool = False 
	disable_at : datetime = Field ( default = min_date_utc ) 
	valid_until : datetime = Field ( default = max_date_utc ) 
class BaseRole ( SQLModel ) :
	role_name : str = Field ( index = True ) 
	created_at : datetime = Field( default_factory = lambda : datetime.now ( timezone.utc ) ) 
	valid_until : datetime = Field ( default = max_date_utc ) 	
class BasePermission (SQLModel ): 
	permission_name: str = Field ( unique = True, index = True ) 
	created_at : datetime = Field( default_factory = lambda : datetime.now ( timezone.utc ) ) 
	valid_until : datetime = Field ( default = max_date_utc ) 	
class BasePost ( SQLModel ) : 
	text : str = Field ( max_length = 144 , min_length = 3 ) 
	created_at : datetime = Field( default_factory = lambda: datetime.now( timezone.utc ) )	
	deleted : bool = False
	like_count : int = 0 
class BaseComment ( SQLModel ) : 
	text : str = Field ( max_length = 144 , min_length = 3 ) 
	created_at : datetime = Field( default_factory = lambda: datetime.now( timezone.utc ) )	
	deleted : bool = Field( default= False ) 
	like_count: int  = 0 
class BaseFriend ( SQLModel ): 
	since : datetime = Field( default_factory = lambda: datetime.now( timezone.utc ))  
class BasePostLikes (SQLModel ) : 
	liked_at : datetime  | None  = Field ( default_factory = lambda : datetime.now( timezone.utc ))
	liked : bool  = True 
class BaseCommentLikes ( SQLModel ):
	liked_at : datetime= Field( default_factory = lambda : datetime.now( timezone.utc ) )  
	liked : bool = True 	
class BaseAccount( SQLModel ): 
	created_at : datetime = Field ( default_factory = datetime.now(timezone.utc ) ) 
	tier : str = Field ( default = "basic" ) 
	last_active : datetime = min_date_utc
	last_viewed_feed : datetime = min_date_utc
	settings : dict = Field ( default_factory=dict, sa_column = Column( JSONB , nullable = False ) )  
class BaseFriendRequest( SQLModel ):  
	created_at : datetime = Field ( default_factory = lambda : datetime.now( timezone.utc )) 
	status : StatusEnum  = Field ( default = StatusEnum.pending ) 
	terminated_at : datetime = Field ( default = max_date_utc ) 
	deleted : bool = False 
########################################
# Table Models
########################################
class Permission ( BasePermission, table = True ): 
	permission_id : uuid.UUID | None = Field ( default =None , primary_key= True  ) 
class Role (BaseRole, table = True ): 
	role_id : uuid.UUID | None = Field ( default = None, primary_key = True ) 
	permission_id : uuid.UUID  = Field( foreign_key = "permission.permission_id" ) 
class User ( BaseUser, table = True ) : 
	user_id : uuid.UUID  | None = Field ( default = None , sa_column = Column( UUID( as_uuid = True ) , primary_key = True, server_default=text ( "gen_random_uuid()" )   )  ) 
	role_id : uuid.UUID  = Field ( foreign_key ="role.role_id") 
class Account ( BaseAccount, table = True ) :
	account_id  : uuid.UUID| None  = Field ( default=None, sa_column= Column ( UUID(as_uuid = True ), primary_key=True, server_default= text ( "gen_random_uuid()") ) ) 
	user_id : uuid.UUID = Field ( foreign_key= "user.user_id" ) 
class Post ( BasePost, table = True ): 
	post_id : uuid.UUID  | None = Field ( default = None , sa_column = Column( UUID( as_uuid = True ) , primary_key = True, server_default=text ( "gen_random_uuid()" )   )  )  
	author_id : uuid.UUID = Field ( foreign_key= "user.user_id")
class Comment ( BaseComment, table= True  ) : 
	comment_id : uuid.UUID  | None = Field ( default = None , sa_column = Column( UUID( as_uuid = True ) , primary_key = True, server_default=text ( "gen_random_uuid()" )   )  )  
	author_id :uuid.UUID  = Field ( foreign_key ="user.user_id" ) 
	parent_id : uuid.UUID  | None = None 
class Friend ( BaseFriend, table= True) : 
	#relation_id : uuid.UUID  | None = Field ( default = None , sa_column = Column( UUID( as_uuid = True ) , primary_key = True, server_default=text ( "gen_random_uuid()" )   )  )  
	user_id : uuid.UUID = Field ( primary_key= True ,foreign_key= "user.user_id" ) 
	friend_id : uuid.UUID = Field ( primary_key = True ,foreign_key = "user.user_id" ) 
class PostLikes ( BasePostLikes, table = True ) : 
	post_id :  uuid.UUID  = Field ( primary_key= True  ,foreign_key="post.post_id" )
	liker_id :  uuid.UUID  = Field ( primary_key = True , foreign_key= "user.user_id"  )  		 	
class CommentLikes ( BaseCommentLikes, table = True ) : 
	comment_id :  uuid.UUID  = Field ( primary_key= True , foreign_key="post.post_id" )
	liker_id :  uuid.UUID  = Field ( primary_key= True  , foreign_key= "user.user_id"  )  		 	

class FriendRequest( BaseFriendRequest , table = True ) : 
	request_id: uuid.UUID | None = Field ( default=None, sa_column= Column ( UUID(as_uuid = True) , primary_key= True , server_default = text( "gen_random_uuid()"))  ) 
	requester_id : uuid.UUID = Field ( foreign_key= "user.user_id" ) 
	requestee_id : uuid.UUID = Field ( foreign_key = "user.user_id" ) 
	
############################################
# In Models
############################################
class UserIn ( BaseModel ): 
	user_name : str  
	password : SecretStr 	
class PostIn ( BaseModel ): 
	author_name : str
	text : str
class CommentIn ( BaseModel ) : 
	author_name : str 
	text : str
class FriendRequestIn ( BaseModel ) : 
	requester_id : str 
	requestee_id : str 
############################################
# Read Models
############################################
class UserRead ( BaseModel ): 
	user_name : str 
	created : datetime
class PostRead ( BaseModel ) : 
	author_name : str
	text : str 
	created : datetime 
class CommentRead( BaseModel ) : 
	author_name : str 
	text : str
	created : datetime
class FriendRead ( BaseModel ):
	friend_name : str 
	since  : str 
class FriendRequestRead ( BaseModel ) : 
	requester_name : str 
	requestee_name : str 
	created : datetime 





