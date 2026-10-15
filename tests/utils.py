from datetime import date, timedelta


def day(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()
