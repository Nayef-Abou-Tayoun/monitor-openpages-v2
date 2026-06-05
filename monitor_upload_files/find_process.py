#!/usr/bin/env python3
"""
OpenPages Process Finder - Standalone Version
Finds processes by ID pattern (e.g., AML_PROC_0008)
"""

import os
import sys
import asyncio
import argparse
import base64
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load .env file from the same directory as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✓ Loaded configuration from: {env_path}\n")
else:
    print(f"⚠ Warning: .env file not found at {env_path}")
    print(f"   Using environment variables or defaults\n")


# Simplified OpenPages Client (embedded)
class OpenPagesClient:
    """Simplified OpenPages API client for basic authentication"""
    
    def __init__(self, base_url: str, username: str, password: str, **kwargs):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self._http_client = None
        
    async def initialize_auth(self):
        """Initialize authentication (no-op for basic auth)"""
        pass
    
    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
    
    async def query(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Execute a query against OpenPages API"""
        if not self._http_client:
            self._http_client = httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0)
        
        url = f"{self.base_url}/opgrc/api/v2/query"
        auth_header = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            'statement': query,
            'offset': 0,
            'max_rows': 500,
            'limit': limit,
            'case_insensitive': False,
            'honor_primary': False
        }
        
        try:
            response = await self._http_client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠ Query failed with status {response.status_code}")
                return {'rows': []}
        except Exception as e:
            print(f"⚠ Request error: {str(e)}")
            return {'rows': []}


# Simple settings class
class Settings:
    def __init__(self):
        self.OPENPAGES_BASE_URL = os.getenv('OPENPAGES_BASE_URL', '')
        self.OPENPAGES_AUTHENTICATION_TYPE = os.getenv('OPENPAGES_AUTHENTICATION_TYPE', 'basic')
        self.OPENPAGES_USERNAME = os.getenv('OPENPAGES_USERNAME', '')
        self.OPENPAGES_PASSWORD = os.getenv('OPENPAGES_PASSWORD', '')
        self.OPENPAGES_APIKEY = os.getenv('OPENPAGES_APIKEY', '')
        self.OPENPAGES_AUTHENTICATION_URL = os.getenv('OPENPAGES_AUTHENTICATION_URL', '')

settings = Settings()


class ProcessFinder:
    """Find OpenPages processes by ID pattern"""
    
    def __init__(self, client: OpenPagesClient):
        self.client = client
        self.cos_client = None
        self.cos_bucket = None
        
        # Initialize COS if credentials are available
        cos_api_key = os.getenv('COS_API_KEY')
        cos_instance_crn = os.getenv('COS_INSTANCE_CRN')
        cos_endpoint = os.getenv('COS_ENDPOINT')
        cos_bucket = os.getenv('COS_BUCKET_NAME')
        
        if all([cos_api_key, cos_instance_crn, cos_endpoint, cos_bucket]):
            try:
                import ibm_boto3
                from ibm_botocore.client import Config
                
                self.cos_client = ibm_boto3.client(
                    's3',
                    ibm_api_key_id=cos_api_key,
                    ibm_service_instance_id=cos_instance_crn,
                    config=Config(signature_version='oauth'),
                    endpoint_url=cos_endpoint
                )
                self.cos_bucket = cos_bucket
                print(f"✓ IBM Cloud Object Storage initialized")
                print(f"   Bucket: {cos_bucket}\n")
            except Exception as e:
                print(f"⚠️  Failed to initialize COS: {str(e)}\n")
    
    async def find_process_by_id(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a specific process by its exact ID
        
        Args:
            process_id: The process ID (e.g., "AML_PROC_0008")
            
        Returns:
            Process details if found, None otherwise
        """
        try:
            print(f"🔍 Searching for process: {process_id}")
            
            # Query for the specific process by Name (which contains the process ID)
            query = f"SELECT * FROM [SOXProcess] WHERE [Name] = '{process_id}'"
            
            result = await self.client.query(query, limit=1)
            
            if result and result.get('rows'):
                process = result['rows'][0]
                print(f"✅ Found process: {process_id}")
                return process
            else:
                print(f"❌ Process not found: {process_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error searching for process: {str(e)}")
            return None
    
    async def find_processes_by_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Find processes matching a pattern (e.g., "AML_PROC_*")
        
        Args:
            pattern: Pattern to match (supports wildcards)
            
        Returns:
            List of matching processes
        """
        try:
            print(f"🔍 Searching for processes matching pattern: {pattern}")
            
            # Convert wildcard pattern to SQL LIKE pattern
            sql_pattern = pattern.replace('*', '%').replace('?', '_')
            
            # Query for processes matching the pattern using Name field
            query = f"SELECT * FROM [SOXProcess] WHERE [Name] LIKE '{sql_pattern}'"
            
            result = await self.client.query(query, limit=100)
            
            if result and result.get('rows'):
                processes = result['rows']
                print(f"✅ Found {len(processes)} process(es) matching pattern")
                return processes
            else:
                print(f"❌ No processes found matching pattern: {pattern}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching for processes: {str(e)}")
            return []
    
    async def find_all_processes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Find all processes (up to limit)
        
        Args:
            limit: Maximum number of processes to return
            
        Returns:
            List of processes
        """
        try:
            print(f"🔍 Retrieving all processes (limit: {limit})")
            
            query = "SELECT * FROM [SOXProcess]"
            
            result = await self.client.query(query, limit=limit)
            
            if result and result.get('rows'):
                processes = result['rows']
                print(f"✅ Found {len(processes)} process(es)")
                return processes
            else:
                print(f"❌ No processes found")
                return []
                
        except Exception as e:
            print(f"❌ Error retrieving processes: {str(e)}")
            return []
    
    async def find_process_documents(self, process_id: str) -> List[Dict[str, Any]]:
        """
        Find all documents (uploaded files) associated with a process
        
        Args:
            process_id: The process ID (e.g., "AML_PROC_0008")
            
        Returns:
            List of documents
        """
        try:
            print(f"📄 Searching for documents in process: {process_id}")
            
            # First, get the process to find its Resource ID
            process_query = f"SELECT * FROM [SOXProcess] WHERE [Name] = '{process_id}'"
            process_result = await self.client.query(process_query, limit=1)
            
            if not process_result or not process_result.get('rows'):
                print(f"❌ Process not found: {process_id}")
                return []
            
            process = process_result['rows'][0]
            resource_id = self._get_field_value(process, 'Resource ID')
            
            print(f"   Process Resource ID: {resource_id}")
            
            # Use the OpenPages API to get child associations (documents are children of processes)
            # This is more reliable than complex queries
            try:
                import httpx
                # Remove /openpages from base_url if present and add /grc/api
                base = self.client.base_url.replace('/openpages', '').rstrip('/')
                url = f"{base}/grc/api/contents/{resource_id}/associations/children"
                headers = {"Accept": "application/json"}
                
                # Create a simple HTTP client for this request with redirect following
                async with httpx.AsyncClient(verify=False, follow_redirects=True) as http_client:
                    response = await http_client.get(
                        url,
                        headers=headers,
                        auth=(self.client.username, self.client.password),
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        # Check if response has content
                        if not response.text or response.text.strip() == '':
                            print(f"ℹ️  No documents found for process: {process_id} (empty response)")
                            return []
                        
                        try:
                            children = response.json()
                        except Exception as json_error:
                            print(f"⚠️  Response is not JSON. Status: {response.status_code}")
                            print(f"   Response text: {response.text[:200]}")
                            return []
                        
                        # Filter for documents (type 4 for this system, also check 22, 42, 46)
                        documents = [child for child in children if child.get('typeDefinitionId') in ['4', '22', '42', '46']]
                        
                        if documents:
                            print(f"✅ Found {len(documents)} document(s)")
                            print(f"   Fetching detailed information for each document...")
                            
                            # Fetch full details for each document
                            formatted_docs = []
                            for i, doc in enumerate(documents, 1):
                                doc_id = doc.get('id')
                                doc_path = doc.get('path', 'Unknown')
                                
                                # Extract filename from path
                                filename = doc_path.split('/')[-1] if doc_path != 'Unknown' else 'Unknown'
                                
                                # Fetch full document details
                                try:
                                    detail_url = f"{base}/grc/api/contents/{doc_id}"
                                    detail_response = await http_client.get(
                                        detail_url,
                                        headers=headers,
                                        auth=(self.client.username, self.client.password),
                                        timeout=30.0
                                    )
                                    
                                    if detail_response.status_code == 200:
                                        doc_details = detail_response.json()
                                        doc_name = doc_details.get('name', filename)
                                        doc_desc = doc_details.get('description', '')
                                        created_date = doc_details.get('createdDate', 'N/A')
                                    else:
                                        doc_name = filename
                                        doc_desc = ''
                                        created_date = 'N/A'
                                except Exception as e:
                                    doc_name = filename
                                    doc_desc = ''
                                    created_date = 'N/A'
                                
                                formatted_doc = {
                                    'fields': [
                                        {'name': 'Resource ID', 'value': doc_id},
                                        {'name': 'Name', 'value': doc_name},
                                        {'name': 'Description', 'value': doc_desc},
                                        {'name': 'Location', 'value': doc_path},
                                        {'name': 'Creation Date', 'value': created_date},
                                    ]
                                }
                                formatted_docs.append(formatted_doc)
                                print(f"      [{i}/{len(documents)}] {doc_name}")
                            
                            return formatted_docs
                        else:
                            print(f"ℹ️  No documents found for process: {process_id}")
                            return []
                    else:
                        print(f"⚠️  API returned status {response.status_code}")
                        return []
                        
            except Exception as api_error:
                print(f"❌ Error calling OpenPages API: {str(api_error)}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching for documents: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    async def monitor_process_for_new_documents(self, process_id: str, check_interval: int = 60):
        """
        Continuously monitor a process for new document uploads
        
        Args:
            process_id: The process ID to monitor
            check_interval: Seconds between checks
        """
        known_documents: set = set()
        
        print("\n" + "=" * 70)
        print("DOCUMENT MONITORING STARTED")
        print("=" * 70)
        print(f"Process ID: {process_id}")
        print(f"Check Interval: {check_interval} seconds")
        print(f"COS Upload: {'ENABLED ☁️' if self.cos_client else 'DISABLED'}")
        print("=" * 70)
        
        # Initialize - get existing documents
        print("\n📥 Initializing - scanning for existing documents...")
        documents = await self.find_process_documents(process_id)
        
        if documents:
            print(f"   Found {len(documents)} existing document(s)")
            for doc in documents:
                doc_id = self._get_field_value(doc, 'Resource ID')
                doc_name = self._get_field_value(doc, 'Name')
                known_documents.add(doc_id)
                print(f"      - {doc_name} (ID: {doc_id})")
            
            # Download existing documents if COS is enabled
            if self.cos_client:
                print(f"\n   Downloading existing documents to COS...")
                await self.download_documents_to_cos(process_id, documents)
        else:
            print(f"   No existing documents found")
        
        print(f"\n✓ Initialization complete")
        print(f"👀 Now monitoring for NEW documents... (Press Ctrl+C to stop)\n")
        
        # Start monitoring loop
        check_count = 0
        try:
            while True:
                check_count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Check for documents
                current_documents = await self.find_process_documents(process_id)
                
                # Find new documents
                new_docs = []
                for doc in current_documents:
                    doc_id = self._get_field_value(doc, 'Resource ID')
                    if doc_id not in known_documents:
                        new_docs.append(doc)
                        known_documents.add(doc_id)
                
                if new_docs:
                    print(f"[{timestamp}] 🆕 NEW DOCUMENT(S) DETECTED: {len(new_docs)}")
                    for doc in new_docs:
                        doc_id = self._get_field_value(doc, 'Resource ID')
                        doc_name = self._get_field_value(doc, 'Name')
                        print(f"   - {doc_name} (ID: {doc_id})")
                    
                    # Download new documents if COS is enabled
                    if self.cos_client:
                        print(f"\n   Downloading new documents to COS...")
                        await self.download_documents_to_cos(process_id, new_docs)
                    
                    print()
                else:
                    if check_count % 10 == 0:  # Log every 10 checks
                        print(f"[{timestamp}] ℹ️  No new documents (tracking {len(known_documents)} documents)")
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n⏹ Monitoring stopped by user")
            print(f"   Total documents tracked: {len(known_documents)}")
    
    async def download_documents_to_cos(self, process_id: str, documents: List[Dict[str, Any]]) -> int:
        """
        Download documents from OpenPages and upload to IBM Cloud Object Storage
        
        Args:
            process_id: The process ID
            documents: List of documents to download
            
        Returns:
            Number of documents successfully downloaded
        """
        if not self.cos_client:
            print("❌ IBM Cloud Object Storage not configured")
            return 0
        
        if not documents:
            print("ℹ️  No documents to download")
            return 0
        
        print(f"\n📥 Downloading {len(documents)} document(s) to COS...")
        success_count = 0
        
        try:
            import httpx
            base = self.client.base_url.replace('/openpages', '').rstrip('/')
            
            async with httpx.AsyncClient(verify=False, follow_redirects=True) as http_client:
                for i, doc in enumerate(documents, 1):
                    doc_id = self._get_field_value(doc, 'Resource ID')
                    doc_name = self._get_field_value(doc, 'Name')
                    
                    try:
                        # Download document from OpenPages
                        download_url = f"{base}/grc/api/contents/{doc_id}/document"
                        headers = {"Accept": "application/octet-stream"}
                        
                        print(f"   [{i}/{len(documents)}] Downloading {doc_name}...")
                        
                        response = await http_client.get(
                            download_url,
                            headers=headers,
                            auth=(self.client.username, self.client.password),
                            timeout=60.0
                        )
                        
                        if response.status_code == 200:
                            file_content = response.content
                            file_size = len(file_content)
                            
                            # Upload to COS
                            cos_key = f"Process_{process_id}/{doc_name}"
                            
                            self.cos_client.put_object(
                                Bucket=self.cos_bucket,
                                Key=cos_key,
                                Body=file_content
                            )
                            
                            print(f"      ✅ Uploaded to COS: {cos_key} ({file_size:,} bytes)")
                            success_count += 1
                        else:
                            print(f"      ❌ Failed to download: HTTP {response.status_code}")
                    
                    except Exception as e:
                        print(f"      ❌ Error: {str(e)}")
                        continue
        
        except Exception as e:
            print(f"❌ Error during download: {str(e)}")
        
        print(f"\n✅ Successfully downloaded {success_count}/{len(documents)} document(s) to COS")
        return success_count
    
    def _get_field_value(self, process: Dict[str, Any], field_name: str) -> str:
        """Extract field value from process data"""
        if 'fields' in process:
            for field in process['fields']:
                if field.get('name') == field_name:
                    value = field.get('value')
                    if value is None:
                        return 'N/A'
                    elif isinstance(value, dict):
                        # Handle enum values
                        return value.get('name', str(value))
                    elif isinstance(value, bool):
                        return 'Yes' if value else 'No'
                    else:
                        return str(value)
        return 'N/A'
    
    def display_process(self, process: Dict[str, Any]):
        """Display process information in a readable format"""
        print("\n" + "=" * 70)
        print("PROCESS DETAILS")
        print("=" * 70)
        
        # Extract key fields
        resource_id = self._get_field_value(process, 'Resource ID')
        name = self._get_field_value(process, 'Name')
        description = self._get_field_value(process, 'Description')
        location = self._get_field_value(process, 'Location')
        status = self._get_field_value(process, 'OPSS-Process:Status')
        business_owner = self._get_field_value(process, 'OPSS-Process:Business Owner')
        process_owner = self._get_field_value(process, 'OPSS-Process:Process Owner')
        created_by = self._get_field_value(process, 'Created By')
        creation_date = self._get_field_value(process, 'Creation Date')
        
        print(f"Resource ID:      {resource_id}")
        print(f"Name:             {name}")
        print(f"Description:      {description}")
        print(f"Location:         {location}")
        print(f"Status:           {status}")
        print(f"Business Owner:   {business_owner}")
        print(f"Process Owner:    {process_owner}")
        print(f"Created By:       {created_by}")
        print(f"Creation Date:    {creation_date}")
        
        # Display all fields if available
        if 'fields' in process:
            print("\nAll Fields:")
            for field in process['fields']:
                field_name = field.get('name', 'Unknown')
                value = field.get('value')
                if value is not None:
                    if isinstance(value, dict):
                        value_str = value.get('name', str(value))
                    else:
                        value_str = str(value)
                    # Truncate long values
                    if len(value_str) > 60:
                        value_str = value_str[:60] + "..."
                    print(f"  {field_name}: {value_str}")
        
        print("=" * 70 + "\n")
    
    def display_process_list(self, processes: List[Dict[str, Any]]):
        """Display a list of processes in a table format"""
        if not processes:
            print("\nNo processes to display.\n")
            return
        
        print("\n" + "=" * 120)
        print(f"{'Resource ID':<15} {'Name':<25} {'Description':<40} {'Status':<20}")
        print("=" * 120)
        
        for process in processes:
            resource_id = self._get_field_value(process, 'Resource ID')
            name = self._get_field_value(process, 'Name')
            description = self._get_field_value(process, 'Description')
            status = self._get_field_value(process, 'OPSS-Process:Status')
            
            # Truncate long values
            if len(name) > 22:
                name = name[:22] + "..."
            if len(description) > 37:
                description = description[:37] + "..."
            if len(status) > 17:
                status = status[:17] + "..."
            
            print(f"{resource_id:<15} {name:<25} {description:<40} {status:<20}")
        
        print("=" * 120 + "\n")
    
    def display_documents(self, documents: List[Dict[str, Any]]):
        """Display a list of documents in a table format"""
        if not documents:
            print("\nNo documents to display.\n")
            return
        
        print("\n" + "=" * 120)
        print(f"{'Resource ID':<15} {'Name':<40} {'Created':<25} {'Location':<40}")
        print("=" * 120)
        
        for doc in documents:
            resource_id = self._get_field_value(doc, 'Resource ID')
            name = self._get_field_value(doc, 'Name')
            created = self._get_field_value(doc, 'Creation Date')
            location = self._get_field_value(doc, 'Location')
            
            # Truncate long values
            if len(name) > 37:
                name = name[:37] + "..."
            if len(created) > 22:
                created = created[:22] + "..."
            if len(location) > 37:
                location = location[:37] + "..."
            
            print(f"{resource_id:<15} {name:<40} {created:<25} {location:<40}")
        
        print("=" * 120 + "\n")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Find OpenPages processes by ID or pattern',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find a specific process by ID
  python find_process.py --id AML_PROC_0008
  
  # Find processes matching a pattern
  python find_process.py --pattern "AML_PROC_*"
  
  # List all processes (up to 50)
  python find_process.py --all
  
  # List all processes with custom limit
  python find_process.py --all --limit 100
        """
    )
    
    parser.add_argument('--id', type=str, help='Find process by exact ID (e.g., AML_PROC_0008)')
    parser.add_argument('--pattern', type=str, help='Find processes matching pattern (e.g., AML_PROC_*)')
    parser.add_argument('--all', action='store_true', help='List all processes')
    parser.add_argument('--documents', action='store_true', help='Show documents (uploaded files) for the process')
    parser.add_argument('--download', action='store_true', help='Download documents to IBM Cloud Object Storage')
    parser.add_argument('--monitor', action='store_true', help='Continuously monitor for new document uploads')
    parser.add_argument('--interval', type=int, default=60, help='Monitor check interval in seconds (default: 60)')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of processes to return (default: 50)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed process information')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.id, args.pattern, args.all]):
        parser.error('Must specify one of: --id, --pattern, or --all')
    
    # Initialize OpenPages client
    print("🔌 Connecting to OpenPages...")
    print(f"   Server: {settings.OPENPAGES_BASE_URL}")
    print(f"   Auth Type: {settings.OPENPAGES_AUTHENTICATION_TYPE}")
    
    try:
        client = OpenPagesClient(
            base_url=settings.OPENPAGES_BASE_URL,
            auth_type=settings.OPENPAGES_AUTHENTICATION_TYPE,
            username=settings.OPENPAGES_USERNAME,
            password=settings.OPENPAGES_PASSWORD,
            api_key=settings.OPENPAGES_APIKEY,
            authentication_url=settings.OPENPAGES_AUTHENTICATION_URL
        )
        
        # Initialize authentication
        await client.initialize_auth()
        print("✅ Connected successfully\n")
        
        # Create finder
        finder = ProcessFinder(client)
        
        # Execute search based on arguments
        if args.id:
            # If --monitor flag is set, start continuous monitoring
            if args.monitor:
                await finder.monitor_process_for_new_documents(args.id, args.interval)
            else:
                # Find by exact ID
                process = await finder.find_process_by_id(args.id)
                if process:
                    if args.verbose:
                        finder.display_process(process)
                    else:
                        finder.display_process_list([process])
                    
                    # If --documents flag is set, also show documents
                    if args.documents:
                        print("\n" + "=" * 70)
                        print("DOCUMENTS IN PROCESS")
                        print("=" * 70)
                        documents = await finder.find_process_documents(args.id)
                        if documents:
                            finder.display_documents(documents)
                            
                            # If --download flag is set, download documents to COS
                            if args.download:
                                await finder.download_documents_to_cos(args.id, documents)
        
        elif args.pattern:
            # Find by pattern
            processes = await finder.find_processes_by_pattern(args.pattern)
            if processes:
                if args.verbose:
                    for process in processes:
                        finder.display_process(process)
                else:
                    finder.display_process_list(processes)
        
        elif args.all:
            # Find all processes
            processes = await finder.find_all_processes(limit=args.limit)
            if processes:
                if args.verbose:
                    for process in processes:
                        finder.display_process(process)
                else:
                    finder.display_process_list(processes)
        
        # Close client
        await client.close()
        print("✅ Done!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
