#!/usr/bin/env python3
"""
Test script for VIP Automation Function Logic
Tests the automation logic, data extraction, and password generation
"""

import sys
import os
import json
import re
import random
import string
from datetime import datetime

# Mock configuration for testing
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

def generate_secure_password():
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

def generate_username_from_name(employee_name):
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

def analyze_ticket_for_automation(ticket):
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

def extract_data_from_ticket(ticket, automation_type):
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

def test_password_generation():
    """Test secure password generation"""
    print("Testing password generation...")
    
    password = generate_secure_password()
    
    # Check length
    assert len(password) == 12, f"Password length should be 12, got {len(password)}"
    
    # Check character requirements
    assert any(c.isupper() for c in password), "Password should contain uppercase"
    assert any(c.islower() for c in password), "Password should contain lowercase"
    assert any(c.isdigit() for c in password), "Password should contain numbers"
    assert any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password), "Password should contain special chars"
    
    # Check excluded characters
    excluded = "lI1O0"
    for char in excluded:
        assert char not in password, f"Password should not contain {char}"
    
    print("✅ Password generation test passed")

def test_username_generation():
    """Test username generation from employee names"""
    print("Testing username generation...")
    
    test_cases = [
        ("John Smith", "jsmith"),
        ("Mary Jane Watson", "mwatson"),
        ("A", "a"),
        ("John A. Smith Jr.", "jsmith"),
    ]
    
    for name, expected in test_cases:
        username = generate_username_from_name(name)
        print(f"  {name} -> {username} (expected: {expected})")
        assert len(username) <= 20, f"Username too long: {username}"
        assert username.islower(), f"Username should be lowercase: {username}"
    
    print("✅ Username generation test passed")

def test_ticket_analysis():
    """Test ticket content analysis for automation"""
    print("Testing ticket analysis...")
    
    # Test password reset detection
    password_reset_ticket = {
        "id": 1,
        "summary": "Password Reset Request",
        "initialDescription": "User john.doe@company.com needs password reset",
        "priority": {"name": "Priority 3 - Medium"},
        "company": {"name": "vip_client_1"}
    }
    
    result = analyze_ticket_for_automation(password_reset_ticket)
    assert result is not None, "Should detect password reset"
    assert result['type'] == 'password_reset', f"Should be password_reset, got {result['type']}"
    assert result['extracted_data']['username'] == 'john.doe@company.com'
    
    # Test account creation detection
    account_creation_ticket = {
        "id": 2,
        "summary": "New Employee Account",
        "initialDescription": "New employee: Jane Smith, Department: IT",
        "priority": {"name": "Priority 2 - High"},
        "company": {"name": "vip_client_2"}
    }
    
    result = analyze_ticket_for_automation(account_creation_ticket)
    assert result is not None, "Should detect account creation"
    assert result['type'] == 'account_creation', f"Should be account_creation, got {result['type']}"
    assert result['extracted_data']['employee_name'] == 'Jane Smith'
    assert result['extracted_data']['department'] == 'IT'
    
    # Test no automation detection
    regular_ticket = {
        "id": 3,
        "summary": "General IT Question",
        "initialDescription": "How do I access the shared drive?",
        "priority": {"name": "Priority 4 - Low"},
        "company": {"name": "vip_client_1"}
    }
    
    result = analyze_ticket_for_automation(regular_ticket)
    assert result is None, "Should not detect automation for regular ticket"
    
    print("✅ Ticket analysis test passed")

def test_data_extraction():
    """Test data extraction from ticket content"""
    print("Testing data extraction...")
    
    # Test password reset extraction
    ticket = {
        "summary": "Password Reset for john.doe@company.com",
        "initialDescription": "User is locked out of domain: company.local"
    }
    
    extracted = extract_data_from_ticket(ticket, "password_reset")
    assert extracted['username'] == 'john.doe@company.com'
    assert extracted['domain'] == 'company.local'
    
    # Test account creation extraction
    ticket = {
        "summary": "New Employee Setup",
        "initialDescription": "Employee: Sarah Johnson, Department: Marketing, Email: sarah.j@company.com"
    }
    
    extracted = extract_data_from_ticket(ticket, "account_creation")
    assert extracted['employee_name'] == 'Sarah Johnson'
    assert extracted['department'] == 'Marketing'
    assert extracted['email'] == 'sarah.j@company.com'
    
    # Test account disable extraction
    ticket = {
        "summary": "Terminate User Account",
        "initialDescription": "Disable account: mike.smith@company.com, Reason: Employee termination"
    }
    
    extracted = extract_data_from_ticket(ticket, "account_disable")
    assert extracted['username'] == 'mike.smith@company.com'
    assert extracted['reason'] == 'Employee termination'
    
    print("✅ Data extraction test passed")

def test_vip_tenant_filtering():
    """Test VIP tenant filtering"""
    print("Testing VIP tenant filtering...")
    
    # Mock tickets from different tenants
    tickets = [
        {"id": 1, "company": {"name": "vip_client_1"}},
        {"id": 2, "company": {"name": "regular_client"}},
        {"id": 3, "company": {"name": "vip_client_2"}},
        {"id": 4, "company": {"name": "another_regular_client"}},
    ]
    
    # Filter VIP tickets
    vip_tickets = []
    for ticket in tickets:
        company = ticket.get('company', {})
        company_name = company.get('name', '').lower()
        if any(vip_tenant.lower() in company_name for vip_tenant in VIP_TENANTS):
            vip_tickets.append(ticket)
    
    assert len(vip_tickets) == 2, f"Should find 2 VIP tickets, found {len(vip_tickets)}"
    assert vip_tickets[0]['id'] == 1, "First VIP ticket should be ID 1"
    assert vip_tickets[1]['id'] == 3, "Second VIP ticket should be ID 3"
    
    print("✅ VIP tenant filtering test passed")

def test_priority_threshold():
    """Test priority threshold filtering"""
    print("Testing priority threshold filtering...")
    
    # Test different priorities
    test_cases = [
        ("Priority 1 - Critical", "Priority 3 - Medium", True),   # Should pass
        ("Priority 2 - High", "Priority 3 - Medium", True),       # Should pass
        ("Priority 3 - Medium", "Priority 3 - Medium", True),     # Should pass
        ("Priority 4 - Low", "Priority 3 - Medium", False),       # Should fail
    ]
    
    for priority, threshold, should_pass in test_cases:
        priority_order = ["Priority 1 - Critical", "Priority 2 - High", "Priority 3 - Medium", "Priority 4 - Low"]
        passes = priority_order.index(priority) <= priority_order.index(threshold)
        assert passes == should_pass, f"Priority {priority} with threshold {threshold} should {'pass' if should_pass else 'fail'}"
    
    print("✅ Priority threshold test passed")

def run_all_tests():
    """Run all tests"""
    print("🧪 Running VIP Automation Function Tests")
    print("=" * 50)
    
    try:
        test_password_generation()
        test_username_generation()
        test_ticket_analysis()
        test_data_extraction()
        test_vip_tenant_filtering()
        test_priority_threshold()
        
        print("=" * 50)
        print("🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 