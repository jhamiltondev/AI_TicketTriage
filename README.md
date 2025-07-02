# ConnectWise Ticket Assigner Azure Function

This Azure Function automatically scans the ConnectWise dispatch portal every 3 minutes and assigns unassigned tickets to available technicians based on workload balancing and priority rules.

## Features

- **Automated Ticket Assignment**: Scans for unassigned tickets every 3 minutes
- **Smart Workload Balancing**: Assigns tickets to techs with the lowest current workload
- **Priority-Based Assignment**: Critical and high-priority tickets can be assigned to specific senior techs
- **Board-Specific Rules**: Different assignment rules for different ConnectWise boards (Help Desk vs Implementation)
- **Audit Trail**: Adds notes to tickets when they are auto-assigned
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Prerequisites

- Azure Function App (Python runtime)
- ConnectWise API access with appropriate permissions
- Python 3.8 or higher

## Setup Instructions

### 1. Deploy to Azure Function App

1. **Create Function App** (if not already created):
   ```bash
   az functionapp create --resource-group <your-resource-group> \
                        --consumption-plan-location <location> \
                        --runtime python \
                        --runtime-version 3.9 \
                        --functions-version 4 \
                        --name <your-function-app-name> \
                        --storage-account <storage-account-name>
   ```

2. **Deploy the function**:
   ```bash
   func azure functionapp publish <your-function-app-name>
   ```

### 2. Configure Environment Variables

In your Azure Function App, set the following Application Settings:

- `CONNECTWISE_SITE`: Your ConnectWise API site URL (e.g., "https://api-na.myconnectwise.net")
- `CONNECTWISE_COMPANY_ID`: Your ConnectWise company ID
- `CONNECTWISE_PUBLIC_KEY`: Your ConnectWise public API key
- `CONNECTWISE_PRIVATE_KEY`: Your ConnectWise private API key
- `CONNECTWISE_CLIENT_ID`: Your ConnectWise client ID

### 3. Tech Assignment Rules (Already Configured)

The assignment rules have been customized for your Buckeye IT team:

- **John Hamilton** (jhamilton@buckeyeit.com): Remote support, email accounts, password resets
- **Jose Pizana** (jpizana@buckeyeit.com): Tier 3 support, firewalls, VPN, network issues
- **Michael Smith** (msmith@buckeyeit.com): Server and backup specialist
- **Jake Schaff** (jschaaf@buckeyeit.com): Quote requests
- **Onsite Techs** (Jacon, Isaac, Matthew): Hardware and physical issues
- **Phil Gosche** (pgosche@buckeyeit.com): Spam/email guidance (mentioned in notes, not assigned)

The system automatically assigns tickets based on keywords in the ticket description and summary.

### 4. Local Development

1. **Install Azure Functions Core Tools**:
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure local settings**:
   - Copy `local.settings.json.example` to `local.settings.json`
   - Update the ConnectWise credentials in `local.settings.json`

4. **Run locally**:
   ```bash
   func start
   ```

## How It Works

### 1. Ticket Discovery
The function queries ConnectWise for tickets that:
- Have no assigned owner (`owner/id is null`)
- Are in "Needs Worked" or "New" status
- Are ordered by priority (highest first) and creation date

### 2. Tech Selection
For each unassigned ticket, the function:
1. Determines the ConnectWise board (Help Desk vs Implementation)
2. Checks priority-specific tech assignments
3. Gets the current workload for each available tech
4. Selects the tech with the lowest workload

### 3. Assignment Process
1. Assigns the ticket to the selected tech
2. Adds an internal note documenting the auto-assignment
3. Logs the assignment for monitoring

## Configuration Options

### Schedule
The function runs every 3 minutes by default. To change this, modify the `schedule` in `function.json`:

```json
{
  "schedule": "0 */5 * * * *"  // Every 5 minutes
}
```

### Ticket Status Filtering
Modify the conditions in `get_unassigned_tickets()` to include/exclude specific statuses:

```python
conditions = '(owner/id is null OR owner/id="") AND (status/name="Needs Worked" OR status/name="New" OR status/name="Pending")'
```

### Workload Calculation
The workload calculation considers tickets in "Needs Worked" or "Working Issue Now" status. Modify `get_tech_workload()` to change this logic.

## Monitoring and Logging

### Azure Application Insights
The function is configured to send logs to Application Insights. Monitor:
- Function execution times
- Number of tickets processed
- Assignment success/failure rates
- API errors

### Custom Logging
The function logs:
- Number of unassigned tickets found
- Number of available techs
- Each ticket assignment attempt
- Success/failure of assignments
- Any API errors

## Troubleshooting

### Common Issues

1. **No tickets being assigned**:
   - Check ConnectWise API credentials
   - Verify tech email addresses match ConnectWise
   - Check if techs are marked as inactive in ConnectWise

2. **API errors**:
   - Verify API permissions
   - Check network connectivity
   - Review ConnectWise API rate limits

3. **Function not running**:
   - Check Function App status in Azure portal
   - Verify timer trigger configuration
   - Check Application Insights for errors

### Debug Mode
Enable debug logging by modifying the logging level in `__init__.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

- Store ConnectWise credentials in Azure Key Vault for production
- Use managed identities for Azure resources when possible
- Regularly rotate API keys
- Monitor function execution logs for suspicious activity

## Support

For issues or questions:
1. Check the Azure Function logs in Application Insights
2. Review ConnectWise API documentation
3. Contact your ConnectWise administrator for API permissions

## License

This project is licensed under the MIT License. 