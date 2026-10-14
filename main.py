from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from router import process_settlement_request, load_fx_graph
from database import get_db_connection
import numpy as np # <-- Adding Data Analytics

app = FastAPI(
    title="Intra-African Liquidity & FX Settlement Engine",
    description="A PAPSS-inspired high-performance cross-border payment routing API.",
    version="1.0.0"
)

class SettlementRequest(BaseModel):
    source_currency: str = Field(..., example="NGN", min_length=3, max_length=3)
    target_currency: str = Field(..., example="GHS", min_length=3, max_length=3)
    amount: float = Field(..., gt=0, description="The transfer volume in source currency units")

@app.post("/api/v1/settle")
def submit_settlement(request: SettlementRequest):
    src = request.source_currency.upper()
    tgt = request.target_currency.upper()
    result = process_settlement_request(src, tgt, request.amount)
    if result["status"] == "FAILED_NO_ROUTE":
        raise HTTPException(status_code=404, detail=result["reason"])
    return result

@app.get("/api/v1/reserves")
def get_reserves():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT currency_code, bank_name, available_liquidity, min_alert_threshold FROM central_bank_reserves")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# 🔥 NEW DATA SCIENCE CORNER: Predictive Stress Metrics
@app.get("/api/v1/analytics/stress-index", summary="Calculate predictive liquidity stress vulnerability scores")
def get_liquidity_stress_index():
    """
    Uses numpy statistical metrics to simulate historical volatility coefficients 
    and output a real-time Liquidity Vulnerability Score (LVS) for each bank corridor.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT currency_code, available_liquidity, min_alert_threshold FROM central_bank_reserves")
    pools = cursor.fetchall()
    conn.close()
    
    stress_report = []
    
    for pool in pools:
        currency = pool['currency_code']
        liquidity = pool['available_liquidity']
        threshold = pool['min_alert_threshold']
        
        # Simulating rolling 30-day transaction volume variance using NumPy
        # In a full system, you would read from the settlement_transactions history table
        np.random.seed(seed=ord(currency[-1])) # Consistent mock variance per node
        historical_sim_demands = np.random.normal(loc=threshold * 1.5, scale=threshold * 0.4, size=30)
        
        peak_demand_risk = np.percentile(historical_sim_demands, 95) # 95th percentile stress point
        
        # Calculate Vulnerability Score: Ratio of Peak simulated demand vs Actual reserves
        vulnerability_score = (peak_demand_risk / liquidity) * 100
        
        if vulnerability_score >= 85:
            status = "CRITICAL_ILLIQUIDITY_RISK"
        elif vulnerability_score >= 50:
            status = "WARNING_ELEVATED_DEMAND"
        else:
            status = "STABLE"
            
        stress_report.append({
            "currency": currency,
            "current_liquidity": round(liquidity, 2),
            "95th_percentile_predicted_demand": round(peak_demand_risk, 2),
            "vulnerability_score_percentage": round(vulnerability_score, 2),
            "risk_status": status
        })
        
    return stress_report
