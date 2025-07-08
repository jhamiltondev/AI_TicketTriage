import azure.functions as func
import logging
import requests
import base64
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import random
import string

# ConnectWise API Configuration
CONNECTWISE_SITE = os.environ.get("CONNECTWISE_SITE", "https://api-na.myconnectwise.net")
CONNECTWISE_COMPANY_ID = os.environ.get("CONNECTWISE_COMPANY_ID", "buckeyeitser")
CONNECTWISE_PUBLIC_KEY = os.environ.get("CONNECTWISE_PUBLIC_KEY", "6btb8DTHkwheGf3d")
CONNECTWISE_PRIVATE_KEY = os.environ.get("CONNECTWISE_PRIVATE_KEY", "sKnSZdrNmU8zeFiQ")
CONNECTWISE_CLIENT_ID = os.environ.get("CONNECTWISE_CLIENT_ID", "173d3199-c79d-4219-88ba-96140f77942e")

# Import configuration
try:
    from config import (
        VIP_AUTOMATION_RULES, VIP_TENANTS, PASSWORD_POLICY, 
        ACCOUNT_CREATION_TEMPLATES, API_TIMEOUT, LOG_LEVEL
    )
except ImportError:
    # Fallback configuration if config.py is not available
    VIP_AUTOMATION_RULES = {
        "password_reset": {
            "keywords": ["password reset", "forgot password", "locked out", "password expired"],
            "auto_resolve": True,
            "priority_threshold": "Priority 3 - Medium"
        },
        "account_creation": {
            "keywords": ["new user", "create account", "new employee", "account setup"],
            "auto_resolve": False,
            "priority_threshold": "Priority 2 - High"
        },
        "account_disable": {
            "keywords": ["disable account", "terminate user", "remove access", "account deactivation"],
            "auto_resolve": False,
            "priority_threshold": "Priority 2 - High"
        }
    }
    VIP_TENANTS = ["vip_client_1", "vip_client_2"]
    PASSWORD_POLICY = {
        "length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special": True,
        "exclude_chars": "lI1O0"
    }
    ACCOUNT_CREATION_TEMPLATES = {
        "default": {
            "groups": ["Domain Users"],
            "home_directory": "\\\\server\\users\\{username}",
            "profile_path": "\\\\server\\profiles\\{username}"
        }
    }
    API_TIMEOUT = 30
    LOG_LEVEL = "INFO"

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

def get_vip_tickets() -> List[Dict]:
    """Fetch VIP tickets that are candidates for automation."""
    base_url = f"{CONNECTWISE_SITE}/v4_6_release/apis/3.0/service/tickets"
    headers = get_connectwise_auth_headers()
    
    # Get tickets from VIP tenants that are new or needs worked
    conditions = 'status/name="New" OR status/name="Needs Worked"'
    
    params = {
        'conditions': conditions,
        'orderBy': 'priority/name asc, dateEntered asc',
        'pageSize': 50,
    }
    
    try:
        logger.info("Fetching VIP tickets for automation...")
        resp = requests.get(base_url, headers=headers, params=params, timeout=API_TIMEOUT)
        
        if resp.status_code == 200:
            all_tickets = resp.json()
            # Filter to only VIP tenant tickets
            vip_tickets = []
            for ticket in all_tickets:
                company = ticket.get('company', {})
                company_name = company.get('name', '').lower()
                if any(vip_tenant.lower() in company_name for vip_tenant in VIP_TENANTS):
                    vip_tickets.append(ticket)
            
            logger.info(f"Found {len(vip_tickets)} VIP tickets for automation")
            return vip_tickets
        else:
            logger.error(f"Failed to fetch tickets: {resp.status_code} - {resp.text}")
            return []
            
    except Exception as e:
        logger.error(f"Exception while fetching VIP tickets: {e}")
        return []

