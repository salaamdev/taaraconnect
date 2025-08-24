from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import json
import plotly.graph_objs as go
import plotly.utils

from app.database import get_db, DataUsageRecord, ApiLog, create_tables
from app.data_collector import run_data_collection
from app.timezone_utils import utc_to_local, format_local_time, get_timezone_info

# Create FastAPI app
app = FastAPI(title="Taara Internet Monitor", version="1.0.0")

# Create database tables
create_tables()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add custom template filters
def local_time_filter(dt):
    """Jinja2 filter to convert UTC time to local time"""
    return format_local_time(dt)

templates.env.filters['local_time'] = local_time_filter

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard"""
    
    # Get latest data for each plan
    latest_records = db.query(DataUsageRecord).filter(
        DataUsageRecord.is_active == True
    ).order_by(desc(DataUsageRecord.timestamp)).limit(10).all()
    
    # Get usage over time for charts
    usage_history = db.query(DataUsageRecord).filter(
        DataUsageRecord.is_active == True,
        DataUsageRecord.timestamp >= datetime.now() - timedelta(days=30)
    ).order_by(DataUsageRecord.timestamp).all()
    
    # Calculate statistics
    stats = {
        "current_balance": 0,
        "total_usage_gb": 0,
        "days_remaining": 0,
        "usage_rate_gb_per_day": 0
    }
    
    if latest_records:
        latest = latest_records[0]
        stats["current_balance"] = latest.remaining_balance_gb
        stats["total_usage_gb"] = latest.total_data_usage_bytes / (1024**3)
        stats["days_remaining"] = latest.expires_in_days
        
        if stats["days_remaining"] > 0:
            used_gb = 1000 - stats["current_balance"]  # Assuming 1TB plan
            days_elapsed = 30 - stats["days_remaining"]  # Assuming 30-day plan
            if days_elapsed > 0:
                stats["usage_rate_gb_per_day"] = used_gb / days_elapsed
    
    # Create charts
    charts = create_charts(usage_history)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "latest_records": latest_records,
        "stats": stats,
        "charts": charts
    })

@app.get("/api/data")
async def get_latest_data(db: Session = Depends(get_db)):
    """API endpoint to get latest data"""
    records = db.query(DataUsageRecord).filter(
        DataUsageRecord.is_active == True
    ).order_by(desc(DataUsageRecord.timestamp)).limit(5).all()
    
    return [
        {
            "id": record.id,
            "timestamp": record.timestamp.isoformat(),
            "timestamp_local": format_local_time(record.timestamp),
            "plan_name": record.plan_name,
            "remaining_balance_gb": record.remaining_balance_gb,
            "expires_in_days": record.expires_in_days,
            "is_active": record.is_active
        }
        for record in records
    ]

@app.get("/api/history")
async def get_usage_history(days: int = 7, db: Session = Depends(get_db)):
    """Get usage history for specified number of days"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    records = db.query(DataUsageRecord).filter(
        DataUsageRecord.timestamp >= cutoff_date,
        DataUsageRecord.is_active == True
    ).order_by(DataUsageRecord.timestamp).all()
    
    return [
        {
            "timestamp": record.timestamp.isoformat(),
            "remaining_balance_gb": record.remaining_balance_gb,
            "plan_name": record.plan_name
        }
        for record in records
    ]

@app.post("/api/collect")
async def trigger_collection():
    """Manually trigger data collection"""
    try:
        success = await run_data_collection()
        if success:
            return {"status": "success", "message": "Data collection completed"}
        else:
            return {"status": "error", "message": "Data collection failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timezone")
async def get_timezone_info_endpoint():
    """Get timezone information"""
    return get_timezone_info()

@app.get("/api/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Get usage statistics"""
    
    # Latest record
    latest = db.query(DataUsageRecord).filter(
        DataUsageRecord.is_active == True
    ).order_by(desc(DataUsageRecord.timestamp)).first()
    
    if not latest:
        return {"error": "No data available"}
    
    # Usage over last 7 days
    week_ago = datetime.now() - timedelta(days=7)
    week_records = db.query(DataUsageRecord).filter(
        DataUsageRecord.timestamp >= week_ago,
        DataUsageRecord.is_active == True
    ).order_by(DataUsageRecord.timestamp).all()
    
    # Calculate daily usage
    daily_usage = []
    if len(week_records) > 1:
        for i in range(1, len(week_records)):
            prev_balance = week_records[i-1].remaining_balance_gb
            curr_balance = week_records[i].remaining_balance_gb
            usage = prev_balance - curr_balance
            if usage > 0:  # Only count positive usage
                daily_usage.append(usage)
    
    avg_daily_usage = sum(daily_usage) / len(daily_usage) if daily_usage else 0
    
    # Predict when data will run out
    days_remaining = latest.expires_in_days
    if avg_daily_usage > 0:
        predicted_days = latest.remaining_balance_gb / avg_daily_usage
        days_remaining = min(days_remaining, predicted_days)
    
    return {
        "current_balance_gb": latest.remaining_balance_gb,
        "expires_in_days": latest.expires_in_days,
        "avg_daily_usage_gb": avg_daily_usage,
        "predicted_days_remaining": days_remaining,
        "plan_name": latest.plan_name,
        "last_updated": latest.timestamp.isoformat()
    }

def create_charts(usage_history):
    """Create Plotly charts for the dashboard"""
    if not usage_history:
        return {"balance_chart": "", "usage_chart": ""}
    
    # Prepare data
    timestamps = [record.timestamp for record in usage_history]
    balances = [record.remaining_balance_gb for record in usage_history]
    
    # Balance over time chart
    balance_fig = go.Figure()
    balance_fig.add_trace(go.Scatter(
        x=timestamps,
        y=balances,
        mode='lines+markers',
        name='Remaining Balance (GB)',
        line=dict(color='#007bff', width=3),
        marker=dict(size=6)
    ))
    
    balance_fig.update_layout(
        title='Data Balance Over Time',
        xaxis_title='Date',
        yaxis_title='Remaining Balance (GB)',
        template='plotly_white',
        height=300
    )
    
    # Usage rate chart (calculated from balance changes)
    usage_rates = []
    usage_dates = []
    
    for i in range(1, len(usage_history)):
        prev_balance = usage_history[i-1].remaining_balance_gb
        curr_balance = usage_history[i].remaining_balance_gb
        usage = prev_balance - curr_balance
        
        if usage >= 0:  # Only show positive usage
            usage_rates.append(usage)
            usage_dates.append(usage_history[i].timestamp)
    
    usage_fig = go.Figure()
    if usage_rates:
        usage_fig.add_trace(go.Bar(
            x=usage_dates,
            y=usage_rates,
            name='Data Usage (GB)',
            marker_color='#28a745'
        ))
    
    usage_fig.update_layout(
        title='Daily Data Usage',
        xaxis_title='Date',
        yaxis_title='Usage (GB)',
        template='plotly_white',
        height=300
    )
    
    return {
        "balance_chart": json.dumps(balance_fig, cls=plotly.utils.PlotlyJSONEncoder),
        "usage_chart": json.dumps(usage_fig, cls=plotly.utils.PlotlyJSONEncoder)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
