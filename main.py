# main.py - Complete Enhanced Policy Management System API
import os
import json
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import our enhanced modules
from database import database, user_model, endorsement_model
from file_processor import file_processor

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Policy Management System",
    description="Corporate Policy & Endorsement Management with Multi-Combination Support",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Simple session storage
active_sessions = {}

# Pydantic Models
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict] = None
    session_token: Optional[str] = None

class EndorsementCreate(BaseModel):
    policy_number: str
    endorsement_type: str
    endorsement_version: Optional[str] = None
    endorsement_validity: Optional[str] = None
    concepto_id: Optional[str] = None
    combination_number: int = 1
    combination_id: Optional[str] = None
    total_combinations: int = 1
    file_group_id: Optional[str] = None
    status: str = "In Review"
    spanish_fields: Dict[str, Any] = {}
    json_data: Dict[str, Any] = {}

class EndorsementUpdate(BaseModel):
    policy_number: Optional[str] = None
    endorsement_type: Optional[str] = None
    endorsement_version: Optional[str] = None
    endorsement_validity: Optional[str] = None
    concepto_id: Optional[str] = None
    status: Optional[str] = None
    spanish_fields: Optional[Dict[str, Any]] = None
    json_data: Optional[Dict[str, Any]] = None

# Authentication Dependencies
def get_current_user(request: Request) -> Dict:
    """Get current user from session"""
    session_token = request.cookies.get("session_token")
    
    if not session_token or session_token not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    session_data = active_sessions[session_token]
    
    # Check if session is expired (24 hours)
    if datetime.now() > session_data["expires_at"]:
        del active_sessions[session_token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    return session_data["user"]

def optional_current_user(request: Request) -> Optional[Dict]:
    """Get current user without raising exception if not authenticated"""
    try:
        return get_current_user(request)
    except HTTPException:
        return None

def extract_core_fields_from_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract core fields from JSON data"""
    core_field_mappings = {
        'número de póliza': 'policy_number',
        'numero de poliza': 'policy_number',
        'policy_number': 'policy_number',
        'poliza': 'policy_number',
        'póliza': 'policy_number',
        
        'nombre del endoso': 'endorsement_type',
        'tipo de endoso': 'endorsement_type',
        'endorsement_type': 'endorsement_type',
        'endoso': 'endorsement_type',
        
        'versión del endoso inicial': 'endorsement_version',
        'version del endoso inicial': 'endorsement_version',
        'versión del endoso': 'endorsement_version',
        'version del endoso': 'endorsement_version',
        'endorsement_version': 'endorsement_version',
        'version': 'endorsement_version',
        'versión': 'endorsement_version'
    }
    
    core_fields = {}
    
    for spanish_field, english_field in core_field_mappings.items():
        for field_name, field_value in json_data.items():
            if spanish_field.lower() == field_name.lower().strip():
                if english_field == 'policy_number':
                    # Extract policy number
                    if field_value and str(field_value).strip():
                        cleaned_value = str(field_value).strip()
                        numbers = re.findall(r'\d+', cleaned_value)
                        if numbers:
                            core_fields[english_field] = numbers[0]
                        else:
                            core_fields[english_field] = cleaned_value
                else:
                    core_fields[english_field] = str(field_value).strip() if field_value else None
                break
    
    return core_fields

# Main Application Route
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main application page"""
    user = optional_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

# Authentication Routes
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and create session"""
    try:
        user = user_model.authenticate(request.username, request.password)
        
        if not user:
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
        
        # Create session
        session_token = str(uuid.uuid4())
        session_data = {
            "user": user,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=24)
        }
        active_sessions[session_token] = session_data
        
        return LoginResponse(
            success=True,
            message="Login successful",
            user=user,
            session_token=session_token
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user and invalidate session"""
    session_token = request.cookies.get("session_token")
    
    if session_token and session_token in active_sessions:
        del active_sessions[session_token]
    
    return {"success": True, "message": "Logged out successfully"}

@app.get("/api/auth/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    return {"success": True, "user": current_user}

# Enhanced Endorsement Routes
@app.get("/api/endorsements")
async def get_endorsements(
    status: Optional[str] = None,
    endorsement_type: Optional[str] = None,
    policy_number: Optional[str] = None,
    search_term: Optional[str] = None,
    grouped: bool = True,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "DESC",
    current_user: Dict = Depends(get_current_user)
):
    """Get endorsements with enhanced multi-combination support"""
    try:
        if search_term:
            endorsements = endorsement_model.search_endorsements(search_term)
        elif grouped:
            endorsements = endorsement_model.get_endorsements_grouped(
                status=status,
                endorsement_type=endorsement_type,
                policy_number=policy_number,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order
            )
        else:
            endorsements = endorsement_model.get_endorsements(
                status=status,
                endorsement_type=endorsement_type,
                policy_number=policy_number,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order
            )
        
        return {
            "success": True,
            "data": endorsements,
            "count": len(endorsements),
            "grouped": grouped
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch endorsements: {str(e)}"
        )

@app.get("/api/endorsements/{endorsement_id}")
async def get_endorsement(
    endorsement_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Get specific endorsement by ID"""
    try:
        endorsement = endorsement_model.get_endorsement_by_id(endorsement_id)
        
        if not endorsement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Endorsement not found"
            )
        
        return {
            "success": True,
            "data": endorsement
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch endorsement: {str(e)}"
        )

@app.get("/api/endorsements/{policy_number}/{endorsement_type}/combinations")
async def get_endorsement_combinations(
    policy_number: str,
    endorsement_type: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get all combinations for a specific policy and endorsement type"""
    try:
        combinations = endorsement_model.get_endorsement_combinations(policy_number, endorsement_type)
        
        if not combinations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No combinations found for this endorsement"
            )
        
        return {
            "success": True,
            "data": combinations,
            "count": len(combinations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch endorsement combinations: {str(e)}"
        )

@app.post("/api/endorsements")
async def create_endorsement(
    endorsement_data: EndorsementCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new endorsement"""
    try:
        endorsement_record = {
            'policy_number': endorsement_data.policy_number,
            'endorsement_type': endorsement_data.endorsement_type,
            'endorsement_version': endorsement_data.endorsement_version,
            'endorsement_validity': endorsement_data.endorsement_validity,
            'concepto_id': endorsement_data.concepto_id,
            'combination_number': endorsement_data.combination_number,
            'combination_id': endorsement_data.combination_id,
            'total_combinations': endorsement_data.total_combinations,
            'file_group_id': endorsement_data.file_group_id,
            'status': endorsement_data.status,
            'spanish_fields': endorsement_data.spanish_fields,
            'json_data': endorsement_data.json_data,
            'uploaded_by': current_user['username']
        }
        
        endorsement_id = endorsement_model.create_endorsement(endorsement_record)
        created_endorsement = endorsement_model.get_endorsement_by_id(endorsement_id)
        
        return {
            "success": True,
            "message": "Endorsement created successfully",
            "data": created_endorsement
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create endorsement: {str(e)}"
        )

@app.put("/api/endorsements/{endorsement_id}")
async def update_endorsement(
    endorsement_id: int,
    endorsement_data: EndorsementUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Enhanced update endorsement with comprehensive field editing"""
    try:
        # Get existing endorsement
        existing = endorsement_model.get_endorsement_by_id(endorsement_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Endorsement not found"
            )
        
        # Prepare update data - only include fields that were provided
        update_data = {}
        for field, value in endorsement_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        # If no data to update
        if not update_data:
            return {
                "success": True, 
                "message": "No changes to update",
                "data": existing
            }
        
        # Update the endorsement
        success = endorsement_model.update_endorsement(
            endorsement_id,
            update_data,
            current_user["username"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update endorsement"
            )
        
        # Get updated endorsement
        updated_endorsement = endorsement_model.get_endorsement_by_id(endorsement_id)
        
        return {
            "success": True,
            "message": f"Endorsement updated successfully by {current_user['username']}",
            "data": updated_endorsement
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update endorsement: {str(e)}"
        )

@app.delete("/api/endorsements/{endorsement_id}")
async def delete_endorsement(
    endorsement_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """Delete an endorsement"""
    try:
        # Check if endorsement exists
        existing = endorsement_model.get_endorsement_by_id(endorsement_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Endorsement not found"
            )
        
        # Delete the endorsement
        success = endorsement_model.delete_endorsement(endorsement_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete endorsement"
            )
        
        return {
            "success": True,
            "message": f"Endorsement deleted successfully by {current_user['username']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete endorsement: {str(e)}"
        )

@app.delete("/api/endorsements/{policy_number}/{endorsement_type}/group")
async def delete_endorsement_group(
    policy_number: str,
    endorsement_type: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete entire endorsement group (all combinations) for a policy and type"""
    try:
        print(f"🗑️ Group deletion request from {current_user['username']}")
        print(f"   Policy: {policy_number}, Type: {endorsement_type}")
        
        # Get group info before deletion
        group_info = endorsement_model.get_endorsement_group_info(policy_number, endorsement_type)
        
        if not group_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Endorsement group not found"
            )
        
        print(f"   Found {group_info['total_combinations']} combinations to delete")
        
        # Delete the entire group
        success = endorsement_model.delete_endorsement_group(policy_number, endorsement_type)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete endorsement group"
            )
        
        return {
            "success": True,
            "message": f"Deleted entire endorsement group: {group_info['total_combinations']} combinations removed",
            "data": {
                "deleted_combinations": group_info['total_combinations'],
                "policy_number": policy_number,
                "endorsement_type": endorsement_type,
                "deleted_by": current_user['username'],
                "deleted_at": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Group deletion error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete endorsement group: {str(e)}"
        )

@app.put("/api/endorsements/bulk/status")
async def bulk_update_status(
    request_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Bulk update status for multiple endorsements"""
    try:
        endorsement_ids = request_data.get('endorsement_ids', [])
        new_status = request_data.get('status')
        
        if not endorsement_ids or not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="endorsement_ids and status are required"
            )
        
        if new_status not in ['Approved', 'Rejected', 'In Review']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status value"
            )
        
        updated_count = 0
        for endorsement_id in endorsement_ids:
            existing = endorsement_model.get_endorsement_by_id(endorsement_id)
            if existing:
                update_data = {'status': new_status}
                
                if endorsement_model.update_endorsement(endorsement_id, update_data, current_user["username"]):
                    updated_count += 1
        
        return {
            "success": True,
            "message": f"Updated {updated_count} endorsements to {new_status}",
            "updated_count": updated_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update: {str(e)}"
        )

# File Upload Routes
@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """Upload and process endorsement file"""
    try:
        print(f"📤 File Upload from user: {current_user.get('username')}")
        print(f"📄 File: {file.filename}, Size: {file.size}")
        
        # Validate file
        file_content = await file.read()
        is_valid, message = file_processor.validate_file(file.filename, len(file_content))
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Save file
        file_path = file_processor.save_uploaded_file(file_content, file.filename)
        
        # Process file
        processed_data = file_processor.process_file(file_path, file.filename)
        
        # Create endorsements from processed data
        created_endorsements = []
        file_group_id = str(uuid.uuid4())
        
        for endorsement_data in processed_data.get('endorsements', []):
            core_fields = endorsement_data.get('core_fields', {})
            
            # More lenient check for creating endorsements
            if core_fields.get('policy_number') or core_fields.get('endorsement_type') or len(endorsement_data.get('all_fields', {})) >= 3:
                endorsement_record = {
                    'policy_number': str(core_fields.get('policy_number', 'unknown')),
                    'endorsement_type': core_fields.get('endorsement_type', 'EXCEL_UPLOAD'),
                    'endorsement_version': core_fields.get('endorsement_version'),
                    'endorsement_validity': core_fields.get('endorsement_validity'),
                    'concepto_id': core_fields.get('concepto_id'),
                    'combination_number': endorsement_data.get('combination_number', 1),
                    'combination_id': endorsement_data.get('combination_id'),
                    'total_combinations': len(processed_data.get('endorsements', [])),
                    'file_group_id': file_group_id,
                    'status': 'In Review',
                    'spanish_fields': endorsement_data.get('spanish_fields', {}),
                    'json_data': endorsement_data.get('all_fields', {}),
                    'original_filename': file.filename,
                    'file_path': file_path,
                    'uploaded_by': current_user['username']
                }
                
                endorsement_id = endorsement_model.create_endorsement(endorsement_record)
                created_endorsement = endorsement_model.get_endorsement_by_id(endorsement_id)
                created_endorsements.append(created_endorsement)
        
        return {
            "success": True,
            "message": f"File processed successfully. Created {len(created_endorsements)} endorsement combinations.",
            "data": {
                "file_info": {
                    "filename": file.filename,
                    "size": len(file_content),
                    "type": processed_data.get('file_type')
                },
                "processing_info": processed_data.get('metadata', {}),
                "endorsements": created_endorsements,
                "file_group_id": file_group_id,
                "combinations_created": len(created_endorsements)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ File Upload Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )

@app.post("/api/files/upload-json")
async def upload_json_text(
    request: Request,
    json_text: str = Form(...),
    current_user: Dict = Depends(get_current_user)
):
    """Upload JSON text directly - FIXED VERSION"""
    try:
        print(f"📤 JSON Upload Request from user: {current_user.get('username')}")
        print(f"📄 JSON Text Length: {len(json_text)} characters")
        print(f"📄 JSON Text Preview: {json_text[:200]}...")
        
        # Parse JSON
        try:
            json_data = json.loads(json_text)
            print(f"✅ JSON parsed successfully: {type(json_data)}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format: {str(e)}"
            )
        
        # Create temporary file for processing
        temp_filename = f"temp_json_{uuid.uuid4()}.json"
        temp_file_path = Path("uploads") / temp_filename
        
        # Ensure uploads directory exists
        Path("uploads").mkdir(exist_ok=True)
        
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Temporary JSON file created: {temp_file_path}")
        
        # Process JSON directly
        created_endorsements = []
        file_group_id = str(uuid.uuid4())
        
        # Handle single object or array
        if isinstance(json_data, dict):
            # Single endorsement object
            endorsements_to_process = [json_data]
        elif isinstance(json_data, list):
            # Array of endorsements
            endorsements_to_process = json_data
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON must be an object or array of objects"
            )
        
        print(f"📊 Processing {len(endorsements_to_process)} JSON endorsement(s)")
        
        for idx, json_endorsement in enumerate(endorsements_to_process):
            if not isinstance(json_endorsement, dict):
                print(f"⚠️ Skipping non-object item at index {idx}")
                continue
            
            # Extract core fields using the function
            core_fields = extract_core_fields_from_json(json_endorsement)
            print(f"📋 Extracted core fields for item {idx}: {core_fields}")
            
            # Create endorsement if we have some data
            if core_fields.get('policy_number') or core_fields.get('endorsement_type') or len(json_endorsement) >= 5:
                endorsement_record = {
                    'policy_number': str(core_fields.get('policy_number', 'unknown')),
                    'endorsement_type': core_fields.get('endorsement_type', 'JSON_UPLOAD'),
                    'endorsement_version': core_fields.get('endorsement_version'),
                    'endorsement_validity': core_fields.get('endorsement_validity'),
                    'concepto_id': core_fields.get('concepto_id'),
                    'combination_number': idx + 1,
                    'combination_id': f"json_combo_{idx + 1}",
                    'total_combinations': len(endorsements_to_process),
                    'file_group_id': file_group_id,
                    'status': 'In Review',
                    'spanish_fields': json_endorsement,  # Keep original JSON as Spanish fields
                    'json_data': json_endorsement,       # Same data for json_data
                    'original_filename': 'json_upload.json',
                    'file_path': str(temp_file_path),
                    'uploaded_by': current_user['username']
                }
                
                print(f"💾 Creating endorsement record for item {idx}")
                endorsement_id = endorsement_model.create_endorsement(endorsement_record)
                created_endorsement = endorsement_model.get_endorsement_by_id(endorsement_id)
                created_endorsements.append(created_endorsement)
                print(f"✅ Created endorsement {endorsement_id} for item {idx}")
            else:
                print(f"⚠️ Skipping item {idx} - insufficient data")
        
        print(f"✅ JSON processing complete: {len(created_endorsements)} endorsements created")
        
        return {
            "success": True,
            "message": f"JSON processed successfully. Created {len(created_endorsements)} endorsement combinations.",
            "data": {
                "processing_info": {
                    "items_processed": len(endorsements_to_process),
                    "endorsements_created": len(created_endorsements),
                    "processed_at": datetime.now().isoformat()
                },
                "endorsements": created_endorsements,
                "file_group_id": file_group_id,
                "combinations_created": len(created_endorsements)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ JSON Upload Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"JSON upload failed: {str(e)}"
        )

# Search Helper Routes
@app.get("/api/search/endorsement-types")
async def get_endorsement_types(current_user: Dict = Depends(get_current_user)):
    """Get all unique endorsement types for dropdown"""
    try:
        types = endorsement_model.get_unique_endorsement_types()
        return {"success": True, "data": types}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch endorsement types: {str(e)}"
        )

@app.get("/api/search/policy-numbers")
async def get_policy_numbers(current_user: Dict = Depends(get_current_user)):
    """Get all unique policy numbers for dropdown"""
    try:
        numbers = endorsement_model.get_unique_policy_numbers()
        return {"success": True, "data": numbers}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch policy numbers: {str(e)}"
        )

@app.get("/api/search/status-options")
async def get_status_options():
    """Get available status options"""
    return {
        "success": True,
        "data": ["Approved", "Rejected", "In Review"]
    }

@app.get("/api/statistics")
async def get_statistics(current_user: Dict = Depends(get_current_user)):
    """Get detailed statistics for dashboard"""
    try:
        all_endorsements = endorsement_model.get_endorsements(limit=1000)
        
        stats = {
            'total_endorsements': len(all_endorsements),
            'approved_count': len([e for e in all_endorsements if e.get('status') == 'Approved']),
            'rejected_count': len([e for e in all_endorsements if e.get('status') == 'Rejected']),
            'in_review_count': len([e for e in all_endorsements if e.get('status') == 'In Review']),
            'recent_uploads': len([e for e in all_endorsements if e.get('created_at')]),
            'endorsement_types_count': len(endorsement_model.get_unique_endorsement_types()),
            'policy_numbers_count': len(endorsement_model.get_unique_policy_numbers())
        }
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

@app.get("/api/system/time")
async def get_system_time():
    """Get current system time information"""
    from datetime import datetime
    import time
    import platform
    
    current_local = datetime.now()
    current_utc = datetime.utcnow()
    
    return {
        "success": True,
        "data": {
            "local_time": current_local.strftime('%Y-%m-%d %H:%M:%S'),
            "utc_time": current_utc.strftime('%Y-%m-%d %H:%M:%S'),
            "timezone": str(time.tzname),
            "platform": platform.system(),
            "offset_hours": (current_local - current_utc).total_seconds() / 3600,
            "formatted_local": current_local.strftime('%A, %B %d, %Y at %I:%M:%S %p'),
            "iso_format": current_local.isoformat(),
            "windows_time": current_local.strftime('%Y-%m-%d %H:%M:%S') if platform.system() == 'Windows' else 'N/A'
        }
    }

# Health Check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": ["multi_combinations", "spanish_fields", "json_upload", "edit_mode"],
        "current_time_utc": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        "active_sessions": len(active_sessions)
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Endpoint not found"}
        )
    return HTMLResponse(content="<h1>404 - Page Not Found</h1>", status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"}
    )

if __name__ == "__main__":
    print("🚀 Starting enhanced Policy Management System server...")
    print(f"📅 Server started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API Documentation at: http://localhost:8000/api/docs")
    print("👤 Default login - Username: admin, Password: admin123")
    print("👤 Demo login - Username: demo, Password: demo123")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
