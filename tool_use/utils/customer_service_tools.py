"""
Customer Service Tools for Claude
Implements tool functions for processing support tickets
"""

import json
from typing import Literal

from anthropic import beta_tool

from .customer_service_api import (
    KNOWLEDGE_BASE,
    TEAM_ROUTING,
    Ticket,
    TicketCategory,
    TicketGenerator,
    TicketPriority,
    TicketStatus,
)

# Global state for demo purposes - in production this would be a database
_ticket_queue: list[Ticket] = []
_current_tickets: dict[str, Ticket] = {}
_queue_index = 0


def initialize_ticket_queue(count: int = 25):
    """Initialize the ticket queue with generated tickets"""
    global _ticket_queue, _queue_index, _current_tickets
    _ticket_queue = TicketGenerator.generate_batch(count)
    _queue_index = 0
    _current_tickets = {}


def _get_ticket(ticket_id: str) -> Ticket | None:
    """Helper to retrieve a ticket by ID"""
    return _current_tickets.get(ticket_id)


def _serialize_ticket(ticket: Ticket) -> str:
    """Convert ticket to JSON string"""
    return json.dumps(
        {
            "id": ticket.id,
            "customer_name": ticket.customer_name,
            "customer_email": ticket.customer_email,
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category.value if ticket.category else None,
            "priority": ticket.priority.value if ticket.priority else None,
            "status": ticket.status.value,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "assigned_team": ticket.assigned_team,
            "notes": ticket.notes,
        },
        indent=2,
    )


@beta_tool
def get_next_ticket() -> str:
    """
    Get the next unprocessed ticket from the queue.
    Returns ticket details as JSON string.
    """
    global _queue_index

    if _queue_index >= len(_ticket_queue):
        return json.dumps(
            {
                "error": "No more tickets in queue",
                "processed": _queue_index,
                "total": len(_ticket_queue),
            }
        )

    ticket = _ticket_queue[_queue_index]
    _queue_index += 1
    _current_tickets[ticket.id] = ticket

    return _serialize_ticket(ticket)


@beta_tool
def classify_ticket(
    ticket_id: str, category: Literal["billing", "technical", "account", "product", "shipping"]
) -> str:
    """
    Classify a ticket into a category.

    Args:
        ticket_id: The ticket ID
        category: The category to assign

    Returns:
        Confirmation message
    """
    ticket = _get_ticket(ticket_id)
    if not ticket:
        return json.dumps({"error": f"Ticket {ticket_id} not found"})

    ticket.category = TicketCategory(category)

    return json.dumps(
        {
            "success": True,
            "message": f"Ticket {ticket_id} classified as {category}",
            "ticket_id": ticket_id,
        }
    )


@beta_tool
def search_knowledge_base(category: str, query: str) -> str:
    """
    Search the knowledge base for relevant information.

    Args:
        category: The category to search (billing, technical, account)
        query: Keywords to search for

    Returns:
        Relevant knowledge base articles as JSON
    """
    category_lower = category.lower()

    if category_lower not in KNOWLEDGE_BASE:
        return json.dumps(
            {
                "error": f"Category '{category}' not found",
                "available_categories": list(KNOWLEDGE_BASE.keys()),
            }
        )

    category_kb = KNOWLEDGE_BASE[category_lower]

    # Simple keyword search
    query_lower = query.lower()
    results = {}

    for key, value in category_kb.items():
        if isinstance(value, dict):
            # Search nested dictionaries
            for sub_key, sub_value in value.items():
                if query_lower in sub_key.lower() or query_lower in str(sub_value).lower():
                    if key not in results:
                        results[key] = {}
                    results[key][sub_key] = sub_value
        else:
            # Search flat key-value pairs
            if query_lower in key.lower() or query_lower in value.lower():
                results[key] = value

    return json.dumps(
        {
            "category": category,
            "query": query,
            "results": results if results else category_kb,
            "all_available": category_kb,
        },
        indent=2,
    )


