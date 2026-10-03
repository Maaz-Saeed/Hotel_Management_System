# Hotel Management System: Day 3 Revision Notes

**Topic:** Phase 3 (Part 2): Alembic aur Migrations
**Aaj ka maqsad:** Models ko asli PostgreSQL tables mein badalna
**Status:** Mukammal. 6 tables `hotel_db` mein ban gayi.

---

## 1. Aaj kya kya hua (Summary)

| # | Kaam | Natija |
|---|---|---|
| 1 | Alembic kyun chahiye, samjha | Database ka "Git" |
| 2 | `alembic init alembic` chalaya | `alembic/` folder aur `alembic.ini` bane |
| 3 | `alembic/env.py` ko project se joda | Settings aur models connect hue |
| 4 | Do ghaltiyan pakri aur theek kin | `sarver_default`, `"%% "` |
| 5 | Pehli migration banayi | `b5714ebe8357_initial_tables.py` |
| 6 | `alembic upgrade head` chalaya | 6 tables database mein ban gayi |
| 7 | pgAdmin aur migration file mein verify kiya | Sab theek |

---

## 2. Alembic kya hai aur kyun?

Models sirf **Python code** hain. Database mein tables banane ke liye SQL `CREATE TABLE` haath se likhna mushkil hai, aur agar baad mein koi column add karna ho to:

> Table haath se badlo? Aur agar doosre developer ya server par bhi wohi tabdeeli karni ho?

**Alembic** database ki tabdeeliyon ka **Git** hai.

| Git | Alembic |
|---|---|
| Code ke changes ka record | Database tables ke changes ka record |
| `git commit` | `alembic revision` (migration file banao) |
| Purani halat par jana | `alembic downgrade` |
| Naye commits lagana | `alembic upgrade` |

- Har tabdeeli ek **migration file** hoti hai.
- `alembic upgrade head` saari tabdeeliyan database par laga deta hai.
- Kisi aur computer par wohi command chalao, wahan bhi bilkul wohi tables ban jayengi.
- `--autogenerate` ki wajah se Alembic models ko database se milakar migration **khud likh leta hai**.

---

## 3. Alembic ke Steps (Commands)

### Step 1: Alembic shuru karo
```
alembic init alembic
```
Isse yeh banta hai:

| Cheez | Kaam |
|---|---|
| `alembic/` folder | `env.py` (settings) aur `versions/` (migration files) |
| `alembic.ini` | Alembic ki configuration file |

### Step 2: `alembic/env.py` ko apne project se jodo

Alembic ko 2 cheezein nahi pata thin: database kahan hai, aur models kahan hain.

`config = context.config` wali line ke **neeche** add kiya:
```python
config = context.config
from app.core.config import settings
from app.db.session import Base
import app.models  # noqa: F401

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))
```

Aur `target_metadata = None` ko badla:
```python
target_metadata = Base.metadata
```

| Code | Matlab |
|---|---|
| `from app.core.config import settings` | `.env` se password parhne wali settings. Password `alembic.ini` mein nahi likhna parta |
| `from app.db.session import Base` | Woh `Base` jis se saare models bane hain |
| `import app.models` | Models ko load karta hai. **Iske baghair migration khali banti hai** |
| `# noqa: F401` | Editor ki "unused import" warning chup karata hai |
| `config.set_main_option(...)` | Alembic ko database ka pata batata hai |
| `.replace("%", "%%")` | Alembic `%` ko khaas nishan samajhta hai. Password mein `%40` ho to isse sahi parha jata hai |
| `target_metadata = Base.metadata` | Models ka naqsha. Alembic is ka database se muqabla karta hai |

### Step 3: Alembic ka connection test karo
```
alembic current
```
Baghair error ke wapas prompt aana chahiye (abhi koi migration nahi chali, is liye kuch print nahi hota).

### Step 4: Pehli migration banao
```
alembic revision --autogenerate -m "initial tables"
```

| Hissa | Matlab |
|---|---|
| `revision` | Nayi migration file banao |
| `--autogenerate` | Models ko database se milao, farq khud likho |
| `-m "initial tables"` | Migration ka naam (commit message ki tarah) |

Output mein 6 `Detected added table ...` lines aani chahiyen. Phir `alembic/versions/` mein nayi file banti hai.

