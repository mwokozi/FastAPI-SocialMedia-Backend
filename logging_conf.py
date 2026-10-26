import logging                                   # base logging module (for Filter class)
import logging.config                            # provides dictConfig
import socket                                    # to get the container's hostname
from contextvars import ContextVar               # async-safe per-request storage
from pathlib import Path                         # path handling for the log dir
from dotenv import  load_dotenv
import os 
import sys
import uuid
load_dotenv (".logging_env" ) 

PATH=os.getenv("LOG_DIR_PATH" ) 
LEVEL = os.getenv ( "LEVEL" )

LOG_DIR = Path(PATH)                      # folder inside the container for log files

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")  # holds current request's ID; "-" outside requests
user_id_ctx : ContextVar[uuid.UUID] = ContextVar("user_id", default="-" ) 

class RequestIdFilter(logging.Filter):           # custom filter that injects the request ID
    def filter(self, record):                    # called for every log record
        record.request_id = request_id_ctx.get() # attach the ID so the format string can use it
        return True                              # True = keep the record, don't drop it

class UserIDFilter( logging.Filter ): 
	def filter (self, record ):
		record.user_id=user_id_ctx 








def setup_logging(level: str = LEVEL ) -> None:  # call once at app startup
    LOG_DIR.mkdir(parents=True, exist_ok=True)   # create the log folder if it's missing
    log_file = LOG_DIR / f"myapp-{socket.gethostname()}.log"  # unique filename per container

    logging.config.dictConfig({                  # apply the whole config from a dict
        "version": 1,                            # required schema version
        "disable_existing_loggers": False,       # don't silence loggers created before this runs (uvicorn's)
        "formatters": {                          # how each log line looks
            "default": {                         # name referenced by handlers below
                "format": "%(asctime)s %(levelname)s [%(request_id)s] [%(user_id)s] %(name)s: %(message)s"  # time, level, request ID, logger, text
            },
        },
        "filters": {                             # filters attached to handlers
            "request_id": {"()": "logging_conf.RequestIdFilter"},  # "()" = build this class by import path
	    "user_id" : { "()" : "logging_conf.UserIDFilter" } 	
        },
        "handlers": {                            # where logs are sent
            "console": {                         # handler name: stdout/stderr
                "class": "logging.StreamHandler",  # writes to the console
                "stream" : "ext://sys.stdout", #send logs to stdout instead of default, stderr
		"formatter": "default",          # use the format defined above
                "filters": ["request_id", "user_id"],       # add request_id and user_id to each record
            },
            "file": {                            # handler name: log file
                "class": "logging.handlers.TimedRotatingFileHandler",  # rotates files on a schedule
                "filename": str(log_file),       # current log file path
                "when": "midnight",              # rotate at midnight
                "backupCount": 30,               # keep 30 old files, delete older
                "encoding": "utf-8",             # file text encoding
                "utc": True,                     # midnight is UTC, not local time
                "formatter": "default",          # same format as console
                "filters": ["request_id","user_id" ],       # add request_id and user_id to each record
            },
        },
        "root": {                                # default settings for all loggers
            "level": level,                      # minimum level to record (e.g. INFO)
            "handlers": ["console", "file"],     # send everything to both outputs
        },
        "loggers": {                             # per-logger overrides
            "uvicorn": {                         # uvicorn's main logger
                "level": "INFO",                 # record INFO and above
                "handlers": ["console", "file"], # send to both outputs
                "propagate": True,              # don't also pass to root (avoids duplicate lines)
            },
            "uvicorn.error": {                   # uvicorn startup/errors
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": True,
            },
            "uvicorn.access": {"level": "INFO"},      # silence uvicorn's access log (your middleware replaces it)
            "sqlalchemy.engine": {"level": "DEBUG"},   # hide SQL statements (set INFO to see them)
        },
    })                                           # end of dictConfig call
