from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME
)

engine = create_engine(url)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_connection():
    session = Session()
    try:
        result = session.execute(text("SELECT 1"))
        print("✓ Conexión a PostgreSQL exitosa")
        return True
    except Exception as e:
        print(f"✗ Error de conexión: {e}")
        return False
    finally:
        session.close()

def create_tables():
    from src.Models.models import Base
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas")