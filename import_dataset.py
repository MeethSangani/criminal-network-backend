import os
import sys
import argparse
import pandas as pd
from datetime import datetime, timezone
import math

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

DEFAULT_DATASET_DIR = r"C:\Users\DELL\Downloads\sih-criminal-person3-clean 1"

def parse_datetime(val):
    if pd.isna(val) or not val:
        return datetime.now(timezone.utc)
    try:
        dt = pd.to_datetime(val)
        if dt.tzinfo is None:
            return dt.tz_localize(timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def ingest_sih_dataset(dataset_dir: str):
    print(f"Ingesting full SIH dataset from '{dataset_dir}' into PostgreSQL...")

    # 1. Clean Reset PostgreSQL Schema
    from sqlalchemy import text
    conn = engine.connect()
    conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    conn.commit()
    conn.close()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # A. Locations
        loc_path = os.path.join(dataset_dir, "base_data", "locations.csv")
        if os.path.exists(loc_path):
            df_loc = pd.read_csv(loc_path)
            loc_objs = []
            for _, row in df_loc.iterrows():
                loc_objs.append(Location(
                    id=str(row['location_id']),
                    name=str(row['location_name']),
                    address=str(row['location_name']),
                    city=str(row.get('city', 'Unknown')),
                    state=str(row.get('state', 'Unknown')),
                    latitude=float(row['latitude']) if not pd.isna(row['latitude']) else None,
                    longitude=float(row['longitude']) if not pd.isna(row['longitude']) else None
                ))
            db.bulk_save_objects(loc_objs)
            db.commit()
            print(f"[OK] Imported {len(loc_objs)} Locations.")

        # B. Organizations
        org_path = os.path.join(dataset_dir, "base_data", "organizations.csv")
        if os.path.exists(org_path):
            df_org = pd.read_csv(org_path)
            org_objs = []
            for _, row in df_org.iterrows():
                org_objs.append(Organization(
                    id=str(row['organization_id']),
                    name=str(row['organization_name']),
                    type=str(row['organization_type']),
                    registration_number=f"REG-{row['organization_id']}",
                    risk_level="MEDIUM",
                    notes=""
                ))
            db.bulk_save_objects(org_objs)
            db.commit()
            print(f"[OK] Imported {len(org_objs)} Organizations.")

        # C. Cases
        cases_path = os.path.join(dataset_dir, "base_data", "cases.csv")
        if os.path.exists(cases_path):
            df_cases = pd.read_csv(cases_path)
            case_objs = []
            for _, row in df_cases.iterrows():
                sev = str(row.get('severity', 'MEDIUM')).upper()
                case_objs.append(Case(
                    id=str(row['case_id']),
                    case_number=f"CASE-{row['case_id']}",
                    title=f"{row['case_type']} Case {row['case_id']}",
                    type=str(row['case_type']),
                    status=str(row.get('status', 'OPEN')).upper(),
                    priority="HIGH" if sev == "HIGH" else ("LOW" if sev == "LOW" else "MEDIUM"),
                    description=str(row.get('description', 'Synthetic investigation file.'))
                ))
            db.bulk_save_objects(case_objs)
            db.commit()
            print(f"[OK] Imported {len(case_objs)} Cases.")

        # D. Phones
        phones_path = os.path.join(dataset_dir, "base_data", "phone_numbers.csv")
        phone_map = {}
        if os.path.exists(phones_path):
            df_phones = pd.read_csv(phones_path)
            phone_objs = []
            for _, row in df_phones.iterrows():
                pid = str(row['phone_id'])
                pnum = str(row['phone_number'])
                phone_map[pid] = pnum
                phone_objs.append(Phone(
                    id=pid,
                    phone_number=pnum,
                    carrier=str(row.get('phone_type', 'Mobile'))
                ))
            db.bulk_save_objects(phone_objs)
            db.commit()
            print(f"[OK] Imported {len(phone_objs)} Phone Numbers.")

        # E. Persons
        persons_path = os.path.join(dataset_dir, "base_data", "persons.csv")
        person_phone_map = {}
        if os.path.exists(persons_path):
            df_persons = pd.read_csv(persons_path)
            person_objs = []
            for _, row in df_persons.iterrows():
                pid = str(row['person_id'])
                fn_full = str(row['full_name']).strip()
                parts = fn_full.split()
                first_name = parts[0] if parts else fn_full
                last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                gender_str = "Female" if str(row.get('gender', 'M')).upper() in ['F', 'FEMALE'] else "Male"
                
                ph_id = str(row.get('phone_id', ''))
                if ph_id and ph_id != 'nan':
                    person_phone_map[ph_id] = pid

                person_objs.append(Person(
                    id=pid,
                    first_name=first_name,
                    last_name=last_name,
                    full_name=fn_full,
                    alias=f"{first_name} {last_name[:1]}." if last_name else first_name,
                    gender=gender_str,
                    dob=str(row.get('date_of_birth', '1985-01-01')),
                    nationality="Indian",
                    occupation=str(row.get('occupation', 'Business')),
                    risk_level="HIGH" if pid in ['P001', 'P002', 'P017', 'P031', 'P050', 'P100'] else "MEDIUM",
                    status="UNDER_INVESTIGATION" if pid in ['P001', 'P017'] else "ACTIVE",
                    notes=f"Location City: {row.get('city', 'India')}"
                ))
            db.bulk_save_objects(person_objs)
            db.commit()
            print(f"[OK] Imported {len(person_objs)} Persons.")

        # F. Bank Accounts
        accounts_path = os.path.join(dataset_dir, "base_data", "bank_accounts.csv")
        account_person_map = {}
        if os.path.exists(accounts_path):
            df_accounts = pd.read_csv(accounts_path)
            acc_objs = []
            for _, row in df_accounts.iterrows():
                aid = str(row['account_id'])
                anum = str(row['account_number'])
                pid = str(row['person_id'])
                account_person_map[aid] = pid
                acc_objs.append(BankAccount(
                    id=aid,
                    account_number=anum,
                    bank_name=str(row.get('bank_name', 'National Bank')),
                    branch=str(row.get('account_type', 'Current')),
                    owner_id=pid
                ))
            db.bulk_save_objects(acc_objs)
            db.commit()
            print(f"[OK] Imported {len(acc_objs)} Bank Accounts.")

        # G. Relationships (Graph Edges)
        edges_path = os.path.join(dataset_dir, "graph_data", "edges.csv")
        if os.path.exists(edges_path):
            df_edges = pd.read_csv(edges_path)
            rel_objs = []
            for _, row in df_edges.iterrows():
                eid = str(row['edge_id'])
                src_raw = str(row['source_id'])
                tgt_raw = str(row['target_id'])
                src = src_raw.split(':')[-1]
                tgt = tgt_raw.split(':')[-1]
                conf = float(row['confidence']) if not pd.isna(row['confidence']) else 0.90
                
                rel_objs.append(Relationship(
                    id=eid,
                    source_id=src,
                    source_type=str(row['source_type']),
                    target_id=tgt,
                    target_type=str(row['target_type']),
                    relationship_type=str(row['relationship']),
                    confidence_score=conf
                ))
            batch_size = 2000
            for i in range(0, len(rel_objs), batch_size):
                db.bulk_save_objects(rel_objs[i:i+batch_size])
                db.commit()
            print(f"[OK] Imported {len(rel_objs)} Relationships/Edges.")

        # H. Call Detail Records (CDRs)
        cdr_path = os.path.join(dataset_dir, "output", "cdr.csv")
        if os.path.exists(cdr_path):
            df_cdr = pd.read_csv(cdr_path)
            cdr_objs = []
            for _, row in df_cdr.iterrows():
                cid = str(row['cdr_id'])
                cp_id = str(row['caller_phone_id'])
                rp_id = str(row['receiver_phone_id'])
                caller_num = phone_map.get(cp_id, cp_id)
                receiver_num = phone_map.get(rp_id, rp_id)
                c_pid = person_phone_map.get(cp_id)
                r_pid = person_phone_map.get(rp_id)
                dur = int(row['duration_seconds']) if not pd.isna(row['duration_seconds']) else 120
                ts = parse_datetime(row.get('timestamp'))

                cdr_objs.append(CDR(
                    id=cid,
                    caller_phone=caller_num,
                    receiver_phone=receiver_num,
                    caller_person_id=c_pid,
                    receiver_person_id=r_pid,
                    duration_seconds=dur,
                    timestamp=ts
                ))
            batch_size = 1000
            for i in range(0, len(cdr_objs), batch_size):
                db.bulk_save_objects(cdr_objs[i:i+batch_size])
                db.commit()
            print(f"[OK] Imported {len(cdr_objs)} Call Detail Records (CDRs).")

        # I. Transactions
        tx_path = os.path.join(dataset_dir, "output", "transactions.csv")
        if os.path.exists(tx_path):
            df_tx = pd.read_csv(tx_path)
            tx_objs = []
            for _, row in df_tx.iterrows():
                tid = str(row['transaction_id'])
                fa_id = str(row['from_account_id'])
                ta_id = str(row['to_account_id'])
                s_pid = account_person_map.get(fa_id)
                r_pid = account_person_map.get(ta_id)
                amt = float(row['amount']) if not pd.isna(row['amount']) else 10000.0
                ts = parse_datetime(row.get('timestamp'))

                tx_objs.append(Transaction(
                    id=tid,
                    sender_account=fa_id,
                    receiver_account=ta_id,
                    sender_person_id=s_pid,
                    receiver_person_id=r_pid,
                    amount=amt,
                    currency="INR",
                    transaction_type=str(row.get('transaction_type', 'Transfer')),
                    timestamp=ts
                ))
            batch_size = 1000
            for i in range(0, len(tx_objs), batch_size):
                db.bulk_save_objects(tx_objs[i:i+batch_size])
                db.commit()
            print(f"[OK] Imported {len(tx_objs)} Financial Transactions.")

        print("\n=======================================================")
        print(f"[COMPLETE] PostgreSQL is now fully populated with the SIH dataset!")
        print(f"Persons: {db.query(Person).count()}")
        print(f"Cases: {db.query(Case).count()}")
        print(f"Organizations: {db.query(Organization).count()}")
        print(f"Locations: {db.query(Location).count()}")
        print(f"Phones: {db.query(Phone).count()}")
        print(f"Bank Accounts: {db.query(BankAccount).count()}")
        print(f"Relationships: {db.query(Relationship).count()}")
        print(f"CDRs: {db.query(CDR).count()}")
        print(f"Transactions: {db.query(Transaction).count()}")
        print("=======================================================\n")

    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Ingest full SIH dataset into PostgreSQL.")
    parser.add_argument("--dir", type=str, default=DEFAULT_DATASET_DIR, help="Path to SIH dataset folder")
    args = parser.parse_args()

    ingest_sih_dataset(args.dir)

if __name__ == "__main__":
    main()
