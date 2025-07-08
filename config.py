"""
Configuration file for ConnectWise Ticket Assigner
Customized for Buckeye IT team structure and assignment rules.
"""

# Tech team configuration
TECH_TEAM = {
    "jhamilton@buckeyeit.com": {
        "name": "John Hamilton",
        "specialties": ["remote_support", "email_accounts", "password_resets", "general_remote"],
        "workload_limit": 15,
        "available": True
    },
    "jboos@buckeyeit.com": {
        "name": "Jacon Boos", 
        "specialties": ["onsite_support", "hardware"],
        "workload_limit": 10,
        "available": True
    },
    "ibaker@buckeyeit.com": {
        "name": "Isaac Baker",
        "specialties": ["onsite_support", "hardware"],
        "workload_limit": 10,
        "available": True
    },
    "mperry@buckeyeit.com": {
        "name": "Matthew Perry",
        "specialties": ["onsite_support", "hardware"],
        "workload_limit": 10,
        "available": True
    },
    "jpizana@buckeyeit.com": {
        "name": "Jose Pizana",
        "specialties": ["tier3", "firewall", "vpn", "network", "fortigate", "audit"],
        "workload_limit": 8,
        "available": True
    },
    "msmith@buckeyeit.com": {
        "name": "Michael Smith",
        "specialties": ["server", "backup", "domain_controller"],
        "workload_limit": 8,
        "available": True
    },
    "jschaaf@buckeyeit.com": {
        "name": "Jake Schaff",
        "specialties": ["quotes"],
        "workload_limit": 5,
        "available": True
    },
    "pgosche@buckeyeit.com": {
        "name": "Phil Gosche",
        "specialties": ["spam", "blocked_email"],
        "workload_limit": 3,
        "available": False  # Does not handle tickets directly
    }
}

# Assignment rules by keywords and ticket types
ASSIGNMENT_RULES = {
    # Tier 3 / Network / Firewall issues
    "tier3_keywords": ["firewall", "vpn", "network outage", "audit", "fortigate", "network configuration"],
    "tier3_tech": "jpizana@buckeyeit.com",
    
    # Server and backup issues
    "server_keywords": ["server", "backup", "domain controller", "server maintenance", "backup failure"],
    "server_tech": "msmith@buckeyeit.com",
    
    # Quote requests
    "quote_keywords": ["quote", "quotation", "pricing", "cost estimate", "proposal"],
    "quote_tech": "jschaaf@buckeyeit.com",
    
    # Remote support issues
    "remote_keywords": ["password reset", "new email", "email creation", "account setup", "remote support", "remote access"],
    "remote_tech": "jhamilton@buckeyeit.com",
    
    # Onsite hardware issues
    "onsite_keywords": ["monitor", "printer", "hardware", "physical", "onsite", "on-site", "computer won't turn on", "broken", "damaged"],
    "onsite_techs": ["jboos@buckeyeit.com", "ibaker@buckeyeit.com", "mperry@buckeyeit.com"],
    
    # Spam/email issues (mention Phil but don't assign)
    "spam_keywords": ["spam", "blocked email", "email blocked", "junk mail", "phishing"],
    "spam_mention": "pgosche@buckeyeit.com"
}

# Tech assignment rules by ConnectWise board
TECH_ASSIGNMENT_RULES = {
    "Help Desk (MS)": {
        # Default techs for general tickets (Priority 3-4)
        "default_techs": [
            "jhamilton@buckeyeit.com",  # John for general remote issues
            "jboos@buckeyeit.com",      # Jacon for onsite
            "ibaker@buckeyeit.com",     # Isaac for onsite
            "mperry@buckeyeit.com"      # Matthew for onsite
        ],
        # Priority-specific tech assignments
        "priority_techs": {
            "Priority 1 - Critical": [
                "jpizana@buckeyeit.com",  # Jose for critical network issues
                "msmith@buckeyeit.com"    # Michael for critical server issues
            ],
            "Priority 2 - High": [
                "jpizana@buckeyeit.com",  # Jose for high priority network
                "msmith@buckeyeit.com",   # Michael for high priority server
                "jhamilton@buckeyeit.com" # John for high priority remote
            ]
        }
    },
    "Implementation (MS)": {
        # Default techs for implementation projects
        "default_techs": [
            "jpizana@buckeyeit.com",  # Jose for network implementations
            "msmith@buckeyeit.com",   # Michael for server implementations
            "jhamilton@buckeyeit.com" # John for remote implementations
        ],
        # Priority-specific tech assignments for implementation
        "priority_techs": {
            "Priority 1 - Critical": [
                "jpizana@buckeyeit.com",
                "msmith@buckeyeit.com"
            ]
        }
    },
    "Project (MS)": {
        "default_techs": [
            "jpizana@buckeyeit.com",
            "msmith@buckeyeit.com",
            "jhamilton@buckeyeit.com"
        ],
        "priority_techs": {}
    }
}

