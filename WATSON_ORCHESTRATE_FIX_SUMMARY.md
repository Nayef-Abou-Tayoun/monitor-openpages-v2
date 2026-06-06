# Watson Orchestrate Integration Fix Summary

## Problem
The OpenPages Document Monitor script was not working with Watson Orchestrate integration. The script would fail to generate executive summaries from documents.

## Root Causes Identified

### 1. **Wrong IAM Token Endpoint** ❌
**Original (Incorrect):**
```python
url = "https://iam.platform.saas.ibm.com/siusermgr/api/1.0/apikeys/token"
response = requests.post(url, json={"apikey": self.wxo_api_key}, timeout=30)
```

**Fixed:**
```python
url = "https://iam.cloud.ibm.com/identity/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}
data = {
    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
    "apikey": self.wxo_api_key
}
response = requests.post(url, headers=headers, data=data, timeout=30)
```

**Why it failed:**
- Wrong endpoint URL (non-existent service)
- Wrong request format (JSON instead of form data)
- Missing required `grant_type` parameter

### 2. **Wrong Watson Orchestrate API Endpoint** ❌
**Original (Incorrect):**
```python
url = f"https://api.dl.watson-orchestrate.ibm.com/instances/{self.wxo_instance_id}/v1/orchestrate/{self.wxo_agent_id}/chat/completions"
```

**Fixed:**
```python
url = f"https://api.watsonx.ai/v1/watson_orchestrate/instances/{self.wxo_instance_id}/agents/{self.wxo_agent_id}/chat/completions"
```

**Why it failed:**
- Wrong base domain (`api.dl.watson-orchestrate.ibm.com` → `api.watsonx.ai`)
- Wrong path structure (`/v1/orchestrate/` → `/v1/watson_orchestrate/instances/`)
- Wrong resource name (`orchestrate` → `agents`)

### 3. **Token Expiration Handling** ⚠️
**Original:**
```python
def is_token_expired(self, expiration_time):
    return int(time.time()) > expiration_time
```

**Fixed:**
```python
def is_token_expired(self, expiration_time):
    """Check if the token is expired (with 60 second buffer)"""
    return int(time.time()) >= (expiration_time - 60)
```

**Why improved:**
- Added 60-second buffer to prevent edge-case failures
- Proactive token refresh before actual expiration

### 4. **Missing Error Handling** ⚠️
**Added:**
- Automatic token refresh on 401 (Unauthorized) responses
- Detailed error logging with tracebacks
- Better exception handling throughout

## Key Changes Made

### 1. IAM Token Authentication
```python
def get_bearer_token(self):
    """Get or refresh the Watson Orchestrate bearer token - FIXED VERSION"""
    if self.wxo_token and not self.is_token_expired(self.wxo_token_expiration):
        return self.wxo_token
    
    try:
        # FIXED: Correct IBM Cloud IAM token endpoint
        url = "https://iam.cloud.ibm.com/identity/token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": self.wxo_api_key
        }
        
        self.log(f"🔑 Requesting Watson Orchestrate IAM token...")
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            self.wxo_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            self.wxo_token_expiration = int(time.time()) + expires_in
            self.log(f"✓ Watson Orchestrate token obtained (expires in {expires_in}s)")
            return self.wxo_token
        else:
            self.log(f"⚠ Token request failed: HTTP {response.status_code}")
            self.log(f"   Response: {response.text[:500]}")
            return None
    except Exception as e:
        self.log(f"⚠ Exception getting token: {str(e)}")
        import traceback
        self.log(f"   Traceback: {traceback.format_exc()}")
        return None
```

### 2. Watson Orchestrate API Call
```python
def trigger_wxo_executive_summary(self, document_text, filename, doc_id):
    """Trigger Watson Orchestrate executive summary agent - FIXED VERSION"""
    if not self.wxo_enabled:
        return None
    
    try:
        # Get bearer token
        token = self.get_bearer_token()
        if not token:
            self.log(f"⚠ Failed to get Watson Orchestrate token")
            return None
        
        # FIXED: Correct Watson Orchestrate API endpoint format
        url = f"https://api.watsonx.ai/v1/watson_orchestrate/instances/{self.wxo_instance_id}/agents/{self.wxo_agent_id}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }
        
        self.log(f"🤖 Triggering Watson Orchestrate executive summary agent...")
        self.log(f"   Endpoint: {url}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get("choices", [{}])[0].get("message", {}).get("content", "No response returned.")
            # ... process summary ...
            return result
        else:
            self.log(f"⚠ Watson Orchestrate agent failed: HTTP {response.status_code}")
            self.log(f"   Response: {response.text[:500]}")
            
            # If unauthorized, clear token to force refresh on next attempt
            if response.status_code == 401:
                self.log(f"   Token expired or invalid - will refresh on next attempt")
                self.wxo_token = None
                self.wxo_token_expiration = 0
            
            return None
    except Exception as e:
        self.log(f"⚠ Exception calling Watson Orchestrate agent: {str(e)}")
        import traceback
