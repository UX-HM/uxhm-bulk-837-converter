import io
import os
import uuid
from datetime import datetime
from typing import Dict

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI(title="837 Converter API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for generated files (for MVP)
generated_files: Dict[str, str] = {}


class ConvertRequest(BaseModel):
    file_id: str


def generate_837P(df: pd.DataFrame, mapping: Dict[str, str]) -> str:
    """Generate 837P EDI file from CSV dataframe."""
    
    # Generate unique control numbers
    isa_control_num = str(uuid.uuid4())[:15].zfill(15)
    gs_control_num = str(uuid.uuid4())[:9].zfill(9)
    st_control_num = "0001"
    
    # Get current date/time
    now = datetime.now()
    date_str = now.strftime("%y%m%d")
    time_str = now.strftime("%H%M")
    
    # Get provider info from first row (or use defaults)
    first_row = df.iloc[0] if len(df) > 0 else {}
    billing_provider_name = first_row.get('billing_provider_name', 'BILLING PROVIDER')
    billing_provider_npi = first_row.get('billing_provider_npi', '1234567890')
    billing_provider_address = first_row.get('billing_provider_address', '123 MAIN STREET')
    billing_provider_city = first_row.get('billing_provider_city', 'CITY')
    billing_provider_state = first_row.get('billing_provider_state', 'ST')
    billing_provider_zip = first_row.get('billing_provider_zip', '12345')
    billing_provider_tax_id = first_row.get('billing_provider_tax_id', '123456789')
    submitter_name = first_row.get('submitter_name', 'SUBMITTER NAME')
    submitter_contact = first_row.get('submitter_contact', 'CONTACT NAME')
    submitter_phone = first_row.get('submitter_phone', '5555555555')
    receiver_name = first_row.get('receiver_name', 'RECEIVER NAME')
    receiver_id = first_row.get('receiver_id', 'RECEIVER')
    
    # Start building the ISA/GS envelope
    edi = []
    
    # ISA - Interchange Control Header
    edi.append(f"ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *{date_str}*{time_str}*U*00401*{isa_control_num}*0*P*>~")
    
    # GS - Functional Group Header
    edi.append(f"GS*HC*SENDER*RECEIVER*{now.strftime('%Y%m%d')}*{time_str}*{gs_control_num}*X*004010~")
    
    # ST - Transaction Set Header
    edi.append(f"ST*837*{st_control_num}*005010~")
    
    # BHT - Beginning of Hierarchical Transaction
    edi.append(f"BHT*0019*00*{uuid.uuid4().hex[:16]}*{date_str}*{time_str}*CH~")
    
    # Loop 1000A - Submitter Name
    edi.append(f"NM1*41*2*{submitter_name}*****46*SENDER~")
    edi.append(f"PER*IC*{submitter_contact}*TE*{submitter_phone}~")
    
    # Loop 1000B - Receiver Name
    edi.append(f"NM1*40*2*{receiver_name}*****46*{receiver_id}~")
    
    # Loop 2000A - Billing Provider Hierarchical Level
    edi.append("HL*1**20*1~")
    edi.append(f"NM1*85*1*{billing_provider_name}******XX*{billing_provider_npi}~")
    edi.append(f"N3*{billing_provider_address}~")
    edi.append(f"N4*{billing_provider_city}*{billing_provider_state}*{billing_provider_zip}~")
    edi.append(f"REF*EI*{billing_provider_tax_id}~")
    
    # Process each row in CSV
    for idx, row in df.iterrows():
        hl_count = idx + 2
        
        # Loop 2000B - Subscriber Hierarchical Level
        edi.append(f"HL*{hl_count}*{idx+1}*22*0~")
        
        # Subscriber Information
        subscriber_last = row.get('subscriber_last_name', 'DOE')
        subscriber_first = row.get('subscriber_first_name', 'JOHN')
        member_id = row.get('member_id', '000000000')
        
        edi.append(f"NM1*IL*1*{subscriber_last}*{subscriber_first}****MI*{member_id}~")
        
        # Subscriber address (optional)
        if row.get('subscriber_address'):
            edi.append(f"N3*{row.get('subscriber_address')}~")
        if row.get('subscriber_city'):
            city = row.get('subscriber_city', 'CITY')
            state = row.get('subscriber_state', 'ST')
            zipcode = row.get('subscriber_zip', '12345')
            edi.append(f"N4*{city}*{state}*{zipcode}~")
        
        # Loop 2000C - Patient Hierarchical Level (same as subscriber for MVP)
        patient_hl = hl_count + 1
        edi.append(f"HL*{patient_hl}*{hl_count}*23*0~")
        edi.append(f"NM1*QC*1*{subscriber_last}*{subscriber_first}****MI*{member_id}~")
        
        if row.get('patient_address'):
            edi.append(f"N3*{row.get('patient_address')}~")
        
        # Loop 2400 - Service Lines
        service_date = row.get('service_date', now.strftime('%Y%m%d'))
        diagnosis = row.get('diagnosis_code', '999.9')
        procedure = row.get('procedure_code', '99213')
        modifier = row.get('modifier', '')
        quantity = row.get('quantity', '1')
        charged_amount = row.get('charged_amount', '100.00')
        
        # DTP - Service Date
        edi.append(f"DTP*431*D8*{service_date}~")
        
        # HI - Diagnosis (ICD-10)
        edi.append(f"HI*BK*{diagnosis}~")
        
        # LX - Service Line Number
        line_num = idx + 1
        edi.append(f"LX*{line_num}~")
        
        # SVD - Service Line Adjudication (corrected format)
        # SVD* payer responsibility amount *HCPCS*service code**units
        if modifier:
            procedure_code = f"{procedure}:{modifier}"
        else:
            procedure_code = procedure
        edi.append(f"SVD* {charged_amount}*HC*{procedure_code}***{quantity}~")
        
        # DTP - Line Item Adjudication Date
        edi.append(f"DTP*573*D8*{now.strftime('%Y%m%d')}~")
    
    # SE - Transaction Set Trailer
    seg_count = len(edi) - 2 + 1  # Excluding ISA, GS, counting from ST
    edi.append(f"SE*{seg_count}*{st_control_num}~")
    
    # GE - Functional Group Trailer
    edi.append(f"GE*1*{gs_control_num}~")
    
    # IEA - Interchange Control Trailer
    edi.append(f"IEA*1*{isa_control_num}~")
    
    return '\n'.join(edi)


@app.get("/")
def root():
    return {"message": "837 Converter API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload CSV file and return column names for mapping."""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    content = await file.read()
    
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    file_id = str(uuid.uuid4())
    
    # Store the CSV data temporarily
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    generated_files[file_id] = csv_buffer.getvalue()
    
    # Replace NaN values with None for JSON serialization
    df_preview = df.head(3).fillna('').to_dict(orient='records')
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "columns": list(df.columns),
        "row_count": len(df),
        "preview": df_preview
    }


@app.post("/convert")
async def convert_to_edi(request: ConvertRequest):
    """Convert uploaded CSV to 837P EDI format."""
    
    if request.file_id not in generated_files:
        raise HTTPException(status_code=404, detail="File not found. Please upload again.")
    
    # Read the CSV
    df = pd.read_csv(io.StringIO(generated_files[request.file_id]))
    
    # Use custom mapping or default
    mapping = request.mapping.mappings if request.mapping else DEFAULT_MAPPING
    
    try:
        edi_content = generate_837P(df, mapping)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate EDI: {str(e)}")
    
    # Store the EDI file
    edi_file_id = str(uuid.uuid4())
    generated_files[edi_file_id] = edi_content
    
    return {
        "file_id": edi_file_id,
        "status": "success",
        "segments": len(edi_content.split('~')),
        "claims_count": len(df)
    }


@app.get("/download/{file_id}")
async def download_edi(file_id: str):
    """Download the generated EDI file."""
    
    if file_id not in generated_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Create a temp file
    temp_path = f"/tmp/{file_id}.edi"
    with open(temp_path, 'w') as f:
        f.write(generated_files[file_id])
    
    return FileResponse(
        temp_path,
        media_type="application/edifact",
        filename=f"claim_{file_id[:8]}.edi"
    )


@app.get("/preview/{file_id}")
async def preview_edi(file_id: str):
    """Preview the EDI content."""
    
    if file_id not in generated_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    content = generated_files[file_id]
    lines = content.split('\n')[:50]  # First 50 segments
    
    return PlainTextResponse(content='\n'.join(lines))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
