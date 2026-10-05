# Hotel Management System: Day 4 Revision Notes

**Topic:** Phase 4: Schemas (Pydantic)
**Aaj ka maqsad:** API ke andar aane aur bahar jaane wale data ki shakal aur jaanch (validation) tay karna
**Status:** Mukammal. 6 cheezon ke schemas ban gaye, sab tests pass.

---

## 1. Summary (Do din ka kaam)

| # | Kaam | Natija |
|---|---|---|
| 1 | Model aur Schema ka farq samjha | Hifazat + validation |
| 2 | `RoomType` schemas | Create, Update, Out |
| 3 | `Room` schemas | `Literal`, nested schema |
| 4 | `Guest` schemas | `EmailStr`, phone regex |
| 5 | `User` schemas | Password andar aata hai, bahar kabhi nahi |
| 6 | `Booking` schemas | `model_validator`, server-calculated fields |
| 7 | `Payment` schemas | `amount > 0` |
| 8 | Har schema ka sahi aur ghalat data se test | `ValidationError` parhna seekha |

---

## 2. Model aur Schema ka Farq (Sab se ahem sabaq)

| | Model (SQLAlchemy) | Schema (Pydantic) |
|---|---|---|
| Kya bayan karta hai | Database ki table | API ka data (andar kya aaye, bahar kya jaye) |
| Kahan rehta hai | `app/models/` | `app/schemas/` |
| Misaal | `User` mein `hashed_password` hai | Bahar bhejne wale schema mein `hashed_password` **nahi** |

**Do alag cheezein kyun?**
1. **Hifazat:** Model seedha bahar bhejein to `hashed_password` bhi chala jayega. Schema chunta hai ke kya jaye.
2. **Jo client nahi bhej sakta:** `id`, `created_at`, `total_amount` jaisi cheezein server banata hai.
3. **Jaanch:** Ghalat data (manfi qeemat, ghalat email) database tak pahunchne se pehle hi saaf paigham ke saath rad ho jata hai.

### Har cheez ke 3 schemas

| Schema | Kab | Khaas baat |
|---|---|---|
| `Create` | Client nayi cheez banata hai (POST) | `id` nahi hoti |
| `Update` | Client tabdeeli karta hai (PUT/PATCH) | Har field optional (`None`) |
| `Out` | Server jawab deta hai | `id` hoti hai, `from_attributes=True` |

---

## 3. Saare Schemas ka Code

### app/schemas/room_type.py
```python
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RoomTypeBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    base_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    capacity: int = Field(default=1, ge=1, le=10)
    description: str | None = Field(default=None, max_length=255)


class RoomTypeCreate(RoomTypeBase):
    pass


class RoomTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    base_price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    capacity: int | None = Field(default=None, ge=1, le=10)
    description: str | None = Field(default=None, max_length=255)


class RoomTypeOut(RoomTypeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
```

### app/schemas/room.py
```python
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.room_type import RoomTypeOut

RoomStatus = Literal["available", "maintenance"]


class RoomBase(BaseModel):
    room_number: str = Field(min_length=1, max_length=10)
    floor: int = Field(ge=0, le=100)
    status: RoomStatus = "available"


class RoomCreate(RoomBase):
    room_type_id: int


class RoomUpdate(BaseModel):
    room_number: str | None = Field(default=None, min_length=1, max_length=10)
    floor: int | None = Field(default=None, ge=0, le=100)
    status: RoomStatus | None = None
    room_type_id: int | None = None


class RoomOut(RoomBase):
    id: int
    room_type_id: int
    room_type: RoomTypeOut

    model_config = ConfigDict(from_attributes=True)
```

### app/schemas/guest.py
```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

IdType = Literal["CNIC", "Passport", "Other"]


class GuestBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str = Field(pattern=r"^\+?[0-9\- ]{7,20}$")
    id_type: IdType
    id_number: str = Field(min_length=3, max_length=50)
    address: str | None = Field(default=None, max_length=255)


class GuestCreate(GuestBase):
    pass


class GuestUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9\- ]{7,20}$")
    id_type: IdType | None = None
    id_number: str | None = Field(default=None, min_length=3, max_length=50)
    address: str | None = Field(default=None, max_length=255)


class GuestOut(GuestBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### app/schemas/user.py
```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "receptionist", "manager"]


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: Role = "receptionist"


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role: Role | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### app/schemas/booking.py
```python
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.guest import GuestOut
from app.schemas.room import RoomOut

BookingStatus = Literal["reserved", "checked_in", "checked_out", "cancelled"]


class BookingCreate(BaseModel):
    guest_id: int
    room_id: int
    check_in: date
    check_out: date

    @model_validator(mode="after")
    def check_dates(self):
        if self.check_in < date.today():
            raise ValueError("check_in cannot be in the past")
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self


class BookingOut(BaseModel):
    id: int
    check_in: date
    check_out: date
    status: BookingStatus
    total_amount: Decimal
    created_by: int
    created_at: datetime
    guest: GuestOut
    room: RoomOut

    model_config = ConfigDict(from_attributes=True)
```

