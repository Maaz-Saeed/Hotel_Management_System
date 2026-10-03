# Hotel Management System: Day 2 Revision Notes

**Topic:** Phase 3 (Part 1): Database ke Models
**Aaj ka maqsad:** Database concepts samajhna aur apni 6 tables ke Python models likhna
**Status:** 6 models likhe gaye. Alembic (asli tables banana) kal.

---

## 1. Aaj kya kya hua (Summary)

| # | Kaam | Natija |
|---|---|---|
| 1 | Database ke 5 buniyadi concepts samjhe | Table, Column, Row, PK, FK |
| 2 | `RoomType` aur `Room` model banaye | Pehla FK, pehla relationship |
| 3 | `Guest` aur `User` model banaye | Index, hashed password |
| 4 | `Booking` model banaya | 3 FK, CheckConstraint, snapshot |
| 5 | `Payment` model banaya | One-to-many |
| 6 | Har step ke baad test aur commit kiya | `Models OK` |

---

## 2. Database ke 5 Buniyadi Concepts

Hotel ki register (diary) ki misaal:

| room_number | floor | status |
|---|---|---|
| 101 | 1 | available |
| 102 | 1 | maintenance |

| Concept | Matlab | Misaal |
|---|---|---|
| **Table** | Ek register, ek qisam ki maloomat | `rooms` |
| **Column** | Register ka ek khana (heading) | `room_number`, `floor` |
| **Row** | Register ki ek line, ek asli cheez | Room 101 ki poori line |
| **Primary Key (PK)** | Har row ki **unique pehchan**, kabhi dohrata nahi | `id` (1, 2, 3...) |
| **Foreign Key (FK)** | Ek column jo **doosri table ki row** ko point karta hai | `rooms.room_type_id` ---> `room_types.id` |

### Foreign Key kyun?
Agar har room ke saath "Deluxe, 5000 rupay, 2 log" likhte rahein to 100 kamron par 100 baar likhna parega, aur qeemat badli to 100 jagah badalni paregi. Is ka hal: `room_types` alag table, aur har room sirf us ka `id` yaad rakhe.

```
room_types                      rooms
id | name   | base_price        id | room_number | room_type_id
1  | Single | 3000              1  | 101         | 1   --> Single
2  | Double | 5000              2  | 102         | 2   --> Double
3  | Suite  | 9000              3  | 201         | 3   --> Suite
```

Ek room type ke **bohat se rooms** hote hain. Ise **one-to-many relationship** kehte hain.

### Model kya hota hai?
Ek Python class jo ek table ko bayan karti hai:
- **Class** = table
- **Class ke variables** = columns
- **Class ka object** = ek row

SQL `CREATE TABLE` likhne ki bajaye Python likhte hain, SQLAlchemy usay SQL mein badal deta hai.

---

## 3. Hamari 6 Tables ka Naqsha

```
users           (staff jo system chalate hain)
guests          (mehman)
room_types ──┐
             └─< rooms ──┐
guests ──────────────────┴─< bookings ──< payments
```
`─<` ka matlab "ek se bohat". Ek guest ki bohat si bookings, ek room ki bohat si bookings, ek booking ki bohat si payments.

**Guest aur User ka farq:**

| Table | Kaun? | Login karta hai? |
|---|---|---|
| `users` | Hotel ka staff (admin, receptionist, manager) | Haan |
| `guests` | Mehman jo kamra book karte hain | Nahi |

---

## 4. Saare Models ka Code

### app/models/room_type.py
```python
from decimal import Decimal

from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RoomType(Base):
    __tablename__ = "room_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    capacity: Mapped[int] = mapped_column(default=1)
    description: Mapped[str | None] = mapped_column(String(255))

    rooms: Mapped[list["Room"]] = relationship(back_populates="room_type")
```

### app/models/room.py
```python
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_number: Mapped[str] = mapped_column(String(10), unique=True)
    floor: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="available")

    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_types.id"))
    room_type: Mapped["RoomType"] = relationship(back_populates="rooms")
```

### app/models/guest.py
```python
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Guest(Base):
    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    id_type: Mapped[str] = mapped_column(String(30))
    id_number: Mapped[str] = mapped_column(String(50), index=True)
    address: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

### app/models/user.py
```python
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="receptionist")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

### app/models/booking.py
```python
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    String, Date, DateTime, Numeric, ForeignKey, CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="ck_booking_dates"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    guest_id: Mapped[int] = mapped_column(ForeignKey("guests.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="reserved")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    guest: Mapped["Guest"] = relationship()
    room: Mapped["Room"] = relationship()
    created_by_user: Mapped["User"] = relationship()
```

### app/models/payment.py
```python
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, DateTime, Numeric, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    method: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="completed")
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    booking: Mapped["Booking"] = relationship()
```

