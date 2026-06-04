# Watsonx Orchestrate Connection Issue - Fix Guide

## Problem Identified

Your Code Engine MCP server is missing **critical environment variables** required for proper operation with Watsonx Orchestrate. The server cannot start correctly without these variables.

## Current Configuration Status

### ✅ Variables You Have (Good!)
- `OPENPAGES_BASE_URL` - http://na4.services.cloud.techzone.ibm.com:45439/openpages
- `OPENPAGES_AUTHENTICATION_TYPE` - basic
- `OPENPAGES_USERNAME` - OpenPagesAdministrator
- `OPENPAGES_PASSWORD` - OpenPagesAdministrator
- `SSL_VERIFY` - False
- `DEBUG` - False
- `LOG_LEVEL` - INFO

### ❌ Missing Critical Variables (MUST ADD)

These are **required** for the server to function:

```bash
SERVER_MODE=remote
PORT=8000
HOST=0.0.0.0
```

### 📊 Recommended Variables (Should Add)

For better performance and monitoring:

```bash
OBSERVABILITY_ENABLED=True
METRICS_ENABLED=True
TRACING_ENABLED=False
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10
```

---

## Step-by-Step Fix Instructions

### Option 1: Using IBM Cloud Console (Easiest)

1. **Navigate to Your Application**
   - Go to: https://cloud.ibm.com/codeengine/projects
   - Select your project
   - Click on application: `openpages-mcp-v2`

2. **Add Missing Variables**
   - Click the **"Environment variables"** tab
   - Click **"Add"** button for each variable below:

   | Variable Name | Type | Value |
   |--------------|------|-------|
   | `SERVER_MODE` | Literal | `remote` |
   | `PORT` | Literal | `8000` |
   | `HOST` | Literal | `0.0.0.0` |
   | `OBSERVABILITY_ENABLED` | Literal | `True` |
   | `METRICS_ENABLED` | Literal | `True` |
   | `TRACING_ENABLED` | Literal | `False` |
   | `RATE_LIMIT_ENABLED` | Literal | `True` |
   | `RATE_LIMIT_REQUESTS_PER_MINUTE` | Literal | `60` |
   | `RATE_LIMIT_BURST_SIZE` | Literal | `10` |

3. **Save and Restart**
   - Click **"Save"** or **"Deploy"**
   - The application will automatically restart with new variables

### Option 2: Using IBM Cloud CLI (Faster)

```bash
# Login to IBM Cloud
ibmcloud login

# Select your Code Engine project
ibmcloud ce project select --name <your-project-name>

# Add all missing variables in one command
ibmcloud ce application update --name openpages-mcp-v2 \
  --env SERVER_MODE=remote \
  --env PORT=8000 \
  --env HOST=0.0.0.0 \
  --env OBSERVABILITY_ENABLED=True \
  --env METRICS_ENABLED=True \
  --env TRACING_ENABLED=False \
  --env RATE_LIMIT_ENABLED=True \
  --env RATE_LIMIT_REQUESTS_PER_MINUTE=60 \
  --env RATE_LIMIT_BURST_SIZE=10
```

---

## Verify the Fix

### 1. Check Application Status

```bash
# View application details
ibmcloud ce application get --name openpages-mcp-v2

# Check if application is running
ibmcloud ce application list
```

### 2. View Application Logs

```bash
# Follow logs in real-time
ibmcloud ce application logs --name openpages-mcp-v2 --follow

# Look for these success messages:
# - "Starting GRC MCP Server"
# - "MCP Server initialized"
# - "Application startup complete"
```

### 3. Test Health Endpoints

Your application URL should be:
```
https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud
```

Test these endpoints:

```bash
# Set your app URL
APP_URL="https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud"

# Test health check (should return 200 OK)
curl -i $APP_URL/health

# Test readiness (should return 200 OK)
curl -i $APP_URL/health/ready

# Test liveness (should return 200 OK)
curl -i $APP_URL/health/live

# Test metrics endpoint (should return metrics data)
curl -i $APP_URL/metrics
```