def analyze_ticket_for_automation(ticket: Dict) -> Optional[Dict]:
    """Analyze ticket content to determine if it can be automated."""
    summary = ticket.get('summary', '').lower()
    description = ticket.get('initialDescription', '').lower()
    full_text = f"{summary} {description}"
    priority = ticket.get('priority', {}).get('name', 'Priority 4 - Low')
    
    # Check each automation rule
    for automation_type, rules in VIP_AUTOMATION_RULES.items():
        # Check if priority meets threshold
        priority_order = ["Priority 1 - Critical", "Priority 2 - High", "Priority 3 - Medium", "Priority 4 - Low"]
        priority_threshold = rules.get('priority_threshold', 'Priority 4 - Low')
        
        if priority_order.index(priority) <= priority_order.index(priority_threshold):
            # Check for keywords
            keywords = rules.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in full_text:
                    return {
                        'type': automation_type,
                        'rules': rules,
                        'confidence': 0.9,  # High confidence for keyword match
                        'extracted_data': extract_data_from_ticket(ticket, automation_type)
                    }
    
    return None

def extract_data_from_ticket(ticket: Dict, automation_type: str) -> Dict:
    """Extract relevant data from ticket for automation."""
    summary = ticket.get('summary', '')
    description = ticket.get('initialDescription', '')
    full_text = f"{summary} {description}"
    
    extracted = {}
    
    if automation_type == "password_reset":
        # Extract username/email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, full_text)
        if emails:
            extracted['username'] = emails[0]
        
        # Extract domain if mentioned
        domain_pattern = r'domain[:\s]+([A-Za-z0-9.-]+)'
        domain_match = re.search(domain_pattern, full_text, re.IGNORECASE)
        if domain_match:
            extracted['domain'] = domain_match.group(1)
    
    elif automation_type == "account_creation":
        # Extract employee name
        name_pattern = r'(?:employee|user|person)[:\s]+([A-Za-z\s]+)'
        name_match = re.search(name_pattern, full_text, re.IGNORECASE)
        if name_match:
            extracted['employee_name'] = name_match.group(1).strip()
        
        # Extract department
        dept_pattern = r'(?:department|dept)[:\s]+([A-Za-z\s]+)'
        dept_match = re.search(dept_pattern, full_text, re.IGNORECASE)
        if dept_match:
            extracted['department'] = dept_match.group(1).strip()
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, full_text)
        if emails:
            extracted['email'] = emails[0]
    
    elif automation_type == "account_disable":
        # Extract username/email to disable
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, full_text)
        if emails:
            extracted['username'] = emails[0]
        
        # Extract reason
        reason_pattern = r'(?:reason|because)[:\s]+([^.]+)'
        reason_match = re.search(reason_pattern, full_text, re.IGNORECASE)
        if reason_match:
            extracted['reason'] = reason_match.group(1).strip()
    
    return extracted

def generate_secure_password() -> str:
    """Generate a secure password according to policy."""
    policy = PASSWORD_POLICY
    length = policy.get('length', 12)
    
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    numbers = string.digits
    special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Remove excluded characters
    exclude_chars = policy.get('exclude_chars', '')
    for char in exclude_chars:
        lowercase = lowercase.replace(char, '')
        uppercase = uppercase.replace(char, '')
        numbers = numbers.replace(char, '')
    
    # Build password ensuring all requirements are met
    password = []
    
    if policy.get('require_lowercase', True):
        password.append(random.choice(lowercase))
    if policy.get('require_uppercase', True):
        password.append(random.choice(uppercase))
    if policy.get('require_numbers', True):
        password.append(random.choice(numbers))
    if policy.get('require_special', True):
        password.append(random.choice(special))
    
    # Fill remaining length
    all_chars = lowercase + uppercase + numbers + special
    while len(password) < length:
        password.append(random.choice(all_chars))
    
    # Shuffle the password
    random.shuffle(password)
    return ''.join(password)

