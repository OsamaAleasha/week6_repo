from db import engine
from models import metadata, tasks
from sqlalchemy import insert, select, delete, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

metadata.create_all(engine)