**Expected Response for /health:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "openpages_connection": "healthy",
    "mcp_server": "healthy"
  }
}
```

---

## Configure Watsonx Orchestrate Agent

### 1. MCP Server Connection Settings

In Watsonx Orchestrate, configure your MCP server connection:

**Server URL:**
```
https://openpages-mcp-v2.271oe4tvp6su.us-south.codeengine.appdomain.cloud
```

**Server Name:**
```
grc-mcp-server
```

### 2. Import Agent Configuration

Use one of these sample configurations:

**For Ontology-Based Tools (Recommended):**
- File: `samples/watsonx_orchastrate_sample_ontology_based_agent.yaml`
- Best for: Flexible, dynamic object type handling
- Tools: Generic tools that work with any object type

**For Type-Based Tools:**
- File: `samples/watsonx_orchastrate_sample_type_based_agent.yaml`
- Best for: Specific object types (Issue, Control, Risk, UseCase)
- Tools: Type-specific tools with optimized schemas

### 3. Important: Remove op_auth_header

⚠️ **CRITICAL**: Due to a known JWT token truncation issue, you MUST remove `op_auth_header` from your agent configuration:

**In your agent YAML, remove:**
```yaml
context_variables:
  - op_auth_header  # ❌ REMOVE THIS LINE
```

**And remove from instructions:**
```yaml
instructions: |-
  # Remove any references to:
  # op_auth_header - {op_auth_header}  # ❌ REMOVE THIS
```

The server will use the configured credentials (OpenPagesAdministrator) for all requests.

---

## Troubleshooting

### Issue: Application Not Starting

**Check logs:**
```bash
ibmcloud ce application logs --name openpages-mcp-v2
```

**Common causes:**
- Missing `SERVER_MODE`, `PORT`, or `HOST` variables
- Invalid OpenPages URL
- Network connectivity issues

### Issue: Health Check Fails

**Verify:**
1. All required environment variables are set
2. OpenPages URL is accessible from Code Engine
3. Credentials are correct

**Test OpenPages connection:**
```bash
# From your local machine
curl -u "OpenPagesAdministrator:OpenPagesAdministrator" \
  "http://na4.services.cloud.techzone.ibm.com:45439/openpages/api/metadata/object_types"
```

### Issue: Watsonx Orchestrate Cannot Connect

**Verify:**
1. MCP server URL is correct (use HTTPS)
2. Health endpoints return 200 OK
3. Server is running (check Code Engine console)
4. No firewall blocking the connection

**Test MCP protocol endpoint:**
```bash
curl -X POST $APP_URL/mcp/v1/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "test-client",
      "version": "1.0.0"
    }
  }'
```

### Issue: Tools Not Appearing in Watsonx Orchestrate

**Check:**
1. Agent YAML has correct tool names (e.g., `grc-mcp-server:openpages_upsert_object`)
2. MCP server is returning tools in list_tools response
3. Agent is properly connected to the MCP server

**Test tools endpoint:**
```bash
curl -X POST $APP_URL/mcp/v1/tools/list \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Next Steps After Fix

1. ✅ Add all missing environment variables
2. ✅ Verify application is running
3. ✅ Test health endpoints
4. ✅ Configure Watsonx Orchestrate connection
5. ✅ Import agent YAML (with op_auth_header removed)
6. ✅ Test agent with simple queries

---

## Quick Reference Commands

```bash
# View application status
ibmcloud ce application get --name openpages-mcp-v2

# View logs
ibmcloud ce application logs --name openpages-mcp-v2 --follow

# Restart application
ibmcloud ce application update --name openpages-mcp-v2

# Scale application
ibmcloud ce application update --name openpages-mcp-v2 \
  --min-scale 1 \
  --max-scale 5

# View all environment variables
ibmcloud ce application get --name openpages-mcp-v2 --output json | jq '.env'
```

---

## Additional Resources

- [Full Deployment Guide](docs/CODE_ENGINE_DEPLOYMENT.md)
- [Authentication Guide](docs/AUTHENTICATION.md)
- [Main README](README.md)
- [Environment Variables Reference](CODE_ENGINE_VARIABLES.md)

---

## Support

If you continue to experience issues after following this guide:

1. Check application logs for specific error messages
2. Verify all environment variables are set correctly
3. Test health endpoints to confirm server is running
4. Review the troubleshooting section above

**Common Success Indicators:**
- ✅ Health endpoint returns 200 OK
- ✅ Logs show "MCP Server initialized"
- ✅ Watsonx Orchestrate shows available tools
- ✅ Test queries return results