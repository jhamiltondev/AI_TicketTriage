import azure.functions as func
import logging
import requests
import base64
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ConnectWise API Configuration
CONNECTWISE_SITE = os.environ.get("CONNECTWISE_SITE", "https://api-na.myconnectwise.net")
CONNECTWISE_COMPANY_ID = os.environ.get("CONNECTWISE_COMPANY_ID", "buckeyeitser")
CONNECTWISE_PUBLIC_KEY = os.environ.get("CONNECTWISE_PUBLIC_KEY", "6btb8DTHkwheGf3d")
CONNECTWISE_PRIVATE_KEY = os.environ.get("CONNECTWISE_PRIVATE_KEY", "sKnSZdrNmU8zeFiQ")
CONNECTWISE_CLIENT_ID = os.environ.get("CONNECTWISE_CLIENT_ID", "173d3199-c79d-4219-88ba-96140f77942e")

# Import configuration
try:
    from config import (
        TECH_ASSIGNMENT_RULES, UNASSIGNED_TICKET_STATUSES, WORKLOAD_STATUSES, 
        MAX_TICKETS_PER_TECH, API_TIMEOUT, LOG_LEVEL, ASSIGNMENT_NOTE_TEMPLATE,
        TECH_TEAM, ASSIGNMENT_RULES
    )
except ImportError:
    # Fallback configuration if config.py is not available
    TECH_ASSIGNMENT_RULES = {
        "Help Desk (MS)": {
            "default_techs": ["tech1@buckeyeit.com", "tech2@buckeyeit.com", "tech3@buckeyeit.com"],
            "priority_techs": {
                "Priority 1 - Critical": ["senior_tech@buckeyeit.com"],
                "Priority 2 - High": ["senior_tech@buckeyeit.com", "tech1@buckeyeit.com"]
            }
        },
        "Implementation (MS)": {
            "default_techs": ["implementation_tech@buckeyeit.com", "senior_tech@buckeyeit.com"],
            "priority_techs": {}
        }
    }
    UNASSIGNED_TICKET_STATUSES = ["Needs Worked", "New"]
    WORKLOAD_STATUSES = ["Needs Worked", "Working Issue Now"]
    MAX_TICKETS_PER_TECH = 10
    API_TIMEOUT = 30
    LOG_LEVEL = "INFO"
    ASSIGNMENT_NOTE_TEMPLATE = "Ticket automatically assigned to {tech_name} by Azure Function at {timestamp}"
    TECH_TEAM = {}
    ASSIGNMENT_RULES = {}

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

