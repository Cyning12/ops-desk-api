"""Global FastAPI dependencies."""

from fastapi import Depends

from app.db.session import get_db

DbDep = Depends(get_db)
