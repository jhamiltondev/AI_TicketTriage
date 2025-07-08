# ConnectWise Ticket Assigner - Azure Function Deployment Script
# This script helps deploy the function to Azure Function App

param(
    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "East US",
    
    [Parameter(Mandatory=$false)]
    [string]$StorageAccountName,
    
    [Parameter(Mandatory=$false)]
    [switch]$CreateFunctionApp,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild
)

Write-Host "🚀 ConnectWise Ticket Assigner - Deployment Script" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Check if Azure CLI is installed
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "✅ Azure CLI found: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI not found. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

# Check if user is logged in
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ Not logged in to Azure. Please run 'az login'" -ForegroundColor Red
    exit 1
}

# Generate storage account name if not provided
if (-not $StorageAccountName) {
    $StorageAccountName = "st" + $FunctionAppName.ToLower().Replace("-", "").Replace("_", "")
    Write-Host "📝 Generated storage account name: $StorageAccountName" -ForegroundColor Yellow
}

# Create Function App if requested
if ($CreateFunctionApp) {
    Write-Host "🔨 Creating Function App..." -ForegroundColor Yellow
    
    # Check if storage account exists, create if not
    $storageExists = az storage account show --name $StorageAccountName --resource-group $ResourceGroup --output json 2>$null
    if (-not $storageExists) {
        Write-Host "📦 Creating storage account..." -ForegroundColor Yellow
        az storage account create `
            --name $StorageAccountName `
            --resource-group $ResourceGroup `
            --location $Location `
            --sku Standard_LRS `
            --kind StorageV2
    }
    
    # Create Function App
    az functionapp create `
        --resource-group $ResourceGroup `
        --consumption-plan-location $Location `
        --runtime python `
        --runtime-version 3.9 `
        --functions-version 4 `
        --name $FunctionAppName `
        --storage-account $StorageAccountName `
        --os-type Linux
    
    Write-Host "✅ Function App created successfully" -ForegroundColor Green
}

# Install dependencies if not skipping build
if (-not $SkipBuild) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
    }
    
    # Activate virtual environment and install dependencies
    if ($IsWindows) {
        .\.venv\Scripts\Activate.ps1
    } else {
        source .venv/bin/activate
    }
    
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}

# Deploy the function
Write-Host "🚀 Deploying function to Azure..." -ForegroundColor Yellow

try {
    func azure functionapp publish $FunctionAppName
    Write-Host "✅ Function deployed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Configure application settings
Write-Host "⚙️  Configuring application settings..." -ForegroundColor Yellow

# Check if settings are already configured
$currentSettings = az functionapp config appsettings list --name $FunctionAppName --resource-group $ResourceGroup --output json | ConvertFrom-Json

$requiredSettings = @{
    "CONNECTWISE_SITE" = "https://api-na.myconnectwise.net"
    "CONNECTWISE_COMPANY_ID" = "buckeyeitser"
    "CONNECTWISE_PUBLIC_KEY" = "6btb8DTHkwheGf3d"
    "CONNECTWISE_PRIVATE_KEY" = "sKnSZdrNmU8zeFiQ"
    "CONNECTWISE_CLIENT_ID" = "173d3199-c79d-4219-88ba-96140f77942e"
}

$settingsToAdd = @()
foreach ($setting in $requiredSettings.GetEnumerator()) {
    $exists = $currentSettings | Where-Object { $_.name -eq $setting.Key }
    if (-not $exists) {
        $settingsToAdd += "$($setting.Key)=$($setting.Value)"
    }
}

if ($settingsToAdd.Count -gt 0) {
    az functionapp config appsettings set `
        --name $FunctionAppName `
        --resource-group $ResourceGroup `
        --settings $settingsToAdd
    
    Write-Host "✅ Application settings configured" -ForegroundColor Green
} else {
    Write-Host "ℹ️  Application settings already configured" -ForegroundColor Blue
}

# Get function URL
$functionUrl = az functionapp function show `
    --name $FunctionAppName `
    --resource-group $ResourceGroup `
    --function-name "ConnectWiseTicketAssigner" `
    --output json | ConvertFrom-Json

Write-Host ""
Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Function App: $FunctionAppName" -ForegroundColor Cyan
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Cyan
Write-Host "Function URL: $($functionUrl.invokeUrlTemplate)" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Update the TECH_ASSIGNMENT_RULES in the function code with your actual tech emails"
Write-Host "2. Configure VIP_TENANTS in config.py for VIP automation"
Write-Host "3. Test the main function using: python test_function.py"
Write-Host "4. Test the VIP automation using: python test_vip_automation.py"
Write-Host "5. Monitor the functions in Azure Portal"
Write-Host "6. Check Application Insights for logs and metrics"
Write-Host ""
Write-Host "🔗 Useful links:" -ForegroundColor Yellow
Write-Host "- Azure Portal: https://portal.azure.com"
Write-Host "- Function App: https://portal.azure.com/#@/resource/subscriptions/*/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$FunctionAppName"
Write-Host "" 