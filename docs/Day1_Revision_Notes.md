# Hotel Management System: Day 1 Revision Notes

**Tech stack:** Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic
**Aaj ka maqsad:** Project setup karna aur FastAPI ko PostgreSQL se jorna
**Status:** Mukammal. Phase 1 aur Phase 2 done.

---

## 1. Aaj kya kya hua (Summary)

| # | Kaam | Natija |
|---|---|---|
| 1 | Project folder banaya | `hotel-management-system/` |
| 2 | Virtual environment banaya aur activate kiya | `(venv)` prompt mein nazar aaya |
| 3 | Libraries install kin | `requirements.txt` ban gayi |
| 4 | Git shuru kiya aur `.gitignore` banayi | Pehla commit hua |
| 5 | Folder structure banaya | `app/core`, `db`, `models`, ... |
| 6 | pgAdmin mein `hotel_db` database banaya | Database tayyar |
| 7 | `.env` aur `config.py` likhe | Settings sahi parhi gayin |
| 8 | `session.py` likhi | Python se PostgreSQL 18.6 connect hua |
| 9 | `main.py` likhi, server chalaya | `/health`, `/health/db`, `/docs` kaam kar rahe hain |

---

## 2. Concepts (Samajhne ki baatein)

### Virtual Environment (venv)
Har project ko apni alag libraries chahiye hoti hain. `venv` ek alag dabba hai sirf is project ke liye, taake libraries aapas mein na takrayein.
- Activate karna: `venv\Scripts\activate`
- Jab `(venv)` prompt ke shuru mein nazar aaye to matlab activate hai.
- Hamesha kaam shuru karne se pehle activate karo.

### Libraries aur unka kaam

| Library | Kaam |
|---|---|
| FastAPI | API banane ke liye (backend ka dil) |
| Uvicorn | Server jo FastAPI ko chalata hai |
| SQLAlchemy | Python code se database se baat karna |
| psycopg2-binary | Python aur PostgreSQL ke beech pul (bridge) |
| Alembic | Database tables ke changes ka record (migrations) |
| pydantic-settings | `.env` file se settings parhna |
| python-jose | Login token (JWT) banana |
| passlib + bcrypt | Password hash karna (kabhi plain password save nahi karte) |
| pytest, httpx | Testing |

### requirements.txt
Installed libraries ki list. Naye computer par: `pip install -r requirements.txt`

### Git aur .gitignore
- Git code ka "time machine" hai. Har commit ek tasveer (save point) hai.
- `.gitignore` Git ko batata hai kin files ko ignore karna hai:

```
venv/             # bohat bara, requirements.txt se dobara ban jata hai
.env              # password aur secret key, kabhi online nahi jani chahiye
__pycache__/      # Python ki temporary files
*.pyc             # (* ka matlab "kuch bhi")
.pytest_cache/    # pytest ki temporary files
```

### .env aur config.py
- `.env` mein raaz ki cheezein (password, secret key).
- `config.py` mein Python code jo `.env` parhta hai.
- Baaqi project mein `settings.DATABASE_URL` likh kar value li jati hai, password code mein kahin nahi likhte.

### Connection String (database ka pata)
```
postgresql+psycopg2://USERNAME:PASSWORD@HOST:PORT/DATABASE
postgresql+psycopg2://postgres:PASSWORD@localhost:5432/hotel_db
```
Agar password mein khaas character ho to URL-encode karo: `@` ban jata hai `%40`.

### Engine, Session, Base (Restaurant ki misaal)

| Cheez | Restaurant mein | Matlab |
|---|---|---|
| Engine | Restaurant ka darwaza aur rasta | Database tak connection ka zariya |
| Session | Ek customer ki table | Ek kaam ka silsila (query, save) |
| Base | Menu ka template | Isse tables (models) define honge |

### get_db() aur yield
```python
def get_db():
    db = SessionLocal()
    try:
        yield db        # session de do, request ka kaam hone do
    finally:
        db.close()      # kaam ho ya error, hamesha band karo
```
`close()` na karein to connections khatam ho jate hain aur app atak jati hai.

