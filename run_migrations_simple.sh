#!/bin/bash
# Simple script to run migrations in Azure Container App
# Run this in Azure Cloud Shell or locally with Azure CLI

RESOURCE_GROUP="intracker-rg-poland"
CONTAINER_APP="intracker-api"
KEY_VAULT="intracker-kv"

# Get DATABASE_URL from Key Vault
DATABASE_URL=$(az keyvault secret show --vault-name "$KEY_VAULT" --name "database-url" --query "value" -o tsv)

# Run migrations using Azure Container App exec (if supported)
# Or use Azure Cloud Shell
echo "To run migrations, use Azure Cloud Shell and execute:"
echo ""
echo "1. Open Azure Cloud Shell: https://shell.azure.com"
echo "2. Clone the repository"
echo "3. Run: cd backend && export DATABASE_URL='$DATABASE_URL' && alembic upgrade head"
echo ""
echo "Or use the run_azure_migrations_cloud.sh script"
