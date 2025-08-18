# main.py - Complete FastAPI Backend Application
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

# Import our custom modules
from database import database, user_model, endorsement_model
from file_processor import file_processor

# Initialize FastAPI app
app = FastAPI(
    title="Policy Management System",
    description="Corporate Policy & Endorsement Management Application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
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

# Simple session storage (in production, use Redis or database)
active_sessions = {}

# Pydantic Models for API
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
    status: str = "In Review"
    json_data: Dict[str, Any] = {}

class EndorsementUpdate(BaseModel):
    policy_number: Optional[str] = None
    endorsement_type: Optional[str] = None
    endorsement_version: Optional[str] = None
    endorsement_validity: Optional[str] = None
    concepto_id: Optional[str] = None
    status: Optional[str] = None
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

# API Routes

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

# Endorsement Routes
@app.get("/api/endorsements")
async def get_endorsements(
    status: Optional[str] = None,
    endorsement_type: Optional[str] = None,
    policy_number: Optional[str] = None,
    search_term: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "DESC",
    current_user: Dict = Depends(get_current_user)
):
    """Get endorsements with filters"""
    try:
        if search_term:
            # Use search functionality
            endorsements = endorsement_model.search_endorsements(search_term)
        else:
            # Use filtered query
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
            "count": len(endorsements)
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

@app.put("/api/endorsements/{endorsement_id}")
async def update_endorsement(
    endorsement_id: int,
    endorsement_data: EndorsementUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update endorsement"""
    try:
        # Get existing endorsement
        existing = endorsement_model.get_endorsement_by_id(endorsement_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Endorsement not found"
            )
        
        # Prepare update data
        update_data = {}
        for field, value in endorsement_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        # If no data to update
        if not update_data:
            return {"success": True, "message": "No changes to update"}
        
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
            "message": "Endorsement updated successfully",
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
    """Delete endorsement"""
    try:
        success = endorsement_model.delete_endorsement(endorsement_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Endorsement not found"
            )
        
        return {
            "success": True,
            "message": "Endorsement deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete endorsement: {str(e)}"
        )

# File Upload Routes
@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """Upload and process endorsement file"""
    try:
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
        
        for endorsement_data in processed_data.get('endorsements', []):
            # Prepare endorsement for database
            core_fields = endorsement_data.get('core_fields', {})
            
            # Skip if no core fields found
            if not any(core_fields.values()):
                continue
            
            endorsement_record = {
                'policy_number': core_fields.get('policy_number'),
                'endorsement_type': core_fields.get('endorsement_type'),
                'endorsement_version': core_fields.get('endorsement_version'),
                'endorsement_validity': core_fields.get('endorsement_validity'),
                'concepto_id': core_fields.get('concepto_id'),
                'status': 'In Review',
                'json_data': endorsement_data.get('all_fields', {}),
                'original_filename': file.filename,
                'file_path': file_path,
                'uploaded_by': current_user['username']
            }
            
            # Create endorsement
            endorsement_id = endorsement_model.create_endorsement(endorsement_record)
            
            # Get the created endorsement
            created_endorsement = endorsement_model.get_endorsement_by_id(endorsement_id)
            created_endorsements.append(created_endorsement)
        
        return {
            "success": True,
            "message": f"File processed successfully. Created {len(created_endorsements)} endorsements.",
            "data": {
                "file_info": {
                    "filename": file.filename,
                    "size": len(file_content),
                    "type": processed_data.get('file_type')
                },
                "processing_info": processed_data.get('metadata', {}),
                "endorsements": created_endorsements
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
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

# File Download Route
@app.get("/api/files/{filename}")
async def download_file(
    filename: str,
    current_user: Dict = Depends(get_current_user)
):
    """Download original uploaded file"""
    try:
        file_path = Path("uploads") / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File download failed: {str(e)}"
        )

# Health Check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Cleanup old sessions periodically (basic implementation)
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("🚀 Policy Management System starting up...")
    print("📊 Database initialized")
    print("📁 File processor ready")
    print("🌐 Server ready at http://localhost:8000")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Policy Management System shutting down...")
    # Clean up sessions
    active_sessions.clear()

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Endpoint not found"}
        )
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"}
    )

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )