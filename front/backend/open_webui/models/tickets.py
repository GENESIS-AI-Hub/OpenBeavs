from pydantic import BaseModel, Field
from typing import Optional
import time
import uuid

from sqlalchemy import BigInteger, Column, String, Text
from open_webui.internal.db import Base, JSONField, get_db

####################
# Ticket DB Schema
####################

class Ticket(Base):
    __tablename__ = "ticket"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    name = Column(String)
    email = Column(String)
    issue_type = Column(String)
    description = Column(Text)
    info = Column(JSONField)  # Renamed from metadata to avoid conflict with Base.metadata
    status = Column(String, default="new")
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)
    resolved_at = Column(BigInteger, nullable=True)

class TicketModel(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    email: str
    issue_type: str
    description: str
    metadata: dict
    status: str
    created_at: int
    updated_at: int
    resolved_at: Optional[int] = None

    class Config:
        from_attributes = True

####################
# Forms
####################

class TicketForm(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    issue_type: str = Field(..., pattern=r"^(bug|feature_request|general_feedback)$")
    description: str = Field(..., min_length=10, max_length=5000)
    metadata: dict = Field(default_factory=dict)

class TicketUpdateForm(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(new|in_progress|resolved|closed)$")

####################
# Ticket Table
####################

class TicketsTable:
    def insert_new_ticket(
        self, form_data: TicketForm, user_id: Optional[str] = None
    ) -> Optional[TicketModel]:
        with get_db() as db:
            ticket_id = str(uuid.uuid4())
            timestamp = int(time.time())
            
            ticket = Ticket(
                id=ticket_id,
                user_id=user_id,
                name=form_data.name,
                email=form_data.email,
                issue_type=form_data.issue_type,
                description=form_data.description,
                info=form_data.metadata,
                status="new",
                created_at=timestamp,
                updated_at=timestamp,
                resolved_at=None,
            )
            
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            
            return TicketModel(
                id=ticket.id,
                user_id=ticket.user_id,
                name=ticket.name,
                email=ticket.email,
                issue_type=ticket.issue_type,
                description=ticket.description,
                metadata=ticket.info if ticket.info else {},
                status=ticket.status,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
                resolved_at=ticket.resolved_at
            )

    def get_ticket_by_id(self, ticket_id: str) -> Optional[TicketModel]:
        try:
            with get_db() as db:
                ticket = db.query(Ticket).filter_by(id=ticket_id).first()
                if ticket:
                    return TicketModel(
                        id=ticket.id,
                        user_id=ticket.user_id,
                        name=ticket.name,
                        email=ticket.email,
                        issue_type=ticket.issue_type,
                        description=ticket.description,
                        metadata=ticket.info if ticket.info else {},
                        status=ticket.status,
                        created_at=ticket.created_at,
                        updated_at=ticket.updated_at,
                        resolved_at=ticket.resolved_at
                    )
                return None
        except Exception:
            return None

    def get_all_tickets(
        self, status: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> list[TicketModel]:
        try:
            with get_db() as db:
                query = db.query(Ticket)
                if status:
                    query = query.filter_by(status=status)
                
                query = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit)
                tickets = query.all()
                
                return [
                    TicketModel(
                        id=t.id,
                        user_id=t.user_id,
                        name=t.name,
                        email=t.email,
                        issue_type=t.issue_type,
                        description=t.description,
                        metadata=t.info if t.info else {},
                        status=t.status,
                        created_at=t.created_at,
                        updated_at=t.updated_at,
                        resolved_at=t.resolved_at
                    ) for t in tickets
                ]
        except Exception as e:
            print(f"Error getting tickets: {e}")
            return []

    def update_ticket_by_id(
        self, ticket_id: str, form_data: TicketUpdateForm
    ) -> Optional[TicketModel]:
        try:
            with get_db() as db:
                ticket = db.query(Ticket).filter_by(id=ticket_id).first()
                if not ticket:
                    return None
                
                if form_data.status:
                    ticket.status = form_data.status
                    ticket.updated_at = int(time.time())
                    
                    if form_data.status == "resolved" and ticket.status != "resolved":
                        ticket.resolved_at = int(time.time())
                        
                    db.commit()
                    db.refresh(ticket)
                    
                    return TicketModel(
                        id=ticket.id,
                        user_id=ticket.user_id,
                        name=ticket.name,
                        email=ticket.email,
                        issue_type=ticket.issue_type,
                        description=ticket.description,
                        metadata=ticket.info if ticket.info else {},
                        status=ticket.status,
                        created_at=ticket.created_at,
                        updated_at=ticket.updated_at,
                        resolved_at=ticket.resolved_at
                    )
                return None
        except Exception as e:
            print(f"Error updating ticket: {e}")
            return None

    def delete_ticket_by_id(self, ticket_id: str) -> bool:
        try:
            with get_db() as db:
                db.query(Ticket).filter_by(id=ticket_id).delete()
                db.commit()
                return True
        except Exception:
            return False

    def get_ticket_count(self, status: Optional[str] = None) -> int:
        try:
            with get_db() as db:
                query = db.query(Ticket)
                if status:
                    query = query.filter_by(status=status)
                return query.count()
        except Exception:
            return 0

Tickets = TicketsTable()