### FastAPI aur Decorator
```python
@app.get("/health")      # jab koi /health par aaye (GET request)
def health():            # to yeh function chalao
    return {"status": "ok"}
```
FastAPI return ki hui dictionary ko khud JSON bana deta hai.

### /docs (Swagger UI)
FastAPI khud ek testing page bana deta hai: `http://localhost:8000/docs`
- Browser ki address bar sirf GET bhej sakti hai. POST, PUT, DELETE ke liye `/docs` use hota hai.
- Frontend ke baghair API test ho jati hai.
- Khud-ba-khud documentation milti hai.
- Aage ja kar yahin se login (Authorize) bhi hoga.

**Use karne ka tareeqa:** endpoint par click, phir Try it out, phir Execute, phir neeche Response dekho.

**Response codes:**

| Code | Matlab |
|---|---|
| 200 | Kamyab |
| 404 | Nahi mila |
| 422 | Aap ka bheja hua data ghalat tha |
| 500 | Server mein khud galti hai |

`/redoc` par wohi documentation sirf parhne ke liye milti hai.

---

## 3. Commands (Windows)

### Setup
```
mkdir hotel-management-system
cd hotel-management-system
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install fastapi "uvicorn[standard]" sqlalchemy psycopg2-binary alembic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" python-multipart pytest httpx
pip install "bcrypt==4.0.1"
pip freeze > requirements.txt
git init
```

### Khali file banana
```
type nul > filename.py          (CMD)
New-Item filename.py            (PowerShell)
```

### Secret key banana
```
python -c "import secrets; print(secrets.token_hex(32))"
```

### Server chalana
```
uvicorn app.main:app --reload
```
- `app.main:app` ka matlab: `app` folder, `main.py` file, `app` variable.
- `--reload` code save karte hi server dobara chalata hai (sirf development mein).
- Rokne ke liye `Ctrl+C`.

### Database connection test
```
python -c "from sqlalchemy import text; from app.db.session import engine; c = engine.connect(); print(c.execute(text('SELECT version()')).scalar()); c.close()"
```

### Git ki aadat
```
git status                          # kya badla?
git add .                           # tasveer ke liye files chuno
git commit -m "message"             # tasveer lo
git log --oneline                   # history dekho
git ls-files                        # Git kin files ko track kar raha hai
```
**Har commit se pehle `git status` mein check karo ke `.env` aur `venv/` nazar na aayein.**

---

## 4. Final Folder Structure (ab tak)

```
hotel-management-system/
├── app/
│   ├── main.py              # FastAPI app, health endpoints
│   ├── core/
│   │   ├── config.py        # .env se settings
│   │   └── security.py      # (khali, baad mein)
│   ├── db/
│   │   ├── session.py       # engine, SessionLocal, Base, get_db
│   │   └── base.py          # (khali, baad mein)
│   ├── models/              # (khali, Phase 3)
│   ├── schemas/             # (khali)
│   ├── crud/                # (khali)
│   ├── services/            # (khali)
│   ├── api/
│   │   ├── deps.py          # (khali)
│   │   └── v1/
│   │       ├── router.py    # (khali)
│   │       └── endpoints/   # (khali)
│   └── utils/
├── tests/
├── scripts/
├── .env                     # raaz, Git mein nahi
├── .env.example             # fake values, Git mein hai
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 5. Aaj ka Final Code

### .env
```
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/hotel_db
SECRET_KEY=yahan_lamba_random_text
ACCESS_TOKEN_EXPIRE_MINUTES=60
```
(Koi space ya inverted commas nahi. `YOUR_PASSWORD` ki jagah asli password, yahan notes mein asli password mat likhna.)

### app/core/config.py
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
```

### app/db/session.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
- `pool_pre_ping=True`: connection use karne se pehle check karta hai ke zinda hai.
- `autoflush=False`: changes database ko tab bhejo jab hum kahein.

### app/main.py
```python
from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import engine

app = FastAPI(title="Hotel Management System", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"database": "connected"}
```
- `/health`: app chal rahi hai.
- `/health/db`: app chal rahi hai aur database bhi jura hua hai.

---

## 6. Errors jo aaye aur unka hal (Bohat zaroori seekh)