### app/models/__init__.py
```python
from app.models.room_type import RoomType
from app.models.room import Room
from app.models.guest import Guest
from app.models.user import User
from app.models.booking import Booking
from app.models.payment import Payment
```
Is file ka kaam: SQLAlchemy aur (kal) Alembic ko batana ke kaun kaun se models mojood hain. **Har naya model banao to yahan import likhna zaroori hai.**

### Test command
```
python -c "from app.models import RoomType, Room, Guest, User, Booking, Payment; from sqlalchemy.orm import configure_mappers; configure_mappers(); print('Models OK')"
```
`configure_mappers()` saare relationships ko jor kar check karta hai. Koi ghalat naam ho to yahin error aa jata hai.

---

## 5. Naye Syntax ka Matlab (Quick Reference)

| Code | Matlab |
|---|---|
| `Mapped[int]` | Number column, khali nahi ho sakta |
| `Mapped[str \| None]` | Text column, khali (`None`) ho sakta hai |
| `mapped_column(primary_key=True)` | Primary key, PostgreSQL khud 1, 2, 3... deta hai |
| `unique=True` | Do rows mein ek jaisi value nahi ho sakti |
| `index=True` | Dhoondna tez ho jata hai (kitab ki fehrist ki tarah) |
| `default="..."` | Python ki taraf se default value |
| `server_default=func.now()` | Database khud waqt likhta hai |
| `String(50)` | Text, zyada se zyada 50 harf |
| `Numeric(10, 2)` | Paison ke liye: 10 digits, 2 ashariya ke baad |
| `Date` | Sirf tarikh |
| `DateTime(timezone=True)` | Tarikh aur waqt, timezone ke saath |
| `ForeignKey("table.id")` | Is column ki value us table ke `id` mein mojood ho |
| `relationship()` | Python ka shortcut (database mein column nahi banta) |
| `back_populates` | Do taraf ke relationships ko jorta hai |
| `CheckConstraint("...")` | Table par qanoon, database khud rokta hai |

### Column aur relationship ka farq
```python
room_type_id: Mapped[int] = mapped_column(ForeignKey("room_types.id"))   # asli column, sirf number
room_type: Mapped["RoomType"] = relationship(back_populates="rooms")      # Python shortcut, poora object
```
Database mein sirf `room_type_id` banta hai. `room_type` sirf Python mein kaam aata hai: `room.room_type.name`.

---

## 6. Aaj ke Sawal aur Jawab (Bohat Zaroori)

### Sawal 1: `room_number` par `unique=True` kyun?
**Jawab:** Taake do rooms ka number ek jaisa na ho.

**Yaad rakho:** `unique=True` koi value **assign nahi karta**, yeh sirf ek **pehra (rule)** hai jo duplicate ko rokta hai. `id` ki value PostgreSQL khud deta hai (`primary_key` ki wajah se), jabke `room_number` aap khud likhte ho. Yeh rule **database** mein lagta hai, is liye pgAdmin ya koi bhi program duplicate nahi daal sakta.

### Sawal 2: `hashed_password` kyun, asli password kyun nahi?
**Jawab:**
1. Hash wapas asli password mein badalna bohat mushkil hai.
2. Database chori ho jaye tab bhi chor ko asli password nahi milta.

**Sudhaar:** Hashing aur encryption **alag** hain.

| | Encryption | Hashing |
|---|---|---|
| Raasta | Do tarfa (chaabi se wapas khulta hai) | **Ek tarfa** (wapas nahi khulta) |
| Misaal | Taale mein saaman | Gosht ka qeema |
| Password ke liye | Ghalat | **Sahi** |

Hash ko "decrypt" nahi karte. Login ke waqt user ka likha hua password **dobara hash** karte hain aur database ke hash se milate hain.

`bcrypt` jaan boojh kar dheema hai aur har password ke saath random "salt" milata hai, taake brute force mushkil ho aur do users ke ek jaise passwords ke hash alag hon.

### Sawal 3: `total_amount` booking mein save kyun?
**Jawab:** Qeemat badalne se purani bookings par asar na pare.

**Poori baat:** Hotel mein hisaab **raaton** ka hota hai.
`total_amount = raatein x us waqt ki base_price`

Yeh booking ke waqt ki qeemat ki **snapshot (tasveer)** hai.

**Misaal:** 3 raat, Double room, 5000 per raat = 15000 ki booking. Agle mahine qeemat 6000 ho gayi. Agar `total_amount` save na karte aur hamesha `base_price x raatein` se nikalte, to purani booking achanak 18000 ki ho jati. Mehman ko 15000 ka kaha tha, 18000 maangna dhoka hota. Accounting aur invoices mein yeh aam usool hai.

### Sawal 4: Paison ke liye `float` kyun nahi, `Numeric` kyun?
**Jawab:** `float` mein addition ka jawab bilkul sahi nahi aata, jaise `0.1 + 0.2`.

