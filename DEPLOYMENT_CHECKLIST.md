# Deployment Checklist for Buckeye IT Ticket Assigner

## Files to Push to GitHub Repo (AI_TicketTriage)

### Core Function Files
- [ ] `__init__.py` - Main Azure Function code with keyword-based assignment logic
- [ ] `function.json` - Timer trigger configuration (runs every 3 minutes)
- [ ] `host.json` - Azure Function App configuration
- [ ] `requirements.txt` - Python dependencies

### Configuration Files
- [ ] `config.py` - Customized for your Buckeye IT team with all tech assignments and rules
- [ ] `local.settings.json` - Local development settings (will be ignored by git)

### Documentation & Scripts
- [ ] `README.md` - Updated documentation for your setup
- [ ] `deploy.ps1` - PowerShell deployment script
- [ ] `test_function.py` - Local testing script
- [ ] `.gitignore` - Git ignore rules
- [ ] `DEPLOYMENT_CHECKLIST.md` - This file

## Deployment Steps

### 1. Push to GitHub
```bash
# Navigate to your local repo
cd path/to/AI_TicketTriage

# Add all files
git add .

# Commit changes
git commit -m "Initial Azure Function for ConnectWise ticket assignment"

# Push to GitHub
git push origin main
```

### 2. Connect GitHub to Azure Function App
1. Go to Azure Portal
2. Navigate to your Function App: `buckeyeit-portal-automation`
3. Go to **Deployment Center**
4. Choose **GitHub** as source
5. Select your organization and `AI_TicketTriage` repo
6. Choose branch (usually `main`)
7. Complete the setup

### 3. Verify Deployment
1. Check **Deployment Center** for successful deployment
2. Go to **Functions** in your Function App
3. Verify the timer function is created and enabled
4. Check **Application Insights** for logs

### 4. Test the Function
1. Create a test ticket in ConnectWise with keywords like "firewall" or "password reset"
2. Wait for the function to run (every 3 minutes)
3. Check if the ticket gets assigned to the correct tech
4. Review logs in Application Insights

## Configuration Summary

### Tech Team (Already Configured)
- **John Hamilton**: Remote support, email, password resets
- **Jose Pizana**: Tier 3, firewall, VPN, network
- **Michael Smith**: Server, backup, domain controller
- **Jake Schaff**: Quote requests
- **Onsite Techs**: Jacon, Isaac, Matthew for hardware issues
- **Phil Gosche**: Spam guidance (mentioned in notes)

### Assignment Rules
- **Firewall/VPN/Network**: → Jose
- **Server/Backup**: → Michael
- **Quotes**: → Jake
- **Password/Email**: → John
- **Hardware/Onsite**: → Rotate among Jacon, Isaac, Matthew
- **Spam**: → Mention Phil in notes

### Schedule
- Runs every 3 minutes
- Scans for unassigned tickets
- Assigns based on keywords and workload balancing

## Troubleshooting

### Common Issues
1. **Function not running**: Check timer trigger in Azure Portal
2. **No assignments**: Verify ConnectWise API credentials
3. **Wrong assignments**: Check tech email addresses match ConnectWise
4. **API errors**: Review Application Insights logs

### Log Locations
- **Azure Portal**: Function App → Functions → ConnectWiseTicketAssigner → Monitor
- **Application Insights**: Live Metrics and Logs
- **Local Testing**: Run `python test_function.py`

## Next Steps After Deployment
1. Monitor the first few assignments
2. Adjust keywords in `config.py` if needed
3. Fine-tune workload limits
4. Set up alerts for failed assignments
5. Consider adding business hours logic

## Support
- Check Azure Function logs first
- Review ConnectWise API documentation
- Contact ConnectWise admin for API permissions
- Monitor Application Insights for detailed error information 