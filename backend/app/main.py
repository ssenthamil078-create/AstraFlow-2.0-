"""
Phase 3 — FastAPI application entrypoint.
Phase 4 — adds the financial-state (digital twin) and goals routers.
Phase 5 — adds the income-sources (reliability score) router.
Phase 6 — adds the auth router (register/login/verify-email) and moves
every other router from a plain `user_id` query param to the
authenticated caller (see app.api.deps.get_current_user).

Wires together the auth router, the ingestion router (CSV/SMS/document
upload), the events router (review queue, confirm, merge), the
financial-state router (rebuild/read/timeline/provenance), the goals
router, and the income-sources router (create source, record
observations, read/recalculate reliability). `init_db()` runs on startup
so the hackathon build has zero manual migration steps — swap to Alembic
when the project needs versioned migrations for real (roadmap Phase 11).
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file (local dev only — Render injects real env vars directly)

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routers import auth, chat, events, financial_state, goals, income_sources, ingestion
from app.core.database import init_db
from app.models.user import UserORM


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AstraFlow API",
    description=(
        "Uncertainty-aware financial operating system. Recommendation-only — "
        "see app.core.boundaries.forbid_money_movement(); nothing in this API "
        "ever moves money."
    ),
    version="0.6.0",
    lifespan=lifespan,
)

# Enable CORS for frontend Vite dev server & the deployed Vercel frontend.
# Set ASTRAFLOW_CORS_ORIGINS in Render to a comma-separated list of allowed
# origins, e.g. "https://astraflow.vercel.app,https://astraflow-git-main-you.vercel.app".
# Falls back to "*" (any origin) if unset, which is fine for a hackathon demo
# but should be tightened before anything resembling production use.
_cors_origins_env = os.environ.get("ASTRAFLOW_CORS_ORIGINS", "").strip()
_allow_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
if not _allow_origins:
    _allow_origins = [
        "https://astra-flow-2-0.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "phase": 6}


app.include_router(auth.router)
app.include_router(ingestion.router)
app.include_router(events.router)
app.include_router(financial_state.router)
app.include_router(goals.router)
app.include_router(income_sources.router)
app.include_router(chat.router)


@app.get("/api/provenance")
def provenance_alias(
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    from app.core.vocabulary import Currency
    from app.services import financial_twin
    return financial_twin.build_provenance(session, current_user.id, Currency.INR)



@app.post("/api/demo/seed")
def seed_demo_data(
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    from datetime import date
    from decimal import Decimal
    from app.core.vocabulary import Currency, EventDirection, EventStatus, GoalType, ObligationCategory
    from app.models.financial_event import FinancialEventORM
    from app.models.goal import GoalORM
    from app.models.income_source import IncomeSourceORM
    from app.api.routers.financial_state import _compute_full_visual_state

    # Remove existing
    session.query(FinancialEventORM).filter(FinancialEventORM.user_id == current_user.id).delete()
    session.query(GoalORM).filter(GoalORM.user_id == current_user.id).delete()
    session.query(IncomeSourceORM).filter(IncomeSourceORM.user_id == current_user.id).delete()

    # Seed initial events
    demo_events = [
        FinancialEventORM(
            user_id=current_user.id,
            title="Monthly Executive Salary",
            amount=Decimal("210000.00"),
            direction=EventDirection.CREDIT.value,
            currency=Currency.INR.value,
            date_occurred=date(2026, 8, 1),
            category="Salary",
            confidence=Decimal("0.99"),
            status=EventStatus.CONFIRMED.value,
            source="CSV Import",
            raw_evidence={"snippet": "SALARY CREDIT CORP ACH ID #98231 +210,000.00 CR"},
        ),
        FinancialEventORM(
            user_id=current_user.id,
            title="UI/UX Architecture Consulting",
            amount=Decimal("45000.00"),
            direction=EventDirection.CREDIT.value,
            currency=Currency.INR.value,
            date_occurred=date(2026, 8, 12),
            category="Consulting",
            confidence=Decimal("0.92"),
            status=EventStatus.CONFIRMED.value,
            source="CSV Import",
            raw_evidence={"snippet": "INWARD WIRE TXN - RET-CLIENT-AURA +45,000.00 CR"},
        ),
        FinancialEventORM(
            user_id=current_user.id,
            title="Penthouse Apartment Lease",
            amount=Decimal("65000.00"),
            direction=EventDirection.DEBIT.value,
            currency=Currency.INR.value,
            date_occurred=date(2026, 8, 5),
            category="Housing",
            confidence=Decimal("0.96"),
            status=EventStatus.CONFIRMED.value,
            source="CSV Import",
            raw_evidence={"snippet": "AUTO-DEBIT LEASE PROPERTY MGMT -65,000.00 DR"},
        ),
        FinancialEventORM(
            user_id=current_user.id,
            title="SIP Mutual Fund Wealth Compounding",
            amount=Decimal("35000.00"),
            direction=EventDirection.DEBIT.value,
            currency=Currency.INR.value,
            date_occurred=date(2026, 8, 10),
            category="Investments",
            confidence=Decimal("0.98"),
            status=EventStatus.CONFIRMED.value,
            source="CSV Import",
            raw_evidence={"snippet": "NACH SIP BATCH - UT-NIFTY-50 -35,000.00 DR"},
        ),
        FinancialEventORM(
            user_id=current_user.id,
            title="Cloud Infrastructure & Dev Cluster",
            amount=Decimal("14200.00"),
            direction=EventDirection.DEBIT.value,
            currency=Currency.INR.value,
            date_occurred=date(2026, 8, 18),
            category="Tech Infrastructure",
            confidence=Decimal("0.94"),
            status=EventStatus.CONFIRMED.value,
            source="CSV Import",
            raw_evidence={"snippet": "AWS EMEA HOSTING & CLOUD SVCS -14,200.00 DR"},
        ),
        FinancialEventORM(
            user_id=current_user.id,
            title="Uncategorized Transfer to UPI-INVEST91",
            amount=Decimal("50000.00"),
            direction=EventDirection.DEBIT.value,
            currency=Currency.INR.value,
            date_occurred=date(2026, 8, 26),
            category="Transfers",
            confidence=Decimal("0.62"),
            status=EventStatus.UNCERTAIN.value,
            source="SMS Import",
            raw_evidence={"snippet": "INR 50,000.00 transferred via UPI to UPI-INVEST91 on 26-08-2026"},
        ),
    ]
    session.add_all(demo_events)

    # Seed income sources
    source = IncomeSourceORM(
        user_id=current_user.id,
        name="Primary Tech Salary (Infosys)",
        category="Salary",
        typical_amount=Decimal("210000.00"),
        reliability_score=Decimal("96.0"),
        observation_count=18,
        is_provisional=False,
        amount_consistency_score=Decimal("98.0"),
        timeliness_score=Decimal("95.0"),
        data_confidence_score=Decimal("99.0"),
    )
    session.add(source)

    # Seed goal
    goal = GoalORM(
        user_id=current_user.id,
        name="Emergency Runway Reserve",
        goal_type=GoalType.SAVINGS_TARGET.value,
        linked_category=ObligationCategory.RENT.value,
        target_amount=Decimal("500000.00"),
        currency=Currency.INR.value,
    )
    state, _ = financial_twin.rebuild_and_persist(session, current_user.id, Currency.INR)
    session.commit()
    return {
        "success": True,
        "message": "Demo universe populated with verified portfolio records.",
        "state": state,
    }


@app.post("/api/demo/reset")
def reset_demo_data(
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    from app.models.financial_event import FinancialEventORM
    from app.models.goal import GoalORM
    from app.models.income_source import IncomeSourceORM
    from app.services import financial_twin

    session.query(FinancialEventORM).filter(FinancialEventORM.user_id == current_user.id).delete()
    session.query(GoalORM).filter(GoalORM.user_id == current_user.id).delete()
    session.query(IncomeSourceORM).filter(IncomeSourceORM.user_id == current_user.id).delete()
    session.commit()

    state = financial_twin.get_current_state(session, current_user.id, Currency.INR)
    return {
        "success": True,
        "message": "Universe reset to pristine empty state.",
        "state": state,
    }