**Misaal Python mein:**
```python
>>> 0.1 + 0.2
0.30000000000000004
```
Kyunke computer numbers ko binary mein rakhta hai, aur `0.1` binary mein poora nahi aa sakta (jaise 1/3 ko decimal mein poora nahi likh sakte). Chhote chhote farq jama ho kar hazaron bookings mein hisaab kharab kar dete hain. `Numeric` (Python mein `Decimal`) paison ko bilkul sahi rakhta hai.

**Qaida:** Paison ke liye hamesha `Numeric`/`Decimal`, kabhi `float` nahi.

---

## 7. Design ke Faisle (Kyun aisa kiya?)

| Faisla | Wajah |
|---|---|
| `users` aur `guests` alag tables | Staff login karta hai, mehman nahi |
| `room_types` alag table | Qeemat aur tafseel ek jagah, badalna aasan |
| `payments` alag table | Ek booking ki kai payments ho sakti hain (advance, phir baaqi) |
| `phone` ko `str` rakha | Number par jama ghata nahi karte, aur `0300...` ka zero gum ho jata |
| `room_number` ko `str` rakha | Kamron ke naam `101A` bhi ho sakte hain |
| `id_number` par `index` | CNIC se mehman dhoondna tez ho |
| `is_active` (delete ki bajaye) | Purane records (kis ne booking ki) kharab na hon |
| `created_by` booking mein | Pata chale kaun sa staff member ne booking ki |
| `CheckConstraint` check_out > check_in | Galat tarikhein database level par hi rok di jayein |
| `server_default=func.now()` | Waqt database khud likhta hai, zyada bharosemand |
| Enum ki bajaye `status` String | Abhi aasaan rakha. Baad mein Python Enum se behtar kar sakte hain |

---

## 8. Git Commits (Aaj ke)

```
git add .
git commit -m "Add RoomType and Room models"
git commit -m "Add Guest and User models"
git commit -m "Add Booking model"
git commit -m "Add Payment model"
git log --oneline
```
`git log --oneline` mein ek se zyada line ho aur screen par `:` nazar aaye to `q` dabao.

---

## 9. Errors aur Tips

| Masla | Hal |
|---|---|
| Test mein `NoReferencedTableError` ya `InvalidRequestError` | `__init__.py` mein koi model import karna bhool gaye, ya naam ki spelling ghalat |
| `Models OK` nahi aaya | Aakhri 2-3 lines parho, file ka naam aur line number dekho |
| File save nahi hui | VS Code mein file ke naam ke saath gol nishan (●) ho to Ctrl+S |
| `LF will be replaced by CRLF` | Sirf ittela hai, error nahi, nazar-andaz karo |

---

## 10. Revision Checklist

Kal shuru karne se pehle:

- [ ] Table, column, row, PK, FK ka farq bata sakta hoon
- [ ] Samajhta hoon ke `ForeignKey` aur `relationship` mein kya farq hai
- [ ] `unique=True` aur `primary_key=True` ka farq samajhta hoon
- [ ] Hashing aur encryption ka farq bata sakta hoon
- [ ] `total_amount` ko snapshot kyun kehte hain, samjha sakta hoon
- [ ] `float` aur `Numeric` ka farq, `0.1 + 0.2` ki misaal ke saath
- [ ] Chhe (6) models ke code ko dekh kar har column ka matlab bata sakta hoon
- [ ] `Booking` model ka test (`Models OK`) pass hua aur commit ho gaya

---

## 11. Kal ka Plan: Alembic (Asli Tables Banana)

Abhi tak models sirf **Python code** hain. Database (`hotel_db`) mein abhi koi table **nahi** hai.

1. **Alembic kya hai:** database ki tables ke changes ka record (migration), jaise Git code ke liye.
2. `alembic init alembic` chalana
3. `alembic/env.py` ko apne models aur `.env` se jorna
4. Pehli migration banana: `alembic revision --autogenerate -m "initial tables"`
5. Tables banana: `alembic upgrade head`
6. **pgAdmin mein 6 tables dekhna** (Databases, hotel_db, Schemas, public, Tables)

### Kal shuru karne ka tareeqa
```
cd "C:\Users\EnterCuin Int\Desktop\Intership Tasks\hotel-management-system"
venv\Scripts\activate
git status
```

---

## 12. Golden Rules (Aaj ke)

1. Paison ke liye hamesha `Numeric`/`Decimal`, `float` nahi.
2. Password kabhi plain save nahi, hamesha hash.
3. Naya model banao to `models/__init__.py` mein import zaroor likho.
4. Tables ko pgAdmin se haath se mat badlo, hamesha models aur Alembic se.
5. Har chhote step ke baad test karo aur commit karo.
6. Purani cheez ki qeemat/halat (snapshot) booking mein mehfooz rakho.
