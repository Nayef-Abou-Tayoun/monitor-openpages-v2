#!/usr/bin/env python3
"""
Upload AI-generated summaries from COS to OpenPages
Uses httpx async client like find_process.py for proper authentication
"""

import os
import sys
import asyncio
import base64
from datetime import datetime
import httpx
import ibm_boto3
from ibm_botocore.client import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenPages Server Configuration
OPENPAGES_SERVER = os.getenv("OPENPAGES_SERVER")
USERNAME = os.getenv("OPENPAGES_USERNAME")
PASSWORD = os.getenv("OPENPAGES_PASSWORD")

# Process to Upload To
PROCESS_ID = os.getenv("PROCESS_ID")
PROCESS_NAME = os.getenv("PROCESS_NAME")

# IBM Cloud Object Storage Configuration
COS_API_KEY = os.getenv("COS_API_KEY")
COS_INSTANCE_CRN = os.getenv("COS_INSTANCE_CRN")
COS_ENDPOINT = os.getenv("COS_ENDPOINT")
COS_BUCKET_NAME = os.getenv("COS_BUCKET_NAME")


class SummaryUploader:
    """Upload AI-generated summaries from COS to OpenPages"""
    
    def __init__(self, server, username, password, process_id,
                 cos_api_key, cos_instance_crn, cos_endpoint, cos_bucket):
        # Normalize server URL
        self.server = server.rstrip('/')
        self.username = username
        self.password = password
        self.process_id = process_id
        self.cos_bucket = cos_bucket
        
        # Initialize IBM COS client
        self.cos_client = ibm_boto3.client(
            's3',
            ibm_api_key_id=cos_api_key,
            ibm_service_instance_id=cos_instance_crn,
            config=Config(signature_version='oauth'),
            endpoint_url=cos_endpoint
        )
        
        print(f"✓ COS client initialized")
        print(f"  Bucket: {cos_bucket}")
        print(f"✓ OpenPages client initialized")
        print(f"  Server: {self.server}")
    
    def log(self, message):
        """Print timestamped log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def list_summary_files(self):
        """List all summary DOCX files in COS for the process"""
        prefix = f"Process_{self.process_id}/"
        summaries = []
        
        try:
            response = self.cos_client.list_objects_v2(
                Bucket=self.cos_bucket,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Only get summary DOCX files
                    if '_summary_' in key and key.endswith('.docx'):
                        summaries.append({
                            'key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'filename': os.path.basename(key)
                        })
            
            return summaries
        except Exception as e:
            self.log(f"❌ Error listing COS objects: {e}")
            return []
    
    def download_from_cos(self, key):
        """Download a file from COS"""
        try:
            response = self.cos_client.get_object(
                Bucket=self.cos_bucket,
                Key=key
            )
            return response['Body'].read()
        except Exception as e:
            self.log(f"❌ Error downloading {key}: {e}")
            return None
    
    async def get_document_folder_id(self, process_id):
        """Get the folder ID where documents for this process are stored"""
        try:
            import httpx
            base = self.server.replace('/openpages', '').rstrip('/')
            url = f"{base}/grc/api/contents/{process_id}/associations/children"
            
            async with httpx.AsyncClient(verify=False, follow_redirects=True) as http_client:
                response = await http_client.get(
                    url,
                    auth=(self.username, self.password),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    children = response.json()
                    
                    if not children:
                        return None
                    
                    # Try to find any document to get its folder
                    for child in children:
                        doc_id = child.get('id')
                        
                        if doc_id:
                            doc_url = f"{base}/grc/api/contents/{doc_id}"
                            doc_response = await http_client.get(
                                doc_url,
                                auth=(self.username, self.password),
                                timeout=30.0
                            )
                            
                            if doc_response.status_code == 200:
                                doc_data = doc_response.json()
                                folder_id = doc_data.get('parentFolderId')
                                
                                if folder_id:
                                    return folder_id
                
                return None
                
        except Exception as e:
            self.log(f"      ⚠ Exception getting document folder: {str(e)}")
            return None
    
    async def upload_to_openpages(self, file_content, filename, description):
        """Upload a document to OpenPages using httpx async client"""
        try:
            # Use known folder ID for AML_PROC_00081
            folder_id = "31628"
            self.log(f"      Using folder ID: {folder_id}")
            
            # Extract original document name from summary filename
            # Format: doc_1 [4]_summary_20260606_160856.docx -> doc_1 [4]
            # Keep version numbers to ensure unique filenames
            name_without_ext = filename.rsplit('.', 1)[0]  # Remove .docx
            
            # Find the original document name (everything before _summary)
            if '_summary_' in name_without_ext:
                original_doc_name = name_without_ext.split('_summary_')[0]
            else:
                original_doc_name = name_without_ext
            
            # Create summary filename with timestamp to ensure uniqueness and avoid "object already exists" error
            timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_filename = f"Executive Risk Summary - {original_doc_name} - {timestamp_suffix}"
            self.log(f"      📤 Creating summary: {summary_filename}")
            
            # Encode file content
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            
            # Remove /openpages from base_url if present
            base = self.server.replace('/openpages', '').rstrip('/')
            create_url = f"{base}/grc/api/contents"
            
            create_payload = {
                "contentDefinition": {
                    "attribute": {
                        "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    },
                    "children": file_content_b64
                },
                "fileTypeDefinition": {
                    "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                },
                "fields": {
                    "field": []
                },
                "typeDefinitionId": "4",  # SOXDocument type (same as existing docs)
                "parentFolderId": folder_id,
                "name": summary_filename.replace('.txt', '').replace('.docx', ''),
                "description": description
            }
            
            self.log(f"      📤 Uploading: {summary_filename}")
            
            # Use httpx async client like find_process.py
            async with httpx.AsyncClient(verify=False, follow_redirects=True) as http_client:
                response = await http_client.post(
                    create_url,
                    json=create_payload,
                    auth=(self.username, self.password),
                    timeout=60.0
                )
                
                self.log(f"      Response status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    try:
                        doc_data = response.json()
                        doc_id = doc_data.get('id')
                        self.log(f"      ✅ Document created (ID: {doc_id})")
                        
                        # Step 2: Associate document with process as a child
                        # Per OpenPages REST API docs page 24
                        process_id = "31619"  # AML_PROC_00081 resource ID
                        assoc_url = f"{base}/grc/api/contents/{process_id}/associations/children"
                        
                        # POST with array containing the new child document
                        assoc_payload = [{"id": doc_id}]
                        
                        self.log(f"      🔗 Associating with process...")
                        assoc_response = await http_client.post(
                            assoc_url,
                            json=assoc_payload,
                            auth=(self.username, self.password),
                            timeout=30.0
                        )
                        
                        if assoc_response.status_code in [200, 201, 204]:
                            self.log(f"      ✅ Successfully associated with process")
                            return doc_id
                        else:
                            self.log(f"      ⚠ Association failed: HTTP {assoc_response.status_code}")
                            self.log(f"         Response: {assoc_response.text[:200]}")
                            self.log(f"         Document created but may not appear in Files tab")
                            return doc_id
                    except Exception as e:
                        self.log(f"      ⚠ Failed to parse response: {e}")
                        self.log(f"         Response: {response.text[:200]}")
                        return None
                else:
                    self.log(f"      ⚠ Upload failed: HTTP {response.status_code}")
                    self.log(f"         {response.text[:200]}")
                    return None
        
        except Exception as e:
            self.log(f"      ❌ Error uploading: {e}")
            return None
    
    async def upload_all_summaries(self):
        """Upload all summary files from COS to OpenPages"""
        print(f"\n{'='*70}")
        print(f"UPLOADING SUMMARIES FROM COS TO OPENPAGES")
        print(f"{'='*70}")
        print(f"Process ID: {self.process_id}")
        print(f"COS Bucket: {self.cos_bucket}")
        print(f"{'='*70}\n")
        
        # List summary files
        self.log("📋 Listing summary files in COS...")
        summaries = self.list_summary_files()
        
        if not summaries:
            self.log("ℹ️  No summary files found in COS")
            return
        
        self.log(f"✅ Found {len(summaries)} summary file(s)\n")
        
        # Upload each summary
        success_count = 0
        for i, summary in enumerate(summaries, 1):
            print(f"[{i}/{len(summaries)}] Processing: {summary['filename']}")
            print(f"   Size: {summary['size']:,} bytes")
            print(f"   Last Modified: {summary['last_modified']}")
            
            # Download from COS
            file_content = self.download_from_cos(summary['key'])
            if not file_content:
                print(f"   ⚠ Skipping - download failed\n")
                continue
            
            # Upload to OpenPages
            description = f"AI-generated executive summary (uploaded from COS)"
            doc_id = await self.upload_to_openpages(
                file_content,
                summary['filename'],
                description
            )
            
            if doc_id:
                success_count += 1
            
            print()
        
        print(f"{'='*70}")
        print(f"✅ Upload complete: {success_count}/{len(summaries)} successful")
        print(f"{'='*70}\n")


async def main():
    """Main entry point"""
    # Get process ID from command line or environment
    process_id = None
    
    if len(sys.argv) > 1:
        process_id = sys.argv[1]
    else:
        process_id = PROCESS_ID or PROCESS_NAME
    
    if not process_id:
        print("❌ Error: Process ID not provided")
        print("\nUsage:")
        print("  python upload_summaries_from_cos.py <PROCESS_ID>")
        print("\nOr set PROCESS_ID environment variable")
        sys.exit(1)
    
    # Validate required environment variables
    if not all([OPENPAGES_SERVER, USERNAME, PASSWORD]):
        print("❌ Error: OpenPages credentials not configured")
        print("   Required: OPENPAGES_SERVER, OPENPAGES_USERNAME, OPENPAGES_PASSWORD")
        sys.exit(1)
    
    if not all([COS_API_KEY, COS_INSTANCE_CRN, COS_ENDPOINT, COS_BUCKET_NAME]):
        print("❌ Error: COS credentials not configured")
        print("   Required: COS_API_KEY, COS_INSTANCE_CRN, COS_ENDPOINT, COS_BUCKET_NAME")
        sys.exit(1)
    
    try:
        uploader = SummaryUploader(
            server=OPENPAGES_SERVER,
            username=USERNAME,
            password=PASSWORD,
            process_id=process_id,
            cos_api_key=COS_API_KEY,
            cos_instance_crn=COS_INSTANCE_CRN,
            cos_endpoint=COS_ENDPOINT,
            cos_bucket=COS_BUCKET_NAME
        )
        await uploader.upload_all_summaries()
    except KeyboardInterrupt:
        print("\n\n⏹ Upload stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
