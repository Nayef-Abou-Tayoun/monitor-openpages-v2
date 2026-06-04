# Direct API Test for OpenPages Connection

## Current Issue

Your `OPENPAGES_BASE_URL` is missing the `/openpages` context path:

**Current (Wrong):**
```
http://na4.services.cloud.techzone.ibm.com:45439
```

**Should Be:**
```
http://na4.services.cloud.techzone.ibm.com:45439/openpages
```

## Fix First

```bash
ibmcloud ce application update --name openpages-mcp-v2 \
  --env OPENPAGES_BASE_URL=http://na4.services.cloud.techzone.ibm.com:45439/openpages
```

Wait 30-60 seconds for the app to restart.

## Then Test with These Commands

### 1. Verify Health Check Shows Correct URL

```bash
curl -s https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud/health | jq '.checks.openpages_config'
```

**Expected Output:**
```json
{
  "status": "healthy",
  "message": "OpenPages client configured",
  "base_url": "http://na4.services.cloud.techzone.ibm.com:45439/openpages"
}
```

### 2. Test List Risks via MCP Protocol

```bash
curl -s -X POST https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "openpages_query_risks",
      "arguments": {
        "limit": 5
      }
    }
  }' | jq .
```

**Expected Output:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"risks\": [{\"id\": \"...\", \"name\": \"...\", ...}]}"
      }
    ]
  },
  "id": 2
}
```

### 3. Test List Issues

```bash
curl -s -X POST https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "openpages_query_issues",
      "arguments": {
        "limit": 5
      }
    }
  }' | jq .
```

### 4. Test List Controls

```bash
curl -s -X POST https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "openpages_query_controls",
      "arguments": {
        "limit": 5
      }
    }
  }' | jq .
```

### 5. Test Execute Query (Most Flexible)

```bash
curl -s -X POST https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tools/call",
    "params": {
      "name": "execute_openpages_query",
      "arguments": {
        "query": "SELECT [Resource ID], [Name], [Description] FROM [SOXRisk] LIMIT 5"
      }
    }
  }' | jq .
```

## Why You're Getting 404 Now

The current URL construction is:
```
Base: http://na4.services.cloud.techzone.ibm.com:45439
Client adds: /opgrc/api/v2/query
Result: http://na4.services.cloud.techzone.ibm.com:45439/opgrc/api/v2/query
```

But your TechZone instance expects:
```
http://na4.services.cloud.techzone.ibm.com:45439/openpages/opgrc/api/v2/query
                                                  ^^^^^^^^^^
                                                  Missing this!
```

## Summary

1. **Fix the URL** - Add `/openpages` (no trailing slash)
2. **Wait for restart** - 30-60 seconds
3. **Verify health check** - Should show correct base_url
4. **Test queries** - Use the commands above

The MCP server itself is working perfectly - it's just the OpenPages URL configuration that needs the `/openpages` context path.