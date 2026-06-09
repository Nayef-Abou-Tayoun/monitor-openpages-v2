# DOCX Text Extraction Enhancement

## Overview
Enhanced the DOCX text extraction to capture **all content** from Word documents, not just paragraphs.

## What's New

### Previous Behavior
- ❌ Only extracted paragraph text
- ❌ Skipped tables
- ❌ Ignored headers and footers
- ❌ Missed text boxes and other content

### Enhanced Behavior
- ✅ Extracts all paragraph text
- ✅ Extracts all table content (formatted with `|` separators)
- ✅ Extracts headers (marked as `[Header: ...]`)
- ✅ Extracts footers (marked as `[Footer: ...]`)
- ✅ Preserves document structure with double newlines between sections

## Code Changes

**File**: `monitor_upload_files/find_process.py` (lines 416-461)

### New Extraction Logic:

1. **Paragraphs**: All paragraph text is extracted
2. **Tables**: Each table is extracted with:
   - Rows separated by newlines
   - Cells separated by ` | ` (pipe character)
   - Nested paragraphs within cells are included
3. **Headers**: Extracted from all document sections with `[Header: ...]` prefix
4. **Footers**: Extracted from all document sections with `[Footer: ...]` prefix

### Example Output Format:

```
This is a paragraph from the document.

Another paragraph here.

Column1 | Column2 | Column3
Data1 | Data2 | Data3
More data | More data | More data

[Header: Document Title - Page 1]

[Footer: Confidential - Page 1 of 5]
```

## Deployment

### Option 1: Rebuild Docker Image (Recommended)

```bash
cd monitor_upload_files
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Option 2: Update Running Container

```bash
# Copy updated file to container
docker cp monitor_upload_files/find_process.py openpages-document-monitor:/app/find_process.py

# Restart container
docker-compose restart
```

### Option 3: Deploy to IBM Code Engine

```bash
# Build and push new image
cd monitor_upload_files
docker build -t us.icr.io/<your-namespace>/openpages-monitor:latest .
docker push us.icr.io/<your-namespace>/openpages-monitor:latest

# Update Code Engine application
ibmcloud ce application update --name trigger-openpages-wxo --image us.icr.io/<your-namespace>/openpages-monitor:latest
```

## Testing

After deployment, the trigger will automatically use the enhanced extraction for new documents:

1. Upload a DOCX file with tables to OpenPages
2. Check the logs: `ibmcloud ce application logs --name trigger-openpages-wxo --tail 50`
3. Verify the extracted text includes table content
4. Check the generated summary in COS or OpenPages

## Benefits

- **More Complete Analysis**: Watson Orchestrate receives all document content for better summaries
- **Table Data Included**: Financial data, risk matrices, and other tabular information is now captured
- **Better Context**: Headers and footers provide additional document context
- **Improved Accuracy**: AI summaries will be more comprehensive and accurate

## Notes

- Empty rows and cells are automatically filtered out
- Table formatting uses simple pipe separators for readability
- Headers and footers are clearly marked to distinguish them from body content
- The enhancement is backward compatible with existing documents