# Ticket statuses that should be considered for assignment
UNASSIGNED_TICKET_STATUSES = [
    "Needs Worked",
    "New",
    "Pending"
]

# Ticket statuses that count toward tech workload
WORKLOAD_STATUSES = [
    "Needs Worked",
    "Working Issue Now"
]

# Maximum tickets per tech (safety limit)
MAX_TICKETS_PER_TECH = 15

# Timeout settings for API calls (in seconds)
API_TIMEOUT = 30

# Logging configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Assignment note template
ASSIGNMENT_NOTE_TEMPLATE = "Ticket automatically assigned to {tech_name} by Azure Function at {timestamp}"

# Business hours (for future enhancements)
BUSINESS_HOURS = {
    "start": "08:00",
    "end": "17:00",
    "timezone": "America/New_York",
    "weekdays": [0, 1, 2, 3, 4]  # Monday to Friday
}

# Holiday handling (for future enhancements)
HOLIDAYS = [
    "2024-01-01",  # New Year's Day
    "2024-01-15",  # Martin Luther King Jr. Day
    "2024-02-19",  # Presidents' Day
    "2024-05-27",  # Memorial Day
    "2024-07-04",  # Independence Day
    "2024-09-02",  # Labor Day
    "2024-10-14",  # Columbus Day
    "2024-11-11",  # Veterans Day
    "2024-11-28",  # Thanksgiving Day
    "2024-12-25",  # Christmas Day
]

# Escalation rules (for future enhancements)
ESCALATION_RULES = {
    "max_wait_time_hours": 4,  # Escalate tickets waiting more than 4 hours
    "escalation_techs": [
        "jpizana@buckeyeit.com",  # Jose for technical escalation
        "pgosche@buckeyeit.com"   # Phil for management escalation
    ]
}

# Notification settings (for future enhancements)
NOTIFICATIONS = {
    "email_notifications": False,
    "teams_webhook_url": None,
    "slack_webhook_url": None
}

# VIP Automation Configuration
VIP_TENANTS = [
    "vip_client_1",
    "vip_client_2", 
    "premium_client",
    "enterprise_client"
]

VIP_AUTOMATION_RULES = {
    "password_reset": {
        "keywords": [
            "password reset", "forgot password", "locked out", "password expired",
            "can't login", "login issue", "account locked", "reset password"
        ],
        "auto_resolve": True,
        "priority_threshold": "Priority 3 - Medium",
        "require_confirmation": False
    },
    "account_creation": {
        "keywords": [
            "new user", "create account", "new employee", "account setup",
            "user creation", "new hire", "employee onboarding", "setup account"
        ],
        "auto_resolve": False,
        "priority_threshold": "Priority 2 - High",
        "require_confirmation": True
    },
    "account_disable": {
        "keywords": [
            "disable account", "terminate user", "remove access", "account deactivation",
            "user termination", "revoke access", "disable user", "employee termination"
        ],
        "auto_resolve": False,
        "priority_threshold": "Priority 2 - High",
        "require_confirmation": True
    },
    "email_forwarding": {
        "keywords": [
            "email forwarding", "forward emails", "email redirect", "mail forwarding",
            "set up forwarding", "email alias"
        ],
        "auto_resolve": True,
        "priority_threshold": "Priority 3 - Medium",
        "require_confirmation": False
    },
    "shared_mailbox": {
        "keywords": [
            "shared mailbox", "shared email", "group mailbox", "department email",
            "team mailbox", "shared inbox"
        ],
        "auto_resolve": False,
        "priority_threshold": "Priority 2 - High",
        "require_confirmation": True
    }
}

# Password Policy for VIP Automation
PASSWORD_POLICY = {
    "length": 12,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special": True,
    "exclude_chars": "lI1O0",
    "expiration_days": 90,
    "history_count": 5
}

# Account Creation Templates
ACCOUNT_CREATION_TEMPLATES = {
    "default": {
        "groups": ["Domain Users"],
        "home_directory": "\\\\server\\users\\{username}",
        "profile_path": "\\\\server\\profiles\\{username}",
        "mailbox_size_limit": "2GB",
        "password_expires": True
    },
    "executive": {
        "groups": ["Domain Users", "Executives"],
        "home_directory": "\\\\server\\executives\\{username}",
        "profile_path": "\\\\server\\profiles\\executives\\{username}",
        "mailbox_size_limit": "5GB",
        "password_expires": True
    },
    "department_head": {
        "groups": ["Domain Users", "Department Heads"],
        "home_directory": "\\\\server\\dept_heads\\{username}",
        "profile_path": "\\\\server\\profiles\\dept_heads\\{username}",
        "mailbox_size_limit": "3GB",
        "password_expires": True
    }
}

# VIP Automation Security Settings
VIP_AUTOMATION_SECURITY = {
    "max_daily_automations": 50,
    "require_approval_for_sensitive_actions": True,
    "sensitive_actions": ["account_disable", "account_creation"],
    "audit_log_enabled": True,
    "notification_on_sensitive_actions": True
} 