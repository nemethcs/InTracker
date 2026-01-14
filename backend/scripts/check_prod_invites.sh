#!/bin/bash
# Script to check team leader invitations in production
# Usage: ./check_prod_invites.sh <resource-group> <container-app-name>

set -e

RESOURCE_GROUP=${1:-"intracker-rg-poland"}
CONTAINER_APP_NAME=${2:-"intracker-backend"}

echo "🔍 Checking team leader invitations in production..."
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Container App: $CONTAINER_APP_NAME"
echo ""

# Get DATABASE_URL from Azure Container App environment variables
echo "📥 Fetching DATABASE_URL from Azure Container App..."
DATABASE_URL=$(az containerapp show \
  --name "$CONTAINER_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.template.containers[0].env[?name=='DATABASE_URL'].value" \
  --output tsv)

if [ -z "$DATABASE_URL" ]; then
  echo "❌ ERROR: Could not retrieve DATABASE_URL from Azure Container App"
  echo "   Please check the resource group and container app name"
  exit 1
fi

echo "✅ DATABASE_URL retrieved"
echo ""

# Run the Python script with the DATABASE_URL
echo "🔍 Running invitation check script..."
export DATABASE_URL
cd "$(dirname "$0")/.."
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate 2>/dev/null || . venv/bin/activate
pip install -q sqlalchemy psycopg2-binary 2>/dev/null || pip install -q sqlalchemy psycopg2-binary
python3 scripts/check_team_leader_invites.py
