# VIP Automation Function - Summary

## Overview
The VIP Automation Function is a new Azure Function that provides automated IT service delivery for VIP tenants. It runs alongside the existing ConnectWise Ticket Assigner function and handles common requests like password resets, account creation, and account management automatically.

## Key Features

### 🔐 Password Reset Automation
- **Triggers**: Keywords like "password reset", "forgot password", "locked out"
- **Action**: Generates secure passwords following policy requirements
- **Auto-resolve**: Yes (for Priority 3 and below)
- **Security**: High - requires no manual confirmation

### 👤 Account Creation Automation
- **Triggers**: Keywords like "new user", "create account", "new employee"
- **Action**: Creates user accounts with appropriate templates
- **Auto-resolve**: No (requires manual review)
- **Security**: High - requires manual confirmation

### 🚫 Account Disable Automation
- **Triggers**: Keywords like "disable account", "terminate user"
- **Action**: Disables user accounts with audit trail
- **Auto-resolve**: No (requires manual review)
- **Security**: High - requires manual confirmation

### 📧 Email Forwarding Automation
- **Triggers**: Keywords like "email forwarding", "forward emails"
- **Action**: Sets up email forwarding rules
- **Auto-resolve**: Yes
- **Security**: Medium

### 📬 Shared Mailbox Automation
- **Triggers**: Keywords like "shared mailbox", "group mailbox"
- **Action**: Creates shared mailboxes for departments
- **Auto-resolve**: No (requires manual review)
- **Security**: High - requires manual confirmation

## Configuration

### VIP Tenants
Configure which tenants are eligible for automation in `config.py`:

```python
VIP_TENANTS = [
    "vip_client_1",
    "vip_client_2", 
    "premium_client",
    "enterprise_client"
]
```

### Password Policy
```python
PASSWORD_POLICY = {
    "length": 12,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special": True,
    "exclude_chars": "lI1O0",
    "expiration_days": 90
}
```

### Account Templates
```python
ACCOUNT_CREATION_TEMPLATES = {
    "default": {
        "groups": ["Domain Users"],
        "home_directory": "\\\\server\\users\\{username}",
        "mailbox_size_limit": "2GB"
    },
    "executive": {
        "groups": ["Domain Users", "Executives"],
        "home_directory": "\\\\server\\executives\\{username}",
        "mailbox_size_limit": "5GB"
    }
}
```

## Security Features

### Approval Requirements
- Sensitive actions require manual confirmation
- Configurable approval thresholds
- Audit logging for all automated actions

### Rate Limiting
- Maximum daily automation limit (default: 50)
- Prevents abuse and ensures oversight

### Audit Trail
- All automated actions are logged
- Detailed notes added to tickets
- Timestamp and operator tracking

## Integration Points

### ConnectWise Integration
- Uses existing ConnectWise API authentication
- Fetches tickets from VIP tenants only
- Adds detailed notes to tickets
- Updates ticket status upon completion

### Active Directory Integration (Placeholder)
The function includes placeholder code for Active Directory integration:

```python
# Example: Active Directory password reset
# ad_reset_password(username, new_password)

# Example: Active Directory account creation  
# ad_create_user(username, employee_name, department, initial_password)

# Example: Active Directory account disable
# ad_disable_user(username)
```

## Deployment

### Function Structure
```
AI_TicketTriage/
├── __init__.py                    # Main ticket assignment function
├── vip_automation/
│   ├── __init__.py               # VIP automation function
│   ├── function.json             # Function configuration
│   └── README.md                 # Detailed documentation
├── config.py                     # Shared configuration
├── test_function.py              # Main function tests
├── test_vip_automation.py        # VIP automation tests
└── deploy.ps1                    # Deployment script
```

### Scheduling
- **Main Function**: Runs every 3 minutes (ticket assignment)
- **VIP Function**: Runs every 2 minutes (VIP automation)

### Environment Variables
Both functions use the same ConnectWise API credentials:
- `CONNECTWISE_SITE`
- `CONNECTWISE_COMPANY_ID`
- `CONNECTWISE_PUBLIC_KEY`
- `CONNECTWISE_PRIVATE_KEY`
- `CONNECTWISE_CLIENT_ID`

## Testing

### Test the VIP Automation
```bash
python test_vip_automation.py
```

### Test the Main Function
```bash
python test_function.py
```

## Monitoring

### Logging
- Detailed logging for all automation attempts
- Success/failure tracking
- Performance metrics

### Alerts
- Notifications for sensitive actions
- Error alerts for failed automations
- Daily summary reports

## Customization

### Adding New Automation Types
1. Add new rule to `VIP_AUTOMATION_RULES`
2. Create extraction function for the new type
3. Implement execution function
4. Update main processing loop

### Modifying Existing Rules
- Update keywords for better detection
- Adjust priority thresholds
- Change auto-resolve settings
- Modify confirmation requirements

## Best Practices

1. **Test Thoroughly**: Always test new automation rules in development
2. **Monitor Closely**: Watch for false positives and adjust keywords
3. **Review Regularly**: Periodically review automation logs and success rates
4. **Update Keywords**: Keep keyword lists current with common request patterns
5. **Security First**: Always require confirmation for sensitive actions

## Future Enhancements

- **Machine Learning**: Improve detection accuracy with ML models
- **Natural Language Processing**: Better understanding of ticket content
- **Multi-language Support**: Handle tickets in different languages
- **Advanced Templates**: More sophisticated account creation templates
- **Integration APIs**: Direct integration with other IT systems

## Troubleshooting

### Common Issues
- **No automations running**: Check VIP_TENANTS configuration
- **False positives**: Adjust keyword lists in automation rules
- **Failed executions**: Check Active Directory integration code
- **Missing data**: Verify ticket content extraction patterns

### Debug Mode
Enable debug logging by setting `LOG_LEVEL = "DEBUG"` in config.py 