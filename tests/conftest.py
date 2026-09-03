from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
import app.models
from app.main import app
from app.models.person import Person
from app.models.case import Case
from app.models.organization import Organization
from app.models.phone import Phone
from app.models.relationship import Relationship
from app.models.cdr import CDR
from app.models.transaction import Transaction

# In-memory SQLite engine for unit tests with StaticPool
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # 1. Seed Persons
    p1 = Person(
        id="P017",
        first_name="Rahul",
        last_name="Sharma",
        full_name="Rahul Sharma",
        alias="R. Sharma",
        gender="Male",
        dob="1985-06-12",
        nationality="Indian",
        occupation="Trader",
        risk_level="HIGH",
        status="UNDER_INVESTIGATION",
        notes="Key entity connected to syndicate"
    )
    p2 = Person(
        id="P024",
        first_name="Ajay",
        last_name="Kumar",
        full_name="Ajay Kumar",
        alias="AK",
        gender="Male",
        dob="1988-11-20",
        nationality="Indian",
        occupation="Logistics Manager",
        risk_level="MEDIUM",
        status="ACTIVE",
        notes="Frequent associate"
    )
    p3 = Person(
        id="P031",
        first_name="Vikram",
        last_name="Singh",
        full_name="Vikram Singh",
        risk_level="HIGH",
        status="ACTIVE"
    )

    # 2. Seed Cases
    c1 = Case(
        id="C101",
        case_number="CASE-2026-001",
        title="Operation CyberShield",
        type="CYBERCRIME",
        status="OPEN",
        priority="HIGH",
        description="Investigation into illicit financial networks."
    )

    # 3. Seed Relationships
    rel1 = Relationship(
        id="R101",
        source_id="P017",
        source_type="PERSON",
        target_id="P024",
        target_type="PERSON",
        relationship_type="ASSOCIATED_WITH",
        confidence_score=0.95
    )
    rel2 = Relationship(
        id="R102",
        source_id="P024",
        source_type="PERSON",
        target_id="P031",
        target_type="PERSON",
        relationship_type="ASSOCIATED_WITH",
        confidence_score=0.90
    )

    # 4. Seed CDR
    cdr1 = CDR(
        id="104",
        caller_phone="9876543210",
        receiver_phone="9876543211",
        caller_person_id="P017",
        receiver_person_id="P024",
        duration_seconds=180,
        timestamp=datetime.now(timezone.utc)
    )

    # 5. Seed Transaction
    tx1 = Transaction(
        id="1029",
        sender_account="ACC001",
        receiver_account="ACC002",
        sender_person_id="P017",
        receiver_person_id="P024",
        amount=500000.0,
        currency="INR",
        timestamp=datetime.now(timezone.utc)
    )

    session.add_all([p1, p2, p3, c1, rel1, rel2, cdr1, tx1])
    session.commit()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
