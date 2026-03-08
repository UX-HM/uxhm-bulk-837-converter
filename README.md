# Bulk 837 Medical Claims Converter

MVP for converting CSV data to X12 837P EDI format for medical billing.

## Quick Start

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

API runs at http://localhost:8000

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `POST /upload` - Upload CSV file
- `POST /convert` - Convert to 837P
- `GET /download/{file_id}` - Download EDI file
- `GET /preview/{file_id}` - Preview EDI content

## CSV Format

Required columns:
- `member_id` - Subscriber/Member ID
- `subscriber_first_name` - First name
- `subscriber_last_name` - Last name

Optional columns (will use defaults if not provided):
- `service_date` - Service date (YYYYMMDD) - default: today
- `diagnosis_code` - ICD-10 diagnosis code - default: 999.9
- `procedure_code` - CPT/HCPCS procedure code - default: 99213
- `modifier` - Optional modifier (e.g., GT, 25)
- `quantity` - Number of units - default: 1
- `charged_amount` - Billed amount - default: 100.00

Billing provider (uses first row):
- `billing_provider_name` - Provider/organization name
- `billing_provider_npi` - NPI number (10 digits)
- `billing_provider_address` - Street address
- `billing_provider_city` - City
- `billing_provider_state` - State (2 letters)
- `billing_provider_zip` - ZIP code
- `billing_provider_tax_id` - Tax ID (EIN)

Optional patient/subscriber address:
- `subscriber_address` - Subscriber street address
- `subscriber_city` - Subscriber city
- `subscriber_state` - Subscriber state
- `subscriber_zip` - Subscriber ZIP

Submitter/Receiver:
- `submitter_name` - Submitter organization name
- `submitter_contact` - Contact name
- `submitter_phone` - Contact phone
- `receiver_name` - Receiver organization name
- `receiver_id` - Receiver ID

## Not for Clearinghouse Use

This tool generates 837P files for providers to upload manually to clearinghouses/payers. It is NOT a clearinghouse itself.