@beta_tool
def set_priority(ticket_id: str, priority: Literal["low", "medium", "high", "urgent"]) -> str:
    """
    Set the priority level for a ticket.

    Args:
        ticket_id: The ticket ID
        priority: Priority level

    Returns:
        Confirmation message
    """
    ticket = _get_ticket(ticket_id)
    if not ticket:
        return json.dumps({"error": f"Ticket {ticket_id} not found"})

    old_priority = ticket.priority.value if ticket.priority else "unset"
    ticket.priority = TicketPriority(priority)

    return json.dumps(
        {
            "success": True,
            "message": f"Ticket {ticket_id} priority updated from {old_priority} to {priority}",
            "ticket_id": ticket_id,
            "old_priority": old_priority,
            "new_priority": priority,
        }
    )


@beta_tool
def route_to_team(ticket_id: str, team: str) -> str:
    """
    Route a ticket to the appropriate support team.

    Args:
        ticket_id: The ticket ID
        team: Team name (billing-team, tech-support, account-services, product-success, logistics-team)

    Returns:
        Confirmation message
    """
    ticket = _get_ticket(ticket_id)
    if not ticket:
        return json.dumps({"error": f"Ticket {ticket_id} not found"})

    valid_teams = list(TEAM_ROUTING.values())
    if team not in valid_teams:
        return json.dumps(
            {
                "error": f"Invalid team '{team}'",
                "valid_teams": valid_teams,
            }
        )

    old_team = ticket.assigned_team
    ticket.assigned_team = team
    ticket.status = TicketStatus.OPEN

    return json.dumps(
        {
            "success": True,
            "message": f"Ticket {ticket_id} routed to {team}",
            "ticket_id": ticket_id,
            "old_team": old_team,
            "new_team": team,
        }
    )


@beta_tool
def draft_response(ticket_id: str, response: str) -> str:
    """
    Draft a response to the customer.

    Args:
        ticket_id: The ticket ID
        response: The draft response text

    Returns:
        Confirmation that draft was saved
    """
    ticket = _get_ticket(ticket_id)
    if not ticket:
        return json.dumps({"error": f"Ticket {ticket_id} not found"})

    # Store draft in notes with special prefix
    draft_note = f"[DRAFT RESPONSE] {response}"
    ticket.notes.append(draft_note)

    return json.dumps(
        {
            "success": True,
            "message": f"Draft response saved for ticket {ticket_id}",
            "ticket_id": ticket_id,
            "draft_length": len(response),
        }
    )


@beta_tool
def add_note(ticket_id: str, note: str) -> str:
    """
    Add an internal note to the ticket.

    Args:
        ticket_id: The ticket ID
        note: Internal note for team reference

    Returns:
        Confirmation message
    """
    ticket = _get_ticket(ticket_id)
    if not ticket:
        return json.dumps({"error": f"Ticket {ticket_id} not found"})

    ticket.notes.append(note)

    return json.dumps(
        {
            "success": True,
            "message": f"Note added to ticket {ticket_id}",
            "ticket_id": ticket_id,
            "total_notes": len(ticket.notes),
        }
    )


@beta_tool
def mark_complete(ticket_id: str) -> str:
    """
    Mark ticket as processed and ready for team review.

    Args:
        ticket_id: The ticket ID

    Returns:
        Confirmation and summary of ticket processing
    """
    ticket = _get_ticket(ticket_id)
    if not ticket:
        return json.dumps({"error": f"Ticket {ticket_id} not found"})

    # Validate ticket is ready for completion
    if not ticket.category:
        return json.dumps({"error": "Cannot complete ticket without category classification"})

    if not ticket.priority:
        return json.dumps({"error": "Cannot complete ticket without priority assignment"})

    if not ticket.assigned_team:
        return json.dumps({"error": "Cannot complete ticket without team routing"})

    ticket.status = TicketStatus.RESOLVED

    summary = {
        "success": True,
        "message": f"Ticket {ticket_id} marked complete",
        "ticket_id": ticket_id,
        "summary": {
            "customer": ticket.customer_name,
            "subject": ticket.subject,
            "category": ticket.category.value,
            "priority": ticket.priority.value,
            "assigned_team": ticket.assigned_team,
            "total_notes": len(ticket.notes),
            "status": ticket.status.value,
        },
    }

    return json.dumps(summary, indent=2)


# Helper function for demo/testing
def get_all_tools():
    """Return all tool functions for registration with Anthropic API"""
    return [
        get_next_ticket,
        classify_ticket,
        search_knowledge_base,
        set_priority,
        route_to_team,
        draft_response,
        add_note,
        mark_complete,
    ]
