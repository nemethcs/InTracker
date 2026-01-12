# Azure CI/CD Pipeline Setup Guide

Ez a dokumentum leírja, hogyan kell beállítani az Azure CI/CD pipeline-t az InTracker projekthez.

## Áttekintés

A CI/CD pipeline automatikusan buildeli és deployolja az alkalmazást Azure Container Apps-re, amikor release tag-et hozunk létre a main branch-en.

## Előfeltételek

1. **Azure Subscription** - Aktív Azure előfizetés
2. **Azure Container Registry (ACR)** - Docker image-ek tárolásához
3. **Azure Container Apps** - Backend és Frontend alkalmazások futtatásához
4. **GitHub Repository** - A projekt GitHub-on
5. **GitHub Secrets** - Azure credentials és konfiguráció

## 1. Azure erőforrások létrehozása

### Azure Container Registry (ACR)

```bash
# ACR létrehozása
az acr create \
  --resource-group <RESOURCE_GROUP> \
  --name <ACR_NAME> \
  --sku Basic \
  --admin-enabled true

# ACR bejelentkezési adatok lekérése
az acr credential show --name <ACR_NAME>
```

### Azure Container Apps

```bash
# Container Apps Environment létrehozása (ha még nincs)
az containerapp env create \
  --name <ENVIRONMENT_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --location <LOCATION>

# Backend Container App létrehozása
az containerapp create \
  --name <BACKEND_APP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --environment <ENVIRONMENT_NAME> \
  --image <ACR_NAME>.azurecr.io/intracker-backend:latest \
  --target-port 3000 \
  --ingress external \
  --registry-server <ACR_NAME>.azurecr.io \
  --registry-username <ACR_USERNAME> \
  --registry-password <ACR_PASSWORD> \
  --env-vars \
    DATABASE_URL=<DATABASE_URL> \
    REDIS_URL=<REDIS_URL> \
    JWT_SECRET=<JWT_SECRET> \
    JWT_REFRESH_SECRET=<JWT_REFRESH_SECRET> \
    GITHUB_TOKEN=<GITHUB_TOKEN> \
    MCP_API_KEY=<MCP_API_KEY> \
    CORS_ORIGIN=<CORS_ORIGIN>

# Frontend Container App létrehozása
az containerapp create \
  --name <FRONTEND_APP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --environment <ENVIRONMENT_NAME> \
  --image <ACR_NAME>.azurecr.io/intracker-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --registry-server <ACR_NAME>.azurecr.io \
  --registry-username <ACR_USERNAME> \
  --registry-password <ACR_PASSWORD> \
  --env-vars \
    VITE_API_BASE_URL=<API_URL> \
    VITE_SIGNALR_URL=<SIGNALR_URL> \
    VITE_APP_NAME=InTracker
```

## 2. GitHub Secrets beállítása

A GitHub repository Settings → Secrets and variables → Actions menüben add hozzá a következő secrets-eket:

### Azure Credentials

1. **AZURE_CREDENTIALS** - Service Principal credentials (JSON)
   ```bash
   # Service Principal létrehozása
   az ad sp create-for-rbac --name "InTracker-CICD" --role contributor \
     --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP> \
     --sdk-auth
   ```
   A kimenet JSON formátumú, ezt add hozzá AZURE_CREDENTIALS néven.

### Azure Configuration

2. **AZURE_RESOURCE_GROUP** - Azure resource group neve
3. **ACR_NAME** - Azure Container Registry neve (pl. `intrackeracr`)
4. **ACR_USERNAME** - ACR admin username (általában az ACR neve)
5. **ACR_PASSWORD** - ACR admin password (`az acr credential show --name <ACR_NAME>`)

### Container Apps Configuration

6. **CONTAINER_APP_NAME_BACKEND** - Backend Container App neve
7. **CONTAINER_APP_NAME_FRONTEND** - Frontend Container App neve
8. **CONTAINER_APP_ENVIRONMENT** - Container Apps Environment neve

### Frontend Build Arguments

9. **VITE_API_BASE_URL** - Backend API URL (pl. `https://backend.azurecontainerapps.io`)
10. **VITE_SIGNALR_URL** - SignalR Hub URL (pl. `https://backend.azurecontainerapps.io/signalr/hub`)

## 3. Release folyamat

### Release tag létrehozása

```bash
# 1. Merge develop → main
git checkout main
git merge develop
git push origin main

# 2. Release tag létrehozása
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Automatikus deployment

Amikor push-olsz egy `v*` tag-et a main branch-re, a GitHub Actions automatikusan:
1. Buildeli a Backend és Frontend Docker image-eket (linux/amd64 platformra)
2. Push-olja az image-eket az Azure Container Registry-be
3. Frissíti a Container Apps-eket az új image-ekkel

## 4. Versioning stratégia

Használjunk **Semantic Versioning** (SemVer) formátumot:
- **v1.0.0** - Major release (breaking changes)
- **v1.1.0** - Minor release (new features, backward compatible)
- **v1.1.1** - Patch release (bug fixes)

## 5. Rollback folyamat

Ha szükséges a rollback:

```bash
# Előző verzióra visszaállítás
az containerapp update \
  --name <BACKEND_APP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --image <ACR_NAME>.azurecr.io/intracker-backend:<PREVIOUS_VERSION>

az containerapp update \
  --name <FRONTEND_APP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --image <ACR_NAME>.azurecr.io/intracker-frontend:<PREVIOUS_VERSION>
```

## 6. Monitoring és alerting

### Container Apps Logs

```bash
# Backend logs
az containerapp logs show \
  --name <BACKEND_APP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --follow

# Frontend logs
az containerapp logs show \
  --name <FRONTEND_APP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --follow
```

### Health Checks

A Container Apps automatikusan monitorozza a health check endpoint-eket:
- Backend: `GET /health` vagy `GET /api/health`
- Frontend: `GET /` (200 OK response)

## 7. Troubleshooting

### Build hiba

- Ellenőrizd a GitHub Actions logokat
- Győződj meg róla, hogy minden secret helyesen van beállítva
- Ellenőrizd, hogy az ACR elérhető-e

### Deployment hiba

- Ellenőrizd az Azure Container Apps logokat
- Győződj meg róla, hogy az image-ek léteznek az ACR-ben
- Ellenőrizd az environment variables-t

### Image pull hiba

- Ellenőrizd az ACR credentials-eket
- Győződj meg róla, hogy a Container Apps hozzáfér az ACR-hez

## 8. Best Practices

1. **Mindig teszteld a pipeline-t** egy test release tag-gel (pl. `v0.1.0-test`)
2. **Használj semantic versioning-et** a verziószámozáshoz
3. **Dokumentáld a változásokat** a release tag message-ben
4. **Monitorozd a deployment-eket** az Azure Portal-on
5. **Készíts backup-et** az environment variables-ről

## 9. További információk

- [Azure Container Apps dokumentáció](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Azure Container Registry dokumentáció](https://docs.microsoft.com/en-us/azure/container-registry/)
- [GitHub Actions dokumentáció](https://docs.github.com/en/actions)
