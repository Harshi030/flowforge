from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.modules.rbac.constants import PERMISSIONS
from app.modules.rbac.models import Permission

def seed_permissions(session: Session) -> None:
    for code, description in PERMISSIONS:
      existing_permission  = session.execute(
        select(Permission).where(Permission.code == code)
      ).scalar_one_or_none()
      
      if not existing_permission:
        insert_permission = Permission(
          code=code,
          description=description
        )
        session.add(insert_permission)
        
    session.commit()
    
def main() -> None:
  session = SessionLocal()
  
  try:
    seed_permissions(session)
  except Exception:
    session.rollback()
    raise
  finally:
    session.close()
    
if __name__ == "__main__":
  main()