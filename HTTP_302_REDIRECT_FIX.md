# HTTP 302 Redirect Error - Fix Guide

## Problem Identified

You're getting an **HTTP 302 redirect error** when the MCP server tries to connect to OpenPages:

```
Error executing query: OpenPages API error (302)
```

This happens because:
1. The OpenPages URL is redirecting (302 = temporary redirect)
2. The httpx client is not following redirects by default
3. The URL format might need adjustment for TechZone

## Your Current Configuration

```
OPENPAGES_BASE_URL=http://useast.services.cloud.techzone.ibm.com:22816/openpages/
```

## Root Cause

The httpx AsyncClient in the OpenPages client is created **without** the `follow_redirects=True` parameter, which means it won't automatically follow HTTP 302 redirects.

## Solution

You need to update the Code Engine environment variable to use the correct URL format:

### Fix 1: Update OPENPAGES_BASE_URL (Recommended)

The URL should **NOT** include the trailing `/openpages/` path. The client adds the correct API paths automatically.

**Change from:**
```
http://useast.services.cloud.techzone.ibm.com:22816/openpages/
```

**Change to:**
```
http://useast.services.cloud.techzone.ibm.com:22816
```

### Fix 2: Try HTTPS (If Available)

Some TechZone environments support HTTPS:

```
https://useast.services.cloud.techzone.ibm.com:22816
```

---

## Step-by-Step Fix

### Option 1: Using IBM Cloud Console

1. Go to Code Engine → Your Project → `openpages-mcp-v2`
2. Click "Environment variables" tab
3. Find `OPENPAGES_BASE_URL`
4. Click "Edit" (pencil icon)
5. Change value to: `http://useast.services.cloud.techzone.ibm.com:22816`
6. Remove the trailing `/openpages/`
7. Click "Save" or "Deploy"

### Option 2: Using IBM Cloud CLI

```bash
# Update the OPENPAGES_BASE_URL
ibmcloud ce application update --name openpages-mcp-v2 \
  --env OPENPAGES_BASE_URL=http://useast.services.cloud.techzone.ibm.com:22816
```

---

## Why This Happens

### URL Path Construction

The OpenPages client automatically constructs the correct API paths:

1. **Your current URL:** `http://...com:22816/openpages/`
2. **Client adds:** `/opgrc/api/v2/query`
3. **Result:** `http://...com:22816/openpages/opgrc/api/v2/query` ❌ (Wrong - double path)

**With corrected URL:**
1. **Base URL:** `http://...com:22816`
2. **Client adds:** `/opgrc/api/v2/query`
3. **Result:** `http://...com:22816/opgrc/api/v2/query` ✅ (Correct)

### Code Reference

In `src/app/core/openpages_client.py`, the `_get_api_path()` method adds `/opgrc` prefix:

```python
def _get_api_path(self, endpoint: str) -> str:
    if self.is_cp4d:
        return f"-opgrc{endpoint}"
    else:
        return f"/opgrc{endpoint}"  # Adds /opgrc prefix
```

---

## Alternative Fix: Code Change (If URL Must Stay)

If you **cannot** change the URL, we can modify the code to handle redirects:

### File: `src/app/core/openpages_client.py`

Find line ~391 where the httpx client is created:

**Current code:**
```python
self._http_client = httpx.AsyncClient(
    verify=self.settings.SSL_VERIFY,
    limits=pool_limits,
)
```

**Change to:**
```python
self._http_client = httpx.AsyncClient(
    verify=self.settings.SSL_VERIFY,
    limits=pool_limits,
    follow_redirects=True,  # Add this line
)
```

Then rebuild and redeploy the container.

---

## Verify the Fix

### 1. Check Application Logs

```bash
ibmcloud ce application logs --name openpages-mcp-v2 --follow
```

Look for successful API calls instead of 302 errors.

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

Try a simple query like:
- "List all issues"
- "Show me recent controls"

---

## Additional Troubleshooting

### If Still Getting 302 Errors

1. **Verify the URL is accessible:**
   ```bash
   curl -v http://useast.services.cloud.techzone.ibm.com:22816/opgrc/api/v2/metadata/object_types \
     -u "OpenPagesAdministrator:OpenPagesAdministrator"
   ```

2. **Check for redirects:**
   ```bash
   curl -I http://useast.services.cloud.techzone.ibm.com:22816/opgrc/api/v2/metadata/object_types \
     -u "OpenPagesAdministrator:OpenPagesAdministrator"
   ```

3. **Try with /openpages prefix explicitly:**
   ```bash
   curl -v http://useast.services.cloud.techzone.ibm.com:22816/openpages/opgrc/api/v2/metadata/object_types \
     -u "OpenPagesAdministrator:OpenPagesAdministrator"
   ```

### Common TechZone URL Patterns

TechZone OpenPages instances typically use one of these formats:

**Pattern 1 (Most Common):**
```
http://hostname:port
```
Example: `http://useast.services.cloud.techzone.ibm.com:22816`

**Pattern 2 (With /openpages context):**
```
http://hostname:port/openpages
```
Example: `http://useast.services.cloud.techzone.ibm.com:22816/openpages`

**Pattern 3 (HTTPS):**
```
https://hostname:port
```

---

## Quick Reference

### Current Environment Variables

```bash
OPENPAGES_BASE_URL=http://useast.services.cloud.techzone.ibm.com:22816/openpages/  # ❌ Wrong
OPENPAGES_AUTHENTICATION_TYPE=basic
OPENPAGES_USERNAME=OpenPagesAdministrator
OPENPAGES_PASSWORD=OpenPagesAdministrator
SSL_VERIFY=False
```

### Corrected Environment Variables

```bash
OPENPAGES_BASE_URL=http://useast.services.cloud.techzone.ibm.com:22816  # ✅ Correct
OPENPAGES_AUTHENTICATION_TYPE=basic
OPENPAGES_USERNAME=OpenPagesAdministrator
OPENPAGES_PASSWORD=OpenPagesAdministrator
SSL_VERIFY=False
```

---

## Summary

**The Fix:**
1. Remove `/openpages/` from the end of `OPENPAGES_BASE_URL`
2. Use: `http://useast.services.cloud.techzone.ibm.com:22816`
3. The client will automatically add the correct API paths

**Why:**
- The client adds `/opgrc/api/v2/...` paths automatically
- Having `/openpages/` in the base URL creates incorrect paths
- This causes the server to redirect (302) to the correct path
- But the httpx client doesn't follow redirects by default

**Result:**
- API calls will work correctly
- No more 302 redirect errors
- Watsonx Orchestrate can successfully execute queries