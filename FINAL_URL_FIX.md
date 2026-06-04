# 404 Error Fix - Correct URL Format for TechZone

## Current Status

✅ **Good News:** 302 redirect error is GONE!  
❌ **New Issue:** 404 Not Found error

## What This Means

The 404 error confirms that your TechZone OpenPages instance **DOES** require the `/openpages` context path, but we need to format it correctly.

## The Problem

Your TechZone instance URL structure is:
```
http://na4.services.cloud.techzone.ibm.com:45439/openpages/opgrc/api/v2/...
         ^^^^^^^^^                           ^^^^^  ^^^^^^^^ ^^^^^
         hostname                            port   context  API path
```

## The Correct Solution

**Use this URL format:**
```
OPENPAGES_BASE_URL=http://na4.services.cloud.techzone.ibm.com:45439/openpages
```

**Key Points:**
1. ✅ Include `/openpages` (the context path)
2. ❌ Do NOT include trailing slash `/`
3. ✅ The client will add `/opgrc/api/v2/...`

## Apply the Fix

```bash
ibmcloud ce application update --name openpages-mcp-v2 \
  --env OPENPAGES_BASE_URL=http://na4.services.cloud.techzone.ibm.com:45439/openpages
```

**Note:** No trailing slash after `openpages`

## Why This Works

### URL Construction Flow

**With correct URL:**
1. Base URL: `http://na4.services.cloud.techzone.ibm.com:45439/openpages`
2. Client adds: `/opgrc/api/v2/query`
3. Final URL: `http://na4.services.cloud.techzone.ibm.com:45439/openpages/opgrc/api/v2/query` ✅

**What you had before (with trailing slash):**
1. Base URL: `http://na4.services.cloud.techzone.ibm.com:45439/openpages/`
2. Client adds: `/opgrc/api/v2/query`
3. Final URL: `http://na4.services.cloud.techzone.ibm.com:45439/openpages//opgrc/api/v2/query` ❌
   (Note the double slash `//` which causes issues)

**What you tried (without /openpages):**
1. Base URL: `http://na4.services.cloud.techzone.ibm.com:45439`
2. Client adds: `/opgrc/api/v2/query`
3. Final URL: `http://na4.services.cloud.techzone.ibm.com:45439/opgrc/api/v2/query` ❌
   (Missing the `/openpages` context path)

## Complete Environment Variables

Here's your complete, correct configuration:

```bash
# Apply all at once
ibmcloud ce application update --name openpages-mcp-v2 \
  --env SERVER_MODE=remote \
  --env PORT=8000 \
  --env HOST=0.0.0.0 \
  --env OPENPAGES_BASE_URL=http://na4.services.cloud.techzone.ibm.com:45439/openpages \
  --env OPENPAGES_AUTHENTICATION_TYPE=basic \
  --env OPENPAGES_USERNAME=OpenPagesAdministrator \
  --env OPENPAGES_PASSWORD=OpenPagesAdministrator \
  --env SSL_VERIFY=False \
  --env DEBUG=False \
  --env LOG_LEVEL=INFO
```

## Verify the Fix

### 1. Check Application Logs

```bash
ibmcloud ce application logs --name openpages-mcp-v2 --follow
```

Look for successful API calls without 404 errors.

### 2. Test Health Endpoint

```bash
curl https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud/health
```

Should return:
```json
{
  "status": "healthy",
  "checks": {
    "openpages_connection": "healthy"
  }
}
```

### 3. Test from Watsonx Orchestrate

Try a simple query:
- "List all issues"
- "Show me the first 5 controls"

## Understanding TechZone URL Patterns

TechZone OpenPages instances typically use this format:

```
http://<hostname>:<port>/openpages
```

**Examples:**
- `http://na4.services.cloud.techzone.ibm.com:45439/openpages`
- `http://useast.services.cloud.techzone.ibm.com:22816/openpages`

**Important:** 
- ✅ Include `/openpages` context path
- ❌ No trailing slash
- ✅ Let the client add API paths

## Summary

**The Issue:** Trailing slash in URL caused double slashes in API paths  
**The Fix:** Remove trailing slash, keep `/openpages` context path  
**Correct URL:** `http://na4.services.cloud.techzone.ibm.com:45439/openpages`

Apply the fix command above and the 404 errors will be resolved.