### app/schemas/payment.py
```python
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PaymentMethod = Literal["cash", "card", "online"]
PaymentStatus = Literal["completed", "refunded"]


class PaymentCreate(BaseModel):
    booking_id: int
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    method: PaymentMethod


class PaymentOut(BaseModel):
    id: int
    booking_id: int
    amount: Decimal
    method: PaymentMethod
    status: PaymentStatus
    paid_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

## 4. Naye Syntax ka Matlab (Quick Reference)

| Code | Matlab |
|---|---|
| `Field(min_length=2, max_length=50)` | Text ki lambai ki had |
| `Field(gt=0)` | "greater than 0", zero se bara |
| `Field(ge=1, le=10)` | "greater or equal", "less or equal" |
| `max_digits`, `decimal_places` | Model ke `Numeric(10, 2)` se match |
| `Field(pattern=r"...")` | Regex se format ki jaanch (jaise phone) |
| `str \| None = None` | Optional field |
| `Literal["a", "b"]` | Sirf yehi values chalengi |
| `EmailStr` | Sahi email format |
| `from_attributes=True` | SQLAlchemy object se data parhne ki ijazat |
| `@model_validator(mode="after")` | Saari fields aane ke baad, aapas mein milakar check |
| `raise ValueError("...")` | Check fail ho to `ValidationError` mein yeh paigham |
| Nested schema (`room: RoomOut`) | Ek schema ke andar doosra, jawab mein poori tafseel |

### Naya package
```
pip install "pydantic[email]"
pip freeze > requirements.txt
```
`EmailStr` ke liye `email-validator` chahiye. `pip freeze` se `requirements.txt` update hoti hai taake naya package wahan bhi aa jaye.

---

## 5. Aaj ke Sawal aur Jawab

### Sawal 1: `RoomTypeCreate` mein `id` kyun nahi, `RoomTypeOut` mein kyun?
**Jawab:** `id` database khud banata hai, client bhej nahi sakta (aur uska haq nahi).

**Sudhaar:** `Out` mein `id` isliye hoti hai ke jawab mein client ko batana hai ke nayi cheez ki `id` kya bani, taake baad mein wo us cheez ko dhoond, badal ya delete kar sake (`GET /room-types/3`).

| Schema | Direction | `id` |
|---|---|---|
| `Create` | Client se server | Nahi |
| `Out` | Server se client | Haan |

### Sawal 2: `status` ko `str` ki bajaye `Literal` kyun?
**Jawab:** Free text database accept na kare, sirf allowed list chale.

**Poori baat:** Model mein `status` sirf `String(20)` hai, to `"availble"` (typo) bhi save ho jata. Phir "available rooms dhoondo" mein woh room **bina kisi error ke ghayab** ho jata. `Literal` is ghalti ko database tak pahunchne se pehle rok deta hai. Bonus: `/docs` par yeh field dropdown ban jati hai.

**Hadd:** Yeh rok sirf API ke raaste se aane wale data par hai. Seedha pgAdmin se likhne wale ko nahi rokta. Is ke liye model par `CheckConstraint` lagta hai.

### Sawal 3: Asli password ko hash kab aur kahan karenge?
**Aap ka jawab:** Model mein store hoga aur `config.py` hash karega.

**Sahi jawab:** Dono ghalat.
1. Asli password **kabhi** model ya database tak nahi pahunchta, model mein sirf `hashed_password` hota hai.
2. Hashing `core/security.py` ka kaam hai, `config.py` ka nahi (woh sirf settings parhta hai).

```
Client: {"password": "mypass123"}
   ↓
UserCreate schema: sirf jaanchta hai (kam az kam 8 characters)
   ↓
crud/user.py: hash_password() bulata hai
   ↓
core/security.py: hash_password() asli hashing karta hai
   ↓
User(hashed_password="$2b$12$...")   <- model mein sirf hash
   ↓
