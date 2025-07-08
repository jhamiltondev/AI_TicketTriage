# VIP Automation Function

This Azure Function provides automated IT service delivery for VIP tenants, handling common requests like password resets, account creation, and account management automatically.

## Features

### 🔐 Password Reset Automation
- Automatically detects password reset requests
- Generates secure passwords following policy requirements
- Adds detailed notes to tickets with new password information
- Can auto-resolve tickets upon completion

### 👤 Account Creation Automation
- Detects new user/employee requests
- Extracts employee information from ticket content
- Generates usernames and initial passwords
- Supports different account templates (default, executive, department head)
- Requires manual confirmation for security

### 🚫 Account Disable Automation
- Handles user termination and account deactivation requests
- Extracts username and reason for disable
- Adds audit notes to tickets
- Requires manual confirmation for security

### 📧 Email Forwarding Automation
- Sets up email forwarding rules
- Handles email alias creation
- Auto-resolves upon completion

### 📬 Shared Mailbox Automation
- Creates shared mailboxes for departments/teams
- Sets up appropriate permissions
- Requires manual confirmation

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

### Automation Rules
Each automation type has configurable rules:

```python
VIP_AUTOMATION_RULES = {
    "password_reset": {
        "keywords": ["password reset", "forgot password", "locked out"],
        "auto_resolve": True,
        "priority_threshold": "Priority 3 - Medium",
        "require_confirmation": False
    }
}
```

### Password Policy
Configure password requirements:

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
Different account types with specific settings:

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
- Sensitive actions (account creation, disable) require manual confirmation
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
- Fetches tickets from VIP tenants
- Adds detailed notes to tickets
- Updates ticket status upon completion
- Uses existing ConnectWise API authentication

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

1. **Function Configuration**: The function runs every 2 minutes to check for VIP tickets
2. **Environment Variables**: Uses the same ConnectWise API credentials as the main function
3. **Dependencies**: Requires the same Python packages as the main function

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

## Troubleshooting

### Common Issues
- **No automations running**: Check VIP_TENANTS configuration
- **False positives**: Adjust keyword lists in automation rules
- **Failed executions**: Check Active Directory integration code
- **Missing data**: Verify ticket content extraction patterns

### Debug Mode
Enable debug logging by setting `LOG_LEVEL = "DEBUG"` in config.py

## Future Enhancements

- **Machine Learning**: Improve detection accuracy with ML models
- **Natural Language Processing**: Better understanding of ticket content
- **Multi-language Support**: Handle tickets in different languages
- **Advanced Templates**: More sophisticated account creation templates
- **Integration APIs**: Direct integration with other IT systems 