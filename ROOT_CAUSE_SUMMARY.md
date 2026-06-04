# Root Cause Summary: HTTP 302 Redirect Error

## The Problem

```
Error executing query: OpenPages API error (302)
```

## Root Cause Analysis

### Issue 1: Missing Critical Environment Variables ⚠️

Your Code Engine deployment is missing **3 required variables** that prevent the server from starting properly:

```bash
SERVER_MODE=remote    # ❌ MISSING
PORT=8000            # ❌ MISSING  
HOST=0.0.0.0         # ❌ MISSING
```

**Impact:** Without these, the MCP server cannot initialize and listen for connections.

---

### Issue 2: Incorrect OpenPages URL Format 🔴

**Your Current URL:**
```
OPENPAGES_BASE_URL=http://useast.services.cloud.techzone.ibm.com:22816/openpages/
                                                                      ^^^^^^^^^^^
                                                                      PROBLEM: Extra path
```

**Why This Causes 302 Redirects:**

1. The OpenPages client **automatically adds** `/opgrc/api/v2/...` to all API calls
2. With `/openpages/` in your base URL, requests become:
   ```
   http://...com:22816/openpages/opgrc/api/v2/query
                       ^^^^^^^^^ ^^^^^ 
                       Wrong!    Correct path
   ```

3. The OpenPages server sees the wrong path and **redirects (HTTP 302)** to:
   ```
   http://...com:22816/opgrc/api/v2/query
   ```

4. But the httpx client is configured **without** `follow_redirects=True`, so it:
   - ❌ Doesn't follow the redirect
   - ❌ Returns the 302 error to your application
   - ❌ Query fails

---

## The Fix (2 Steps)

### Step 1: Add Missing Environment Variables

```bash
ibmcloud ce application update --name openpages-mcp-v2 \
  --env SERVER_MODE=remote \
  --env PORT=8000 \
  --env HOST=0.0.0.0
```

### Step 2: Fix the OpenPages URL

**Remove `/openpages/` from the end:**

```bash
ibmcloud ce application update --name openpages-mcp-v2 \
  --env OPENPAGES_BASE_URL=http://useast.services.cloud.techzone.ibm.com:22816
```

**Before:** `http://useast.services.cloud.techzone.ibm.com:22816/openpages/` ❌  
**After:** `http://useast.services.cloud.techzone.ibm.com:22816` ✅

---

## Why This Works

### Correct URL Construction

With the fixed base URL:

1. **Base URL:** `http://...com:22816`
2. **Client adds:** `/opgrc/api/v2/query`
3. **Final URL:** `http://...com:22816/opgrc/api/v2/query` ✅

**Result:**
- ✅ No redirect needed
- ✅ Direct API call succeeds
- ✅ Queries work correctly

---

## Technical Details

### Code Reference

In `src/app/core/openpages_client.py`, line ~232:

```python
def _get_api_path(self, endpoint: str) -> str:
    """Get the correct API path based on deployment type"""
    if self.is_cp4d:
        return f"-opgrc{endpoint}"
    else:
        return f"/opgrc{endpoint}"  # Adds /opgrc prefix automatically
```

The client **always** adds `/opgrc` prefix, so your base URL should **never** include it.

### HTTP 302 Redirect Flow

```
Your Request:
  http://...com:22816/openpages/opgrc/api/v2/query
                      ↓
Server Response: 302 Redirect
  Location: http://...com:22816/opgrc/api/v2/query
                      ↓
httpx Client: ❌ Does not follow (follow_redirects=False by default)
                      ↓
Error: "OpenPages API error (302)"
```

---

## Summary

**Two problems, two fixes:**

1. **Missing variables** → Add `SERVER_MODE`, `PORT`, `HOST`
2. **Wrong URL format** → Remove `/openpages/` from base URL

**Apply both fixes, restart the application, and the 302 errors will be resolved.**

---

## Quick Commands

```bash
# Apply both fixes at once
ibmcloud ce application update --name openpages-mcp-v2 \
  --env SERVER_MODE=remote \
  --env PORT=8000 \
  --env HOST=0.0.0.0 \
  --env OPENPAGES_BASE_URL=http://useast.services.cloud.techzone.ibm.com:22816

# Verify application is running
ibmcloud ce application get --name openpages-mcp-v2

# Check logs
ibmcloud ce application logs --name openpages-mcp-v2 --follow

# Test health endpoint
curl https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud/health