Database
```

| Jagah | Kaam |
|---|---|
| Schema | Jaanchna |
| `core/security.py` | `hash_password()`, `verify_password()` |
| `crud/user.py` | Hash banwana aur model mein save karna |
| Model | Sirf hash rakhna |
| `config.py` | Sirf settings |

Har file ka ek hi kaam. Yehi folder structure ka asli fayda hai.

### Sawal 4: `BookingCreate` mein `total_amount` kyun nahi?
**Aap ka jawab:** Client bheje to ghalat calculate hoga, aur raqam nikalna user ka kaam hai.

**Sahi jawab:** Pehla hissa sahi, doosra ghalat.
- Client par bharosa nahi kar sakte. Wo 15000 ki booking ke liye `100` bhej de to hotel ka nuksan.
- Raqam **server** nikalta hai (user nahi), booking banate waqt:
  `raatein x us waqt ki room_type.base_price`, phir booking mein snapshot ke tor par save.

**Usool:** Jo cheez server khud jaanta hai, wo server likhta hai.

| Field | Kaun deta hai? |
|---|---|
| `guest_id`, `room_id`, `check_in`, `check_out` | Client |
| `total_amount` | Server (hisaab se) |
| `status` | Server (shuru mein `reserved`) |
| `created_by` | Server (login hue user se) |
| `id`, `created_at` | Database |

---

## 6. Design ke Faisle

| Faisla | Wajah |
|---|---|
| `Out` mein password ka koi field nahi | Password kabhi bahar nahi jana chahiye |
| `UserOut` `BaseModel` se bana, `UserCreate` se nahi | Galti se bhi password field copy na ho |
| `max_length=72` password par | `bcrypt` sirf pehle 72 bytes istemal karta hai |
| `min_length=8` password par | Kamzor password (`123`) shuru hi mein rad |
| `phone` ko `str` + regex | Leading zero na gire, aur format bhi check ho |
| `Create` mein `room_type_id`, `Out` mein poora `room_type` | Client ke liye aasan, jawab tafseeli |
| `BookingUpdate` abhi nahi | Check-in, check-out, cancel ke apne qaide hain, alag endpoints se karenge |
| Nested schemas (`BookingOut` mein `guest`, `room`) | Ek jawab mein poori tafseel |
| Schema mein date ka check, database mein bhi `CheckConstraint` | Dohri hifazat, aur client ko saaf paigham |

---

## 7. Errors aur Tips

| Masla | Hal |
|---|---|
| `ImportError: email-validator is not installed` | `pip install "pydantic[email]"` |
| `ValidationError` | Error nahi, schema apna kaam kar raha hai. Har field ki shikayat alag likhi hoti hai |
| `from_attributes` na ho to | Pydantic SQLAlchemy object ko parh nahi sakta |
| Test mein tareekh ka masla | `check_in` guzre din ki ho to rad, tests mein 2027 ki tareekhein use ki |
| `ValidationError` parhna | Field ka naam, wajah aur di hui value teeno dekho |

### Test kaise likhte the
Sahi data se chalao, phir jaan boojh kar ghalat data se. Dono ka natija dekhna zaroori hai:
```
python -c "from app.schemas.room import RoomCreate; print(RoomCreate(room_number='101', floor=1, room_type_id=2))"
python -c "from app.schemas.room import RoomCreate; RoomCreate(room_number='101', floor=1, room_type_id=2, status='broken')"
```

---

## 8. Git Commits (Aaj ke)

```
git commit -m "Add RoomType schemas"
git commit -m "Add Room schemas"
git commit -m "Add Guest and User schemas"
git commit -m "Add Booking and Payment schemas"
```
Har commit se pehle `git status` zaroor dekho.

---

## 9. Final Folder Structure (ab tak)

```
hotel-management-system/
├── alembic/
├── app/
│   ├── main.py
│   ├── core/config.py
│   ├── db/session.py
│   ├── models/        # room_type, room, guest, user, booking, payment
│   ├── schemas/       # room_type, room, guest, user, booking, payment
│   ├── crud/          # (khali)
│   ├── services/      # (khali)
│   └── api/           # (khali)
├── docs/              # revision notes
├── .env
└── requirements.txt
```

---

## 10. Revision Checklist

- [ ] Model aur Schema ka farq bata sakta hoon
- [ ] `Create`, `Update`, `Out` ka farq aur har ek mein kya hota hai
- [ ] `Create` mein `id` kyun nahi, `Out` mein kyun
- [ ] `Literal` ka fayda, aur uski hadd
- [ ] Nested schema kya hai aur kyun use karte hain
- [ ] `UserOut` mein password kyun nahi
- [ ] Password kahan hash hota hai (`core/security.py`) aur kaun bulata hai (`crud`)
- [ ] `total_amount`, `status`, `created_by` client se kyun nahi lete
- [ ] `ValidationError` parh kar bata sakta hoon kis field mein kya galat hai
- [ ] Har schema ka sahi aur ghalat data se test chala sakta hoon

---

## 11. Aage ka Plan

| Phase | Kaam |
|---|---|
| **Phase 5** | Authentication: `core/security.py` (hash, verify, JWT), login endpoint |
| **Phase 6** | Pehle asli endpoints: room types aur rooms ki CRUD |
| **Phase 7** | Guests aur bookings, double-booking ki rok-tham |

### Phase 5 mein kya aayega
1. `hash_password()` aur `verify_password()`
2. `create_access_token()` (JWT)
3. `POST /auth/login`
4. `get_current_user` aur role check (`require_role("admin")`)
5. Pehle admin user ke liye seed script

Phase 5 se pehle ek sawal par soch lo: **JWT token kya hota hai, aur login ke baad server kaise yaad rakhta hai ke aap kaun ho?**

---

## 12. Golden Rules (Aaj ke)

1. Schema database tak data pahunchne se pehle ki chowki hai.
2. Password andar aata hai, bahar kabhi nahi jata.
3. Jo cheez server khud jaanta hai (`id`, `total_amount`, `status`, `created_by`), client se mat lo.
4. Hashing `security.py` mein, `config.py` mein nahi.
5. `Literal` se typo database tak nahi pahunchte.
6. Har schema ko sahi aur ghalat dono data se test karo.
7. `ValidationError` ghalti nahi, schema ka kaam hai.
