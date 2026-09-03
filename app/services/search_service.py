from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.models.person import Person
from app.models.organization import Organization
from app.models.location import Location
from app.models.vehicle import Vehicle
from app.models.phone import Phone
from app.models.bank_account import BankAccount
from app.models.case import Case
from app.schemas.search import SearchResultItem

class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search_all(self, query: str, limit: int = 20) -> List[SearchResultItem]:
        pattern = f"%{query.strip()}%"
        results: List[SearchResultItem] = []

        # 1. Search Persons
        person_stmt = select(Person).where(
            or_(
                Person.full_name.ilike(pattern),
                Person.first_name.ilike(pattern),
                Person.last_name.ilike(pattern),
                Person.alias.ilike(pattern),
                Person.id.ilike(pattern)
            )
        ).limit(limit)
        for p in self.db.scalars(person_stmt).all():
            results.append(SearchResultItem(id=p.id, type="PERSON", name=p.full_name, matching_field="full_name"))

        # 2. Search Organizations
        org_stmt = select(Organization).where(
            or_(Organization.name.ilike(pattern), Organization.id.ilike(pattern))
        ).limit(limit)
        for org in self.db.scalars(org_stmt).all():
            results.append(SearchResultItem(id=org.id, type="ORGANIZATION", name=org.name, matching_field="name"))

        # 3. Search Locations
        loc_stmt = select(Location).where(
            or_(Location.name.ilike(pattern), Location.city.ilike(pattern), Location.id.ilike(pattern))
        ).limit(limit)
        for loc in self.db.scalars(loc_stmt).all():
            results.append(SearchResultItem(id=loc.id, type="LOCATION", name=loc.name, matching_field="name"))

        # 4. Search Vehicles
        veh_stmt = select(Vehicle).where(
            or_(Vehicle.license_plate.ilike(pattern), Vehicle.id.ilike(pattern))
        ).limit(limit)
        for v in self.db.scalars(veh_stmt).all():
            results.append(SearchResultItem(id=v.id, type="VEHICLE", name=f"{v.make or ''} {v.model or ''} ({v.license_plate})", matching_field="license_plate"))

        # 5. Search Phones
        phone_stmt = select(Phone).where(
            or_(Phone.phone_number.ilike(pattern), Phone.id.ilike(pattern))
        ).limit(limit)
        for ph in self.db.scalars(phone_stmt).all():
            results.append(SearchResultItem(id=ph.id, type="PHONE", name=ph.phone_number, matching_field="phone_number"))

        # 6. Search Bank Accounts
        acc_stmt = select(BankAccount).where(
            or_(BankAccount.account_number.ilike(pattern), BankAccount.id.ilike(pattern))
        ).limit(limit)
        for acc in self.db.scalars(acc_stmt).all():
            results.append(SearchResultItem(id=acc.id, type="BANK_ACCOUNT", name=f"{acc.bank_name or ''} {acc.account_number}", matching_field="account_number"))

        # 7. Search Cases
        case_stmt = select(Case).where(
            or_(Case.title.ilike(pattern), Case.case_number.ilike(pattern), Case.id.ilike(pattern))
        ).limit(limit)
        for c in self.db.scalars(case_stmt).all():
            results.append(SearchResultItem(id=c.id, type="CASE", name=f"Case {c.case_number}: {c.title}", matching_field="title"))

        return results[:limit]