### Error 1: `'source' is not recognized`
- **Wajah:** `source venv/bin/activate` Linux/Mac ka command hai.
- **Hal:** Windows par `venv\Scripts\activate`.

### Error 2: pip line ke akhir mein `\` se masla
- **Wajah:** `\` Linux mein line jorne ke liye hota hai, Windows CMD mein nahi chalta.
- **Hal:** Poora `pip install ...` command **ek hi line** mein likho.

### Error 3: `psql is not recognized`
- **Wajah:** PostgreSQL install hai, lekin uska `bin` folder Windows ke PATH mein nahi.
- **Hal:** Database pgAdmin se banaya (Databases, right-click, Create, Database). `psql` ki zaroorat nahi.

### Error 4: `ImportError: cannot import name 'Declarative_Base'`
- **Wajah:** `session.py` mein purane andaz ki import line thi (`from sqlalchemy.ext.declarative import Declarative_Base, sessionmaker`). Naam bhi ghalat tha aur jagah bhi.
- **Hal:** Naye SQLAlchemy 2.x ka tareeqa: `from sqlalchemy.orm import sessionmaker, DeclarativeBase`.
- **Seekh:** Purane tutorials ka code naye version mein nahi chalta. Version check karo.

### Error Parhne ka tareeqa
1. **Aakhri line** parho: kya hua (`ImportError`, `ValidationError`, ...)
2. **`File "...", line N`** dekho: kaun si file, kaun si line
3. Us line ko dekho aur theek karo
4. Chat mein poora traceback nahi, aakhri 2-3 lines bhejo. **Password kabhi share mat karo.**

### Aam errors ki quick table

| Error | Matlab |
|---|---|
| `password authentication failed` | `.env` mein password ghalat |
| `database "hotel_db" does not exist` | Database ka naam ghalat ya bana nahi |
| `Connection refused` | PostgreSQL service band hai |
| `ValidationError ... Field required` | `.env` mein koi line missing ya file save nahi hui |
| `ModuleNotFoundError: app` | Project folder ke andar nahi ho |
| `ModuleNotFoundError: pydantic_settings` | `(venv)` active nahi hai |
| `Address already in use` | Server pehle se chal raha hai, purana band karo |

---

## 7. Revision Checklist

Kal shuru karne se pehle yeh sab ho sakta hai to tayyar ho:

- [ ] `venv\Scripts\activate` karke `(venv)` dekh sakta hoon
- [ ] `uvicorn app.main:app --reload` se server chala sakta hoon
- [ ] `/health`, `/health/db` aur `/docs` browser mein khol sakta hoon
- [ ] Bata sakta hoon `.env` aur `config.py` ka kya rishta hai
- [ ] Engine, Session aur Base ka farq samajhta hoon
- [ ] `get_db()` mein `yield` aur `finally` ka kaam samajhta hoon
- [ ] `git status`, `add`, `commit` kar sakta hoon
- [ ] Samajhta hoon ke `.env` Git mein kyun nahi jata

---

## 8. Kal ka plan: Phase 3 (Database Tables)

1. **Concepts:** table, row, column, primary key, foreign key (hotel ki misaal se)
2. **Models likhna** (ek ek karke): `users`, `guests`, `room_types`, `rooms`, `bookings`, `payments`
3. **Alembic setup:** database ke changes ko code se manage karna
4. **Pehli migration:** tables ko database mein banana
5. **pgAdmin mein check karna** ke tables ban gayi

### Kal shuru karne ka tareeqa
```
cd "C:\Users\EnterCuin Int\Desktop\Intership Tasks\hotel-management-system"
venv\Scripts\activate
git status
uvicorn app.main:app --reload
```
Pehle PostgreSQL service chal rahi ho (pgAdmin kholne par server connect ho jata hai to theek hai).

---

## 9. Yaad rakhne ke Golden Rules

1. Kaam shuru karne se pehle **venv activate** karo.
2. `.env` **kabhi** Git ya chat mein nahi.
3. Har mukammal hissay ke baad **commit** karo.
4. Error aaye to **aakhri line aur line number** parho.
5. Purane tutorials ka code **version check** kiye baghair copy mat karo.
6. Sirf copy paste mat karo, har line ka matlab samjho.