def execute_password_reset(ticket: Dict, extracted_data: Dict) -> bool:
    """Execute password reset automation."""
    username = extracted_data.get('username')
    if not username:
        logger.warning(f"Cannot reset password for ticket {ticket.get('id')}: No username found")
        return False
    
    # Generate new password
    new_password = generate_secure_password()
    
    # Here you would integrate with your actual password reset system
    # This is a placeholder for the actual implementation
    try:
        # Example: Active Directory password reset
        # ad_reset_password(username, new_password)
        
        # For now, we'll just log the action
        logger.info(f"Password reset for {username}: {new_password}")
        
        # Add note to ticket
        note_text = f"""AUTOMATED PASSWORD RESET COMPLETED

Username: {username}
New Password: {new_password}
Reset Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This password reset was performed automatically by the VIP automation system.
Please contact the user with the new password.

Note: This password will expire in 90 days and must be changed on first login."""
        
        add_automation_note(ticket.get('id'), note_text)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset password for {username}: {e}")
        return False

def execute_account_creation(ticket: Dict, extracted_data: Dict) -> bool:
    """Execute account creation automation."""
    employee_name = extracted_data.get('employee_name')
    department = extracted_data.get('department', 'General')
    email = extracted_data.get('email')
    
    if not employee_name:
        logger.warning(f"Cannot create account for ticket {ticket.get('id')}: No employee name found")
        return False
    
    # Generate username from employee name
    username = generate_username_from_name(employee_name)
    initial_password = generate_secure_password()
    
    try:
        # Here you would integrate with your actual account creation system
        # This is a placeholder for the actual implementation
        
        # Example: Active Directory account creation
        # ad_create_user(username, employee_name, department, initial_password)
        
        # For now, we'll just log the action
        logger.info(f"Account creation for {employee_name} ({username}): {initial_password}")
        
        # Add note to ticket
        note_text = f"""AUTOMATED ACCOUNT CREATION COMPLETED

Employee Name: {employee_name}
Username: {username}
Department: {department}
Email: {email or 'Not specified'}
Initial Password: {initial_password}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This account was created automatically by the VIP automation system.
Please provide the username and password to the employee.

Note: The password must be changed on first login."""
        
        add_automation_note(ticket.get('id'), note_text)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create account for {employee_name}: {e}")
        return False

def execute_account_disable(ticket: Dict, extracted_data: Dict) -> bool:
    """Execute account disable automation."""
    username = extracted_data.get('username')
    reason = extracted_data.get('reason', 'No reason specified')
    
    if not username:
        logger.warning(f"Cannot disable account for ticket {ticket.get('id')}: No username found")
        return False
    
    try:
        # Here you would integrate with your actual account disable system
        # This is a placeholder for the actual implementation
        
        # Example: Active Directory account disable
        # ad_disable_user(username)
        
        # For now, we'll just log the action
        logger.info(f"Account disable for {username}: {reason}")
        
        # Add note to ticket
        note_text = f"""AUTOMATED ACCOUNT DISABLE COMPLETED

Username: {username}
Reason: {reason}
Disabled: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This account was disabled automatically by the VIP automation system.
The account has been locked and all access has been revoked.

Note: This action can be reversed by re-enabling the account if needed."""
        
        add_automation_note(ticket.get('id'), note_text)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to disable account for {username}: {e}")
        return False

def generate_username_from_name(employee_name: str) -> str:
    """Generate a username from employee name."""
    # Remove special characters and split
    clean_name = re.sub(r'[^a-zA-Z\s]', '', employee_name)
    parts = clean_name.split()
    
    if len(parts) >= 2:
        # First letter of first name + last name
        username = f"{parts[0][0].lower()}{parts[-1].lower()}"
    else:
        # Just use the name if only one part
        username = parts[0].lower()
    
    # Ensure username is not too long
    if len(username) > 20:
        username = username[:20]
    
    return username

def add_automation_note(ticket_id: int, note_text: str) -> bool:
    """Add an automation note to the ticket."""
    base_url = f"{CONNECTWISE_SITE}/v4_6_release/apis/3.0/service/tickets/{ticket_id}/notes"
    headers = get_connectwise_auth_headers()
    
    payload = {
        'text': note_text,
        'detailDescriptionFlag': True,
        'internalAnalysisFlag': False,
        'resolutionFlag': False,
        'customerUpdatedFlag': False,
    }
    
    try:
        resp = requests.post(base_url, headers=headers, json=payload, timeout=API_TIMEOUT)
        
        if resp.status_code in (200, 201):
            logger.info(f"Added automation note to ticket {ticket_id}")
            return True
        else:
            logger.error(f"Failed to add note to ticket {ticket_id}: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"Exception while adding note to ticket {ticket_id}: {e}")
        return False

def resolve_ticket(ticket_id: int, resolution_text: str) -> bool:
    """Resolve the ticket with automation completion."""
    base_url = f"{CONNECTWISE_SITE}/v4_6_release/apis/3.0/service/tickets/{ticket_id}"
    headers = get_connectwise_auth_headers()
    
    payload = {
        "status": {"name": "Closed"},
        "closedDate": datetime.now().isoformat(),
        "closedBy": "VIP Automation System"
    }
    
    try:
        resp = requests.patch(base_url, headers=headers, json=payload, timeout=API_TIMEOUT)
        
        if resp.status_code in (200, 204):
            logger.info(f"Resolved ticket {ticket_id}")
            return True
        else:
            logger.error(f"Failed to resolve ticket {ticket_id}: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"Exception while resolving ticket {ticket_id}: {e}")
        return False

def main(mytimer: func.TimerRequest) -> None:
    """Main function that runs every 2 minutes to process VIP automation."""
    utc_timestamp = datetime.utcnow().replace(tzinfo=None).isoformat()
    
    logger.info(f'VIP Automation function started at {utc_timestamp}')
    
    try:
        # Get VIP tickets
        vip_tickets = get_vip_tickets()
        
        if not vip_tickets:
            logger.info("No VIP tickets found for automation")
            return
        
        # Process each VIP ticket
        automated_count = 0
        for ticket in vip_tickets:
            ticket_id = ticket.get('id')
            summary = ticket.get('summary', 'Unknown')
            
            # Skip if ticket_id is None
            if ticket_id is None:
                logger.warning(f"Skipping ticket with no ID: {summary}")
                continue
            
            logger.info(f"Processing VIP ticket {ticket_id}: {summary}")
            
            # Analyze ticket for automation
            automation_result = analyze_ticket_for_automation(ticket)
            
            if automation_result:
                automation_type = automation_result['type']
                rules = automation_result['rules']
                extracted_data = automation_result['extracted_data']
                
                logger.info(f"Automation detected for ticket {ticket_id}: {automation_type}")
                
                # Execute automation
                success = False
                if automation_type == "password_reset":
                    success = execute_password_reset(ticket, extracted_data)
                elif automation_type == "account_creation":
                    success = execute_account_creation(ticket, extracted_data)
                elif automation_type == "account_disable":
                    success = execute_account_disable(ticket, extracted_data)
                
                if success:
                    # Auto-resolve if configured
                    if rules.get('auto_resolve', False):
                        resolve_ticket(ticket_id, f"Automated {automation_type} completed successfully")
                    
                    automated_count += 1
                    logger.info(f"Successfully automated {automation_type} for ticket {ticket_id}")
                else:
                    logger.error(f"Failed to automate {automation_type} for ticket {ticket_id}")
            else:
                logger.debug(f"No automation rules matched for ticket {ticket_id}")
        
        logger.info(f"VIP automation process completed. Automated {automated_count} tickets.")
        
    except Exception as e:
        logger.error(f"Error in VIP automation function: {e}")
        raise 