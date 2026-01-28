from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import time
from collections import defaultdict

from open_webui.models.tickets import (
    Tickets,
    TicketForm,
    TicketModel,
    TicketUpdateForm,
)
from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user, get_admin_user, decode_token
from open_webui.constants import ERROR_MESSAGES

router = APIRouter()

# Simple in-memory rate limiting (resets on server restart)
# For production, consider using Redis or similar
rate_limit_store = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 5
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds


def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    current_time = time.time()
    
    # Clean old entries
    rate_limit_store[client_ip] = [
        timestamp for timestamp in rate_limit_store[client_ip]
        if current_time - timestamp < RATE_LIMIT_WINDOW
    ]
    
    # Check if limit exceeded
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    # Add current request
    rate_limit_store[client_ip].append(current_time)
    return True


############################
# Submit Ticket
############################


@router.post("/tickets/submit", response_model=TicketModel)
async def submit_ticket(
    request: Request,
    form_data: TicketForm,
):
    """
    Submit a new support ticket.
    Rate limited to 5 requests per hour per IP address.
    """
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )
    
    # Try to get user_id if user is authenticated (optional)
    user_id = None
    try:
        # Check if there's an authorization header
        auth_header = request.headers.get("authorization")
        if auth_header:
            token = auth_header.replace("Bearer ", "")
            data = decode_token(token)
            if data and "id" in data:
                user_id = data["id"]
    except Exception:
        # User not authenticated, that's fine
        pass
    
    # Create ticket
    ticket = Tickets.insert_new_ticket(form_data, user_id=user_id)
    
    if ticket:
        return ticket
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ticket",
        )


############################
# Get All Tickets (Admin Only)
############################


@router.get("/tickets", response_model=list[TicketModel])
async def get_tickets(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    user=Depends(get_admin_user),
):
    """
    Get all tickets. Admin only.
    Optionally filter by status: new, in_progress, resolved, closed
    """
    tickets = Tickets.get_all_tickets(status=status, skip=skip, limit=limit)
    return tickets


############################
# Get Ticket by ID (Admin Only)
############################


@router.get("/tickets/{ticket_id}", response_model=TicketModel)
async def get_ticket_by_id(
    ticket_id: str,
    user=Depends(get_admin_user),
):
    """Get a specific ticket by ID. Admin only."""
    ticket = Tickets.get_ticket_by_id(ticket_id)
    
    if ticket:
        return ticket
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )


############################
# Update Ticket (Admin Only)
############################


@router.patch("/tickets/{ticket_id}", response_model=TicketModel)
async def update_ticket(
    ticket_id: str,
    form_data: TicketUpdateForm,
    user=Depends(get_admin_user),
):
    """Update ticket status. Admin only."""
    ticket = Tickets.update_ticket_by_id(ticket_id, form_data)
    
    if ticket:
        return ticket
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )


############################
# Delete Ticket (Admin Only)
############################


@router.delete("/tickets/{ticket_id}")
async def delete_ticket(
    ticket_id: str,
    user=Depends(get_admin_user),
):
    """Delete a ticket. Admin only."""
    result = Tickets.delete_ticket_by_id(ticket_id)
    
    if result:
        return {"success": True, "message": "Ticket deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )


############################
# Get Ticket Statistics (Admin Only)
############################


class TicketStats(BaseModel):
    total: int
    new: int
    in_progress: int
    resolved: int
    closed: int


@router.get("/tickets/stats/summary", response_model=TicketStats)
async def get_ticket_stats(
    user=Depends(get_admin_user),
):
    """Get ticket statistics. Admin only."""
    return TicketStats(
        total=Tickets.get_ticket_count(),
        new=Tickets.get_ticket_count(status="new"),
        in_progress=Tickets.get_ticket_count(status="in_progress"),
        resolved=Tickets.get_ticket_count(status="resolved"),
        closed=Tickets.get_ticket_count(status="closed"),
    )