### Step 5: Migration file parho (chalane se pehle)
Autogenerate hamesha 100% sahi nahi hota. File mein 2 functions hote hain:
- `upgrade()`: tables banao (`op.create_table(...)`)
- `downgrade()`: tabdeeli wapas karo (`op.drop_table(...)`)

Check karo:
1. 6 `op.create_table` hain
2. `room_types` pehle aur `bookings` baad mein hai (FK ko pehle wali table chahiye)
3. `paid_at` mein `server_default=sa.text('now()')` hai
4. `bookings` mein CheckConstraint hai

Aaj ka check:
```
findstr /n "now()" alembic\versions\b5714ebe8357_initial_tables.py
```
4 lines aayin (`guests`, `users`, `bookings` ke `created_at` aur `payments` ka `paid_at`), yani sab theek.

### Step 6: Tables banao
```
alembic upgrade head
```
`head` ka matlab "sab se nayi migration tak". Output:
```
Running upgrade  -> b5714ebe8357, initial tables
```

### Step 7: Verify karo
```
alembic current
```
`b5714ebe8357 (head)` aana chahiye. `(head)` ka matlab hai ke aap sab se nayi migration par ho.

pgAdmin mein: `hotel_db`, phir `Schemas`, phir `public`, phir `Tables`, right-click, **Refresh**. **7 tables** nazar aati hain:
`alembic_version`, `bookings`, `guests`, `payments`, `room_types`, `rooms`, `users`

Kisi table mein `Constraints` kholo to Primary Key, Foreign Keys aur Check constraint nazar aate hain. Yeh sab Python mein likha tha, Alembic ne SQL mein badal kar daal diya.

---

## 4. Aaj ke Sawal aur Jawab

### Sawal 1: `import app.models` na likhte to kya hota?
**Jawab:** Alembic `app.models` se models leta hai.

**Poori chain:**
```
import app.models
    ↓ (models/__init__.py chalti hai)
saare models import hote hain
    ↓ (har class Base se bani hai)
har class apni table ko Base.metadata mein register karti hai
    ↓
Alembic Base.metadata parhta hai aur database se muqabla karta hai
```
Models "app.models mein store" nahi hote, woh `Base.metadata` mein **register** hote hain. Agar import na hota to `Base.metadata` **khali** rehta aur migration khali banti (`upgrade()` mein sirf `pass`). Yeh beginners ki sab se aam ghalti hai.

### Sawal 2: `alembic_version` table kya hai?
**Jawab:** Is se Alembic ko pata chalta hai ke database kis migration par hai.

**Sudhaar:** Is mein har migration par nayi row add **nahi** hoti. Is mein hamesha **sirf ek row** hoti hai, aur har migration par us ki value **update** ho jati hai.

| Table | Column | Value (abhi) |
|---|---|---|
| `alembic_version` | `version_num` | `b5714ebe8357` |

Yeh kitab mein **bookmark** ki tarah hai: hamesha ek hi page par, aur har baar aage khisakta hai.

---

## 5. Errors jo aaye aur unka hal

### Error 1: `SAWarning: Can't validate argument 'sarver_default'`
- **Wajah:** `payment.py` mein `server_default` ki jagah `sarver_default` likha tha (spelling ki ghalti).
- **Asar:** Yeh sirf warning thi, error nahi, is liye test pass ho gaya tha. Lekin `paid_at` ka default waqt kabhi lagta hi nahi.
- **Hal:** Spelling theek ki. Dhoondne ke liye:
  ```
  findstr /n "sarver" app\models\*.py
  ```
  Kuch nahi aana chahiye.
- **Seekh:** Warnings ko nazar-andaz mat karo, woh bhi kuch batati hain.

### Error 2: `password authentication failed for user "postgres"` (sirf Alembic mein)
- **Wajah:** `env.py` mein ek **extra space**:
  ```python
  .replace("%", "%% ")     # ghalat, "%%" ke baad space hai
  .replace("%", "%%")      # sahi
  ```
- **Kaise kharab hua:** Password `ali%40123` ke `%` ko `%%` aur space ban gaya, to Alembic ne `% 40` parha, jo ghalat password hai.
- **Kyun app chal rahi thi:** `session.py` seedha `settings.DATABASE_URL` use karta hai, `replace` wali line se guzarta hi nahi.
- **Debug ka tareeqa:** Test A (`session.py` wala connection) chalaya. Wo pass hua to pata chala masla `.env` mein nahi, `env.py` mein hai.
- **Seekh:** Code paste karo to ek ek character milao, khaas kar `""` ke andar.