def get_connectwise_auth_headers():
    """Generate ConnectWise API authentication headers."""
    auth_string = f"{CONNECTWISE_COMPANY_ID}+{CONNECTWISE_PUBLIC_KEY}:{CONNECTWISE_PRIVATE_KEY}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()
    
    return {
        'Authorization': f'Basic {auth_b64}',
        'clientId': CONNECTWISE_CLIENT_ID,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

def get_unassigned_tickets() -> List[Dict]:
    """Fetch unassigned tickets from ConnectWise."""
    base_url = f"{CONNECTWISE_SITE}/v4_6_release/apis/3.0/service/tickets"
    headers = get_connectwise_auth_headers()
    
    # Conditions for unassigned tickets that need work
    status_conditions = ' OR '.join([f'status/name="{status}"' for status in UNASSIGNED_TICKET_STATUSES])
    conditions = f'(owner/id is null OR owner/id="") AND ({status_conditions})'
    
    params = {
        'conditions': conditions,
        'orderBy': 'priority/name asc, dateEntered asc',
        'pageSize': 50,
    }
    
    try:
        logger.info("Fetching unassigned tickets from ConnectWise...")
        resp = requests.get(base_url, headers=headers, params=params, timeout=API_TIMEOUT)
        
        if resp.status_code == 200:
            tickets = resp.json()
            logger.info(f"Found {len(tickets)} unassigned tickets")
            return tickets
        else:
            logger.error(f"Failed to fetch tickets: {resp.status_code} - {resp.text}")
            return []
            
    except Exception as e:
        logger.error(f"Exception while fetching tickets: {e}")
        return []

def get_available_techs() -> List[Dict]:
    """Fetch available techs from ConnectWise."""
    base_url = f"{CONNECTWISE_SITE}/v4_6_release/apis/3.0/system/members"
    headers = get_connectwise_auth_headers()
    
    # Get techs who are active and available
    conditions = 'inactiveFlag=false AND adminFlag=true'
    
    params = {
        'conditions': conditions,
        'pageSize': 100,
    }
    
    try:
        logger.info("Fetching available techs from ConnectWise...")
        resp = requests.get(base_url, headers=headers, params=params, timeout=API_TIMEOUT)
        
        if resp.status_code == 200:
            members = resp.json()
            logger.info(f"Found {len(members)} available techs")
            return members
        else:
            logger.error(f"Failed to fetch techs: {resp.status_code} - {resp.text}")
            return []
            
    except Exception as e:
        logger.error(f"Exception while fetching techs: {e}")
        return []

def get_tech_workload(tech_id: int) -> int:
    """Get the current workload (number of active tickets) for a tech."""
    base_url = f"{CONNECTWISE_SITE}/v4_6_release/apis/3.0/service/tickets"
    headers = get_connectwise_auth_headers()
    
    # Count active tickets assigned to this tech
    status_conditions = ' OR '.join([f'status/name="{status}"' for status in WORKLOAD_STATUSES])
    conditions = f'owner/id={tech_id} AND ({status_conditions})'
    
    params = {
        'conditions': conditions,
        'pageSize': 1,  # We only need the count
    }
    
    try:
        resp = requests.get(base_url, headers=headers, params=params, timeout=API_TIMEOUT)
        if resp.status_code == 200:
            # The response includes total count in headers or we can count the results
            return len(resp.json())
        else:
            logger.error(f"Failed to get workload for tech {tech_id}: {resp.status_code}")
            return 999  # Return high number to avoid assigning to this tech
    except Exception as e:
        logger.error(f"Exception getting workload for tech {tech_id}: {e}")
        return 999

def analyze_ticket_content(ticket: Dict) -> Dict:
    """Analyze ticket content to determine the best tech based on keywords and specialties."""
    summary = ticket.get('summary', '').lower()
    description = ticket.get('initialDescription', '').lower()
    full_text = f"{summary} {description}"
    
    # Check for specific keyword matches
    for keyword_type, keywords in ASSIGNMENT_RULES.items():
        if keyword_type.endswith('_keywords'):
            for keyword in keywords:
                if keyword.lower() in full_text:
                    if keyword_type == 'tier3_keywords':
                        return {"type": "specialty", "tech_email": ASSIGNMENT_RULES["tier3_tech"]}
                    elif keyword_type == 'server_keywords':
                        return {"type": "specialty", "tech_email": ASSIGNMENT_RULES["server_tech"]}
                    elif keyword_type == 'quote_keywords':
                        return {"type": "specialty", "tech_email": ASSIGNMENT_RULES["quote_tech"]}
                    elif keyword_type == 'remote_keywords':
                        return {"type": "specialty", "tech_email": ASSIGNMENT_RULES["remote_tech"]}
                    elif keyword_type == 'onsite_keywords':
                        return {"type": "onsite_rotation", "tech_emails": ASSIGNMENT_RULES["onsite_techs"]}
                    elif keyword_type == 'spam_keywords':
                        return {"type": "spam_mention", "tech_email": ASSIGNMENT_RULES["spam_mention"]}
    
    return {"type": "general", "tech_emails": []}

def select_best_tech(ticket: Dict, available_techs: List[Dict]) -> Optional[Dict]:
    """Select the best available tech for a ticket based on content analysis, workload and priority."""
    board_name = ticket.get('board', {}).get('name', 'Help Desk (MS)')
    priority_name = ticket.get('priority', {}).get('name', 'Priority 3 - Medium')
    
    # First, analyze ticket content for keyword-based assignment
    content_analysis = analyze_ticket_content(ticket)
    
    if content_analysis["type"] == "specialty":
        # Direct assignment based on keywords
        target_email = content_analysis["tech_email"]
        tech_obj = next((t for t in available_techs if t.get('emailAddress', '').lower() == target_email.lower()), None)
        if tech_obj and TECH_TEAM.get(target_email, {}).get('available', True):
            workload = get_tech_workload(tech_obj['id'])
            if workload < TECH_TEAM.get(target_email, {}).get('workload_limit', MAX_TICKETS_PER_TECH):
                logger.info(f"Assigning to specialty tech {target_email} based on keywords")
                return tech_obj
            else:
                logger.warning(f"Specialty tech {target_email} at capacity, falling back to general assignment")
    
    elif content_analysis["type"] == "onsite_rotation":
        # Rotate among onsite techs
        onsite_techs = content_analysis["tech_emails"]
        available_onsite_techs = []
        
        for tech_email in onsite_techs:
            tech_obj = next((t for t in available_techs if t.get('emailAddress', '').lower() == tech_email.lower()), None)
            if tech_obj and TECH_TEAM.get(tech_email, {}).get('available', True):
                workload = get_tech_workload(tech_obj['id'])
                if workload < TECH_TEAM.get(tech_email, {}).get('workload_limit', MAX_TICKETS_PER_TECH):
                    available_onsite_techs.append((tech_obj, workload))
        
        if available_onsite_techs:
            # Select the onsite tech with lowest workload
            best_onsite_tech = min(available_onsite_techs, key=lambda x: x[1])
            logger.info(f"Assigning to onsite tech {best_onsite_tech[0].get('emailAddress')} based on keywords")
            return best_onsite_tech[0]
    
    elif content_analysis["type"] == "spam_mention":
        # Don't assign to Phil, but mention him in notes
        logger.info(f"Spam-related ticket detected, will mention {content_analysis['tech_email']} in notes")
    
    # Fall back to general assignment rules
    rules = TECH_ASSIGNMENT_RULES.get(board_name, TECH_ASSIGNMENT_RULES["Help Desk (MS)"])
    
    # Check if there are priority-specific techs
    priority_techs = rules.get("priority_techs", {}).get(priority_name, [])
    
    # Get all available techs (priority + default)
    all_techs = priority_techs + rules.get("default_techs", [])
    
    # Filter to only include techs that exist in ConnectWise and are available
    available_tech_emails = [tech.get('emailAddress', '').lower() for tech in available_techs]
    valid_techs = []
    
    for tech_email in all_techs:
        if (tech_email.lower() in available_tech_emails and 
            TECH_TEAM.get(tech_email, {}).get('available', True)):
            valid_techs.append(tech_email)
    
    if not valid_techs:
        logger.warning(f"No valid techs found for board {board_name}")
        return None
    
    # Find tech with lowest workload
    best_tech = None
    lowest_workload = float('inf')
    
    for tech_email in valid_techs:
        # Find the tech object
        tech_obj = next((t for t in available_techs if t.get('emailAddress', '').lower() == tech_email.lower()), None)
        if tech_obj:
            workload = get_tech_workload(tech_obj['id'])
            workload_limit = TECH_TEAM.get(tech_email, {}).get('workload_limit', MAX_TICKETS_PER_TECH)
            
            if workload < workload_limit and workload < lowest_workload:
                lowest_workload = workload
                best_tech = tech_obj
    
    return best_tech

def assign_ticket_to_tech(ticket_id: int, tech_id: int) -> bool:
    """Assign a ticket to a specific tech in ConnectWise."""
    base_url = f"{CONNECTWISE_SITE}/v4_6_release/apis/3.0/service/tickets/{ticket_id}"
    headers = get_connectwise_auth_headers()
    
    payload = {
        "owner": {"id": tech_id}
    }
    
    try:
        logger.info(f"Assigning ticket {ticket_id} to tech {tech_id}")
        resp = requests.patch(base_url, headers=headers, json=payload, timeout=API_TIMEOUT)
        
        if resp.status_code in (200, 204):
            logger.info(f"Successfully assigned ticket {ticket_id} to tech {tech_id}")
            return True
        else:
            logger.error(f"Failed to assign ticket {ticket_id}: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"Exception while assigning ticket {ticket_id}: {e}")
        return False

def add_assignment_note(ticket_id: int, tech_name: str, ticket: Optional[Dict] = None) -> bool:
    """Add a note to the ticket indicating it was auto-assigned."""
    base_url = f"{CONNECTWISE_SITE}/v4_6_release/apis/3.0/service/tickets/{ticket_id}/notes"
    headers = get_connectwise_auth_headers()
    
    # Check if this is a spam-related ticket that should mention Phil
    note_text = f"Ticket automatically assigned to {tech_name} by Azure Function at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    if ticket:
        content_analysis = analyze_ticket_content(ticket)
        if content_analysis["type"] == "spam_mention":
            spam_tech_email = content_analysis["tech_email"]
            spam_tech_name = TECH_TEAM.get(spam_tech_email, {}).get('name', spam_tech_email)
            note_text += f"\n\nNote: This appears to be spam/email related. {spam_tech_name} may be able to provide additional guidance if needed."
    
    payload = {
        'text': note_text,
        'detailDescriptionFlag': True,
        'internalAnalysisFlag': True,
        'resolutionFlag': False,
        'customerUpdatedFlag': False,
    }
    
    try:
        resp = requests.post(base_url, headers=headers, json=payload, timeout=API_TIMEOUT)
        
        if resp.status_code in (200, 201):
            logger.info(f"Added assignment note to ticket {ticket_id}")
            return True
        else:
            logger.error(f"Failed to add note to ticket {ticket_id}: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"Exception while adding note to ticket {ticket_id}: {e}")
        return False

def main(mytimer: func.TimerRequest) -> None:
    """Main function that runs every 3 minutes to assign unassigned tickets."""
    utc_timestamp = datetime.utcnow().replace(
        tzinfo=None).isoformat()
    
    logger.info(f'ConnectWise Ticket Assigner function started at {utc_timestamp}')
    
    try:
        # Get unassigned tickets
        unassigned_tickets = get_unassigned_tickets()
        
        if not unassigned_tickets:
            logger.info("No unassigned tickets found")
            return
        
        # Get available techs
        available_techs = get_available_techs()
        
        if not available_techs:
            logger.error("No available techs found")
            return
        
        # Process each unassigned ticket
        assigned_count = 0
        for ticket in unassigned_tickets:
            ticket_id = ticket.get('id')
            summary = ticket.get('summary', 'Unknown')
            
            # Skip if ticket_id is None
            if ticket_id is None:
                logger.warning(f"Skipping ticket with no ID: {summary}")
                continue
            
            logger.info(f"Processing ticket {ticket_id}: {summary}")
            
            # Select best tech for this ticket
            best_tech = select_best_tech(ticket, available_techs)
            
            if best_tech:
                tech_id = best_tech['id']
                tech_name = best_tech.get('fullName', best_tech.get('emailAddress', 'Unknown'))
                
                # Assign ticket to tech
                if assign_ticket_to_tech(ticket_id, tech_id):
                    # Add assignment note
                    add_assignment_note(ticket_id, tech_name, ticket)
                    assigned_count += 1
                    logger.info(f"Successfully assigned ticket {ticket_id} to {tech_name}")
                else:
                    logger.error(f"Failed to assign ticket {ticket_id} to {tech_name}")
            else:
                logger.warning(f"No suitable tech found for ticket {ticket_id}")
        
        logger.info(f"Ticket assignment process completed. Assigned {assigned_count} tickets.")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise 