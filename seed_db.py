from datetime import datetime, timezone, timedelta
import random
from app.database import SessionLocal, engine, Base
import app.models
from app.models.person import Person
from app.models.organization import Organization
from app.models.location import Location
from app.models.vehicle import Vehicle
from app.models.phone import Phone
from app.models.bank_account import BankAccount
from app.models.case import Case
from app.models.cdr import CDR
from app.models.transaction import Transaction
from app.models.relationship import Relationship

def seed_rich_dataset():
    # 1. Reset database tables cleanly
    from sqlalchemy import text
    conn = engine.connect()
    conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    conn.commit()
    conn.close()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Generating comprehensive synthetic criminal analysis dataset...")

    # 2. Generate 25 Persons
    persons_data = [
        ("P001", "Rajesh", "Verma", "R. Verma", "Male", "1980-04-12", "Indian", "Business Owner", "HIGH", "UNDER_INVESTIGATION", "Alleged syndicate leader operating front companies."),
        ("P002", "Amit", "Shah", "Amit B.", "Male", "1984-09-18", "Indian", "Accountant", "HIGH", "UNDER_INVESTIGATION", "Primary hawala operator and offshore account manager."),
        ("P003", "Suresh", "Menon", "S. Menon", "Male", "1979-01-25", "Indian", "Logistics Coordinator", "MEDIUM", "ACTIVE", "Coordinates transport across state boundaries."),
        ("P004", "Priya", "Sharma", "Priya S.", "Female", "1992-06-30", "Indian", "IT Consultant", "MEDIUM", "ACTIVE", "Managed encrypted messaging channels."),
        ("P005", "Vikram", "Rathore", "V. Rathore", "Male", "1987-11-14", "Indian", "Real Estate Agent", "HIGH", "UNDER_INVESTIGATION", "Acquired properties for money laundering."),
        ("P006", "Karan", "Malhotra", "Karan M.", "Male", "1983-03-22", "Indian", "Import/Export Agent", "HIGH", "ACTIVE", "Oversees trade-based money laundering operations."),
        ("P007", "Ananya", "Deshmukh", "Ananya D.", "Female", "1995-08-09", "Indian", "Bank Manager", "HIGH", "UNDER_INVESTIGATION", "Facilitated high-value suspicious accounts without KYC."),
        ("P008", "Deepak", "Chawla", "D. Chawla", "Male", "1981-12-05", "Indian", "Customs Broker", "MEDIUM", "ACTIVE", "Cleared suspicious shipments at ports."),
        ("P009", "Sunil", "Gupta", "Sunil G.", "Male", "1976-07-19", "Indian", "Jeweller", "HIGH", "ACTIVE", "Converted illicit funds into bullion."),
        ("P010", "Meera", "Joshi", "M. Joshi", "Female", "1990-10-11", "Indian", "Legal Advisor", "MEDIUM", "ACTIVE", "Drafted shell company agreements."),
        ("P011", "Manish", "Tiwari", "M. Tiwari", "Male", "1986-02-28", "Indian", "Driver / Runner", "LOW", "ACTIVE", "Cash courier for localized transactions."),
        ("P012", "Sanjay", "Dube", "S. Dube", "Male", "1989-05-17", "Indian", "Warehouse Supervisor", "MEDIUM", "ACTIVE", "Managed contraband storage facilities."),
        ("P013", "Ritu", "Saxena", "R. Saxena", "Female", "1993-12-01", "Indian", "Front Desk Clerk", "LOW", "ACTIVE", "Handled fake document submissions."),
        ("P014", "Alok", "Nath", "Alok N.", "Male", "1978-08-24", "Indian", "Financier", "HIGH", "UNDER_INVESTIGATION", "Provided initial capital for illegal networks."),
        ("P015", "Kavita", "Rao", "K. Rao", "Female", "1988-04-03", "Indian", "Shell Director", "HIGH", "ACTIVE", "Listed dummy director across 4 corporations."),
        ("P016", "Tarun", "Bhasin", "T. Bhasin", "Male", "1985-10-29", "Indian", "Software Engineer", "MEDIUM", "ACTIVE", "Developed illegal betting platform software."),
        ("P017", "Rahul", "Sharma", "R. Sharma", "Male", "1985-06-12", "Indian", "Trader / Broker", "HIGH", "UNDER_INVESTIGATION", "Key entity identified in multi-city financial transaction trace."),
        ("P018", "Pooja", "Hegde", "Pooja H.", "Female", "1994-01-16", "Indian", "Marketing Executive", "LOW", "ACTIVE", "Promoted online gaming portals."),
        ("P019", "Gaurav", "Kapoor", "G. Kapoor", "Male", "1982-07-07", "Indian", "Hotelier", "MEDIUM", "ACTIVE", "Hosted syndicate strategy meetings."),
        ("P020", "Nikhil", "Roy", "N. Roy", "Male", "1991-09-23", "Indian", "Crypto Broker", "HIGH", "UNDER_INVESTIGATION", "Processed USDT crypto off-ramps."),
        ("P021", "Neha", "Patel", "N. Patel", "Female", "1991-08-04", "Indian", "Accountant", "LOW", "ACTIVE", "Handled wire transfer approvals."),
        ("P022", "Varun", "Dhawan", "V. Dhawan", "Male", "1987-05-31", "Indian", "Automobile Dealer", "MEDIUM", "ACTIVE", "Provided luxury vehicles to syndicate leaders."),
        ("P023", "Simran", "Kaur", "S. Kaur", "Female", "1996-03-14", "Indian", "PR Assistant", "LOW", "ACTIVE", "Managed burner social media handles."),
        ("P024", "Ajay", "Kumar", "AK Logistics", "Male", "1988-11-20", "Indian", "Logistics Manager", "MEDIUM", "ACTIVE", "Primary link between primary suspect and transport networks."),
        ("P031", "Vikram", "Singh", "V. Singh", "Male", "1982-03-15", "Indian", "Financial Consultant", "HIGH", "ACTIVE", "Financial strategist controlling shell company accounts.")
    ]

    persons = []
    for pid, fn, ln, alias, gender, dob, nat, occ, risk, status, notes in persons_data:
        p = Person(
            id=pid, first_name=fn, last_name=ln, full_name=f"{fn} {ln}",
            alias=alias, gender=gender, dob=dob, nationality=nat,
            occupation=occ, risk_level=risk, status=status, notes=notes
        )
        persons.append(p)
        db.add(p)

    # 3. Organizations
    orgs_data = [
        ("ORG001", "Apex Logistics Pvt Ltd", "SHELL_COMPANY", "REG-2024-998", "HIGH", "Suspected front organization for money routing."),
        ("ORG002", "Global Trade Enterprises", "IMPORT_EXPORT", "REG-2023-412", "HIGH", "Under review for trade over-invoicing."),
        ("ORG003", "Starlight Bullion & Gold", "JEWELLERY", "REG-2022-881", "HIGH", "Cash-to-gold conversion conduit."),
        ("ORG004", "Horizon Real Estate Developers", "REAL_ESTATE", "REG-2021-105", "MEDIUM", "Property laundering division."),
        ("ORG005", "CyberTech Software Solutions", "IT_SERVICES", "REG-2025-009", "MEDIUM", "Illegal server hosting infrastructure.")
    ]
    for oid, name, otype, reg, risk, notes in orgs_data:
        db.add(Organization(id=oid, name=name, type=otype, registration_number=reg, risk_level=risk, notes=notes))

    # 4. Locations
    locations_data = [
        ("LOC001", "Bandra Kurla Complex Hub", "BKC Financial District", "Mumbai", "Maharashtra", 19.0657, 72.8686),
        ("LOC002", "Connaught Place Office", "Inner Circle CP", "New Delhi", "Delhi", 28.6315, 77.2167),
        ("LOC003", "Park Street Gold Market", "Park Street Market", "Kolkata", "West Bengal", 22.5532, 88.3524),
        ("LOC004", "MG Road Commercial Tower", "MG Road Hub", "Bengaluru", "Karnataka", 12.9756, 77.6097)
    ]
    for lid, name, addr, city, state, lat, lon in locations_data:
        db.add(Location(id=lid, name=name, address=addr, city=city, state=state, latitude=lat, longitude=lon))

    # 5. Cases
    cases_data = [
        ("C101", "CASE-2026-001", "Operation CyberShield", "CYBER_FINANCIAL_CRIME", "OPEN", "HIGH", "Comprehensive investigation into coordinated cyber fraud and illicit money laundering networks."),
        ("C102", "CASE-2026-002", "Syndicate Alpha Tracking", "ORGANIZED_CRIME", "IN_PROGRESS", "HIGH", "Cross-border intelligence tracking of syndicate key operators."),
        ("C103", "CASE-2026-003", "Gold Bullion Smuggling Probe", "CUSTOMS_FRAUD", "OPEN", "MEDIUM", "Investigation into illegal gold bullion imports and cash laundering."),
        ("C104", "CASE-2026-004", "Hawala Money Routing Network", "MONEY_LAUNDERING", "OPEN", "HIGH", "Detection of multi-city hawala operators.")
    ]
    for cid, cnum, title, ctype, cstat, prio, desc in cases_data:
        db.add(Case(id=cid, case_number=cnum, title=title, type=ctype, status=cstat, priority=prio, description=desc))

    # 6. Relationships
    relationships_data = [
        ("R001", "P001", "PERSON", "P002", "PERSON", "FINANCIAL_PARTNER", 0.98),
        ("R002", "P001", "PERSON", "P006", "PERSON", "ASSOCIATED_WITH", 0.95),
        ("R003", "P002", "PERSON", "P007", "PERSON", "COLLABORATOR", 0.92),
        ("R004", "P002", "PERSON", "P009", "PERSON", "TRANSACTS_WITH", 0.96),
        ("R005", "P003", "PERSON", "P011", "PERSON", "SUPERVISES", 0.88),
        ("R006", "P005", "PERSON", "ORG004", "ORGANIZATION", "DIRECTOR", 0.99),
        ("R007", "P006", "PERSON", "ORG002", "ORGANIZATION", "OWNER", 0.99),
        ("R008", "P009", "PERSON", "ORG003", "ORGANIZATION", "PROPRIETOR", 0.99),
        ("R009", "P017", "PERSON", "P024", "PERSON", "ASSOCIATED_WITH", 0.95),
        ("R010", "P024", "PERSON", "P031", "PERSON", "BUSINESS_PARTNER", 0.90),
        ("R011", "P017", "PERSON", "ORG001", "ORGANIZATION", "DIRECTOR", 0.99),
        ("R012", "P017", "PERSON", "C101", "CASE", "PRIME_SUSPECT", 0.95),
        ("R013", "P001", "PERSON", "C102", "CASE", "KEY_TARGET", 0.97),
        ("R014", "P020", "PERSON", "P002", "PERSON", "CRYPTO_CONDUIT", 0.91),
        ("R015", "P014", "PERSON", "P001", "PERSON", "FINANCIER_OF", 0.94)
    ]
    for rid, src, stype, tgt, ttype, rtype, conf in relationships_data:
        db.add(Relationship(id=rid, source_id=src, source_type=stype, target_id=tgt, target_type=ttype, relationship_type=rtype, confidence_score=conf))

    # 7. CDRs (Call Detail Records)
    base_time = datetime.now(timezone.utc) - timedelta(days=5)
    cdrs_data = [
        ("CDR101", "9876543201", "9876543202", "P001", "P002", 340, base_time + timedelta(hours=2)),
        ("CDR102", "9876543202", "9876543207", "P002", "P007", 520, base_time + timedelta(hours=5)),
        ("CDR103", "9876543206", "9876543209", "P006", "P009", 180, base_time + timedelta(hours=8)),
        ("CDR104", "9876543217", "9876543224", "P017", "P024", 180, base_time + timedelta(hours=12)),
        ("CDR105", "9876543224", "9876543225", "P024", "P031", 420, base_time + timedelta(hours=14)),
        ("CDR106", "9876543220", "9876543202", "P020", "P002", 650, base_time + timedelta(hours=18)),
        ("CDR107", "9876543214", "9876543201", "P014", "P001", 890, base_time + timedelta(hours=22))
    ]
    for cid, cp, rp, cpid, rpid, dur, ts in cdrs_data:
        db.add(CDR(id=cid, caller_phone=cp, receiver_phone=rp, caller_person_id=cpid, receiver_person_id=rpid, duration_seconds=dur, timestamp=ts))

    # 8. Transactions
    txs_data = [
        ("TX1001", "ACC001", "ACC002", "P001", "P002", 2500000.0, "INR", "WIRE", base_time + timedelta(hours=1)),
        ("TX1002", "ACC002", "ACC009", "P002", "P009", 1800000.0, "INR", "WIRE", base_time + timedelta(hours=4)),
        ("TX1003", "ACC006", "ACC003", "P006", "ORG003", 4500000.0, "INR", "IMPS", base_time + timedelta(hours=7)),
        ("TX1004", "ACC017", "ACC024", "P017", "P024", 500000.0, "INR", "WIRE", base_time + timedelta(hours=11)),
        ("TX1005", "ACC024", "ACC025", "P024", "P031", 1200000.0, "INR", "WIRE", base_time + timedelta(hours=13)),
        ("TX1006", "ACC020", "ACC002", "P020", "P002", 3200000.0, "INR", "CRYPTO_OFFRAMP", base_time + timedelta(hours=19)),
        ("TX1007", "ACC014", "ACC001", "P014", "P001", 7500000.0, "INR", "HAWALA_CREDIT", base_time + timedelta(hours=23))
    ]
    for tid, sa, ra, spid, rpid, amt, curr, ttype, ts in txs_data:
        db.add(Transaction(id=tid, sender_account=sa, receiver_account=ra, sender_person_id=spid, receiver_person_id=rpid, amount=amt, currency=curr, transaction_type=ttype, timestamp=ts))

    db.commit()
    print(f"Successfully seeded dataset into PostgreSQL! Total Persons: {db.query(Person).count()}, Cases: {db.query(Case).count()}, Organizations: {db.query(Organization).count()}")
    db.close()

if __name__ == "__main__":
    seed_rich_dataset()