### Lambi error kaise parhein
Traceback 100+ lines ka ho sakta hai. Sirf yeh dekho:
1. **Shuru ki lines:** warnings (jaise `SAWarning`)
2. **Aakhri line:** asli wajah (`password authentication failed`)
3. Beech ki lines sirf "raasta" dikhati hain

Mujhe bhejte waqt: pehli 1-2 aur aakhri 3 lines kaafi hain. Password wali jagah chhupa do.

### Debugging ki tarteeb (jo aaj kaam aayi)
1. Error ki aakhri line parho
2. Pata karo kya chal raha hai aur kya nahi (app chal rahi thi, Alembic nahi)
3. Farq dhoondo (dono mein kya alag hai: `env.py` ki ek line)
4. Theek karo, dobara test karo

---

## 6. Naye Words (Glossary)

| Lafz | Matlab |
|---|---|
| Migration | Database ki ek tabdeeli ki file |
| Revision ID | Migration ki pehchan, jaise `b5714ebe8357` |
| `head` | Sab se nayi migration |
| `upgrade` | Migration lagao |
| `downgrade` | Migration wapas karo |
| `autogenerate` | Models se migration khud likhwao |
| Metadata | Models ka naqsha (kaun si tables, kaun se columns) |
| Constraint | Table par qanoon (PK, FK, Unique, Check) |

---

## 7. Git Commits (Aaj ke)

```
git add .
git commit -m "Initialize Alembic"
git add .
git commit -m "Add initial migration"
git log --oneline
```
`git status` mein `.env` nazar nahi aani chahiye. `LF will be replaced by CRLF` sirf ittela hai.

---

## 8. Final Folder Structure (ab tak)

```
hotel-management-system/
├── alembic/
│   ├── env.py                 # (humne badla)
│   ├── script.py.mako
│   └── versions/
│       └── b5714ebe8357_initial_tables.py
├── alembic.ini
├── app/
│   ├── main.py
│   ├── core/config.py
│   ├── db/session.py
│   ├── models/                # room_type, room, guest, user, booking, payment
│   ├── schemas/               # (khali, Phase 4)
│   └── ...
├── docs/                      # revision notes
├── .env
├── .gitignore
└── requirements.txt
```

---

## 9. Revision Checklist

- [ ] Bata sakta hoon Alembic Git se kaise milta julta hai
- [ ] `env.py` mein har nayi line ka matlab bata sakta hoon
- [ ] Samajhta hoon `import app.models` kyun zaroori hai
- [ ] `alembic revision --autogenerate` aur `alembic upgrade head` ka farq bata sakta hoon
- [ ] Samajhta hoon `alembic_version` mein sirf ek row kyun hoti hai
- [ ] Migration file khol kar `upgrade()` aur `downgrade()` pehchan sakta hoon
- [ ] Lambi error mein pehli aur aakhri lines dekh kar masla dhoond sakta hoon
- [ ] pgAdmin mein tables aur constraints dekh sakta hoon

---

## 10. Aage ka Plan

| Phase | Kaam |
|---|---|
| **Phase 4** | Schemas (Pydantic): API ka data aur validation |
| **Phase 5** | Authentication: password hash, login, JWT |
| **Phase 6** | Asli endpoints: room types aur rooms ki CRUD |

### Alembic ko aage kaise use karenge
Kal agar kisi model mein koi column add karna ho:
1. Model badlo (Python mein)
2. `alembic revision --autogenerate -m "add column x"`
3. Migration file parho
4. `alembic upgrade head`

**Kabhi pgAdmin mein haath se table mat badlo.** Warna Alembic ka record aur asli database alag ho jate hain.

---

## 11. Golden Rules (Aaj ke)

1. Tables hamesha models aur Alembic se badlo, pgAdmin se haath se nahi.
2. Migration chalane se pehle file zaroor parho.
3. Warnings ko nazar-andaz mat karo.
4. Code paste karo to ek ek character milao (ek space bhi masla bana sakta hai).
5. Lambi error mein sirf pehli aur aakhri lines parho.
6. Naya model banao to `models/__init__.py` mein import zaroor likho, warna migration khali banti hai.
7. `alembic_version` table ko kabhi haath se mat chhedo.
