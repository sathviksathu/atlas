from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import polars as pl
from fraud_monitoring_home_page import fraud_monitoring_home_page
from fraud_transaction_monitor_service import FraudTransactionMonitorService
from fraud_transaction_rules import ( 
    SuspiciousFrequencyRule, 
    UnusualTimeRule,
    DuplicateTransactionRule,
    SuspiciousMerchantRule,
    MerchantVelocityRule
)

app = FastAPI(title="Fraud Transaction Monitor", version="1.0.0")

# Initialize the fraud monitor service with rules
fraud_monitor = FraudTransactionMonitorService()
fraud_monitor.add_rule(SuspiciousMerchantRule())
fraud_monitor.add_rule(MerchantVelocityRule())
fraud_monitor.add_rule(UnusualTimeRule(start_hour=1, end_hour=4))
fraud_monitor.add_rule(DuplicateTransactionRule())
fraud_monitor.add_rule(SuspiciousFrequencyRule())


class FilePathRequest(BaseModel):
    file_path: str
    page: int = 1
    page_size: int = 15

class PaginationInfo(BaseModel):
    current_page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

class FraudDetectionResponse(BaseModel):
    total_transactions: int
    fraudulent_transactions: int
    fraud_percentage: float
    fraud_data: List[Dict[str, Any]]
    rules_applied: List[str]
    fraud_code_explanations: Dict[str, str]
    pagination: PaginationInfo

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    """Serve the fraud monitoring UI page"""
    return fraud_monitoring_home_page

@app.post("/analyze-fraud", response_model=FraudDetectionResponse)
async def analyze_fraud(request: FilePathRequest):
    """Analyze CSV file for fraudulent transactions"""
    try:
        # Validate file path
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=400, detail="File not found")
        
        if not request.file_path.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Process the file
        result = fraud_monitor.analyze_transactions(request.file_path, request.page, request.page_size)
        
        return FraudDetectionResponse(
            total_transactions=result['total_transactions'],
            fraudulent_transactions=result['fraudulent_transactions'],
            fraud_percentage=result['fraud_percentage'],
            fraud_data=result['fraud_data'],
            rules_applied=result['rules_applied'],
            fraud_code_explanations=result['fraud_code_explanations'],
            pagination=result['pagination']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

if __name__ == "__main__":
    #import logging
    #logging.basicConfig(level=logging.INFO)
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
