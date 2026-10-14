#!/usr/bin/env python3
"""
GridPilot-GT FastAPI Backend Server
Exposes ML and quantitative strategy functionality via REST APIs
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import traceback

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import pandas as pd
import numpy as np

# Import GridPilot-GT modules
from api_client import get_prices, get_inventory, submit_bid
from api_client.client import test_mara_api_connection
from forecasting import Forecaster, create_advanced_forecaster, get_forecaster
from game_theory.bid_generators import build_bid_vector, portfolio_optimization, dynamic_pricing_strategy
from game_theory.vcg_auction import vcg_allocate, auction_efficiency_metrics
from control.cooling_model import cooling_for_gpu_kW
from dispatch.dispatch_agent import build_payload
import main

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="GridPilot-GT API",
    description="Advanced Energy Trading & GPU Resource Allocation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management
class SystemState:
    def __init__(self):
        self.forecaster = None
        self.last_prices = None
        self.last_inventory = None
        self.last_forecast = None
        self.last_allocation = None
        self.system_metrics = {}
        self.websocket_clients = set()
        
    def update_metrics(self, metrics: Dict[str, Any]):
        self.system_metrics.update({
            **metrics,
            'timestamp': datetime.now().isoformat(),
            'uptime': time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
        })

system_state = SystemState()

# Pydantic models for API contracts
class ForecastRequest(BaseModel):
    periods: int = Field(default=24, ge=1, le=168, description="Forecast horizon in hours")
    use_advanced: bool = Field(default=False, description="Use advanced quantitative models")

class ForecastResponse(BaseModel):
    forecast: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class OptimizationRequest(BaseModel):
    forecast_periods: int = Field(default=24, ge=1, le=168)
    risk_aversion: float = Field(default=0.5, ge=0.0, le=1.0)
    lambda_deg: float = Field(default=0.0002, ge=0.0, le=0.01)

class OptimizationResponse(BaseModel):
    allocation: Dict[str, float]
    payments: Dict[str, float]
    optimization_metrics: Dict[str, Any]
    constraints_satisfied: bool

class SystemStatusResponse(BaseModel):
    status: str
    timestamp: str
    api_connectivity: Dict[str, Any]
    system_metrics: Dict[str, Any]
    performance_summary: Dict[str, Any]

# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    app.state.start_time = time.time()
    logger.info("🚀 GridPilot-GT FastAPI server starting up...")
    
    # Initialize forecaster
    system_state.forecaster = get_forecaster()
    
    # Test API connectivity
    try:
        connection_test = test_mara_api_connection()
        logger.info(f"MARA API status: {connection_test.get('overall_status', 'unknown')}")
    except Exception as e:
        logger.warning(f"API connectivity check failed: {e}")
    
    # Start background tasks
    asyncio.create_task(background_data_refresh())
    logger.info("✅ GridPilot-GT FastAPI server ready!")

@app.get("/", response_class=JSONResponse)
async def root():
    """API root endpoint with system information."""
    return {
        "service": "GridPilot-GT API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "documentation": "/docs",
        "endpoints": {
            "system": "/api/v1/system/status",
            "data": "/api/v1/data/prices",
            "forecast": "/api/v1/ml/forecast",
            "optimization": "/api/v1/optimization/allocate",
            "dispatch": "/api/v1/dispatch/execute",
            "websocket": "/ws/live-data"
        }
    }

@app.get("/api/v1/system/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get comprehensive system status and health metrics."""
    try:
        # Test API connectivity
        api_test = test_mara_api_connection()
        
        # Get current system metrics
        performance_summary = {
            "forecaster_ready": system_state.forecaster is not None,
            "last_data_update": system_state.last_prices is not None,
            "websocket_clients": len(system_state.websocket_clients),
            "uptime_seconds": time.time() - app.state.start_time,
        }
        
        if system_state.last_allocation:
            performance_summary["last_allocation_kw"] = sum(system_state.last_allocation.values())
        
        return SystemStatusResponse(
            status="operational",
            timestamp=datetime.now().isoformat(),
            api_connectivity=api_test,
            system_metrics=system_state.system_metrics,
            performance_summary=performance_summary
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"System status error: {str(e)}")

@app.get("/api/v1/data/prices")
async def get_market_prices(hours_back: int = 24):
    """Get current and historical market prices."""
    try:
        prices_df = get_prices()
        
        # Limit to requested hours
        if len(prices_df) > hours_back:
            prices_df = prices_df.tail(hours_back)
        
        # Convert to JSON-serializable format
        prices_data = []
        for _, row in prices_df.iterrows():
            prices_data.append({
                "timestamp": row['timestamp'].isoformat() if pd.notna(row['timestamp']) else None,
                "energy_price": float(row['price']) if pd.notna(row['price']) else None,
                "hash_price": float(row.get('hash_price', 0)) if pd.notna(row.get('hash_price', 0)) else None,
                "token_price": float(row.get('token_price', 0)) if pd.notna(row.get('token_price', 0)) else None,
                "volume": float(row.get('volume', 1000)) if pd.notna(row.get('volume', 1000)) else None,
                "volatility_24h": float(row.get('price_volatility_24h', 0)) if pd.notna(row.get('price_volatility_24h', 0)) else None
            })
        
        # Update system state
        system_state.last_prices = prices_df
        
        return {
            "data": prices_data,
            "metadata": {
                "total_records": len(prices_data),
                "latest_price": prices_data[-1]["energy_price"] if prices_data else None,
                "price_range": {
                    "min": min(p["energy_price"] for p in prices_data if p["energy_price"]) if prices_data else None,
                    "max": max(p["energy_price"] for p in prices_data if p["energy_price"]) if prices_data else None
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        raise HTTPException(status_code=500, detail=f"Price data error: {str(e)}")

@app.get("/api/v1/data/inventory")
async def get_system_inventory():
    """Get current system inventory and operational status."""
    try:
        inventory = get_inventory()
        
        # Update system state
        system_state.last_inventory = inventory
        
        # Convert to frontend-friendly format
        return {
            "power": {
                "total_kw": inventory.get("power_total", 0),
                "available_kw": inventory.get("power_available", 0),
                "used_kw": inventory.get("power_used", 0),
                "utilization": inventory.get("power_used", 0) / inventory.get("power_total", 1) if inventory.get("power_total", 0) > 0 else 0
            },
            "battery": {
                "soc": inventory.get("battery_soc", 0),
                "capacity_mwh": inventory.get("battery_capacity_mwh", 1.0),
                "max_power_kw": inventory.get("battery_max_power_kw", 250.0)
            },
            "gpu": {
                "utilization": inventory.get("gpu_utilization", 0),
                "cooling_load_kw": inventory.get("cooling_load", 0)
            },
            "operational": {
                "temperature": inventory.get("temperature", 65),
                "efficiency": inventory.get("efficiency", 0.92),
                "status": inventory.get("status", "operational"),
                "alerts": inventory.get("alerts", [])
            },
            "timestamp": inventory.get("timestamp", datetime.now().isoformat())
        }
        
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail=f"Inventory error: {str(e)}")

@app.post("/api/v1/ml/forecast", response_model=ForecastResponse)
async def generate_forecast(request: ForecastRequest):
    """Generate ML-based price forecasts."""
    try:
        start_time = time.time()
        
        # Get current prices if not cached
        if system_state.last_prices is None:
            system_state.last_prices = get_prices()
        
        # Initialize forecaster if needed
        if system_state.forecaster is None:
            if request.use_advanced:
                system_state.forecaster = create_advanced_forecaster()
            else:
                system_state.forecaster = get_forecaster()
        
        # Generate forecast
        forecast_df = system_state.forecaster.predict_next(
            system_state.last_prices, 
            periods=request.periods
        )
        
        # Convert to JSON format
        forecast_data = []
        for _, row in forecast_df.iterrows():
            forecast_data.append({
                "timestamp": row['timestamp'].isoformat() if pd.notna(row['timestamp']) else None,
                "predicted_price": float(row['predicted_price']) if pd.notna(row['predicted_price']) else None,
                "lower_bound": float(row['lower_bound']) if pd.notna(row['lower_bound']) else None,
                "upper_bound": float(row['upper_bound']) if pd.notna(row['upper_bound']) else None,
                "uncertainty_energy": float(row.get('σ_energy', 0)) if pd.notna(row.get('σ_energy', 0)) else None,
                "method": row.get('method', 'unknown')
            })
        
        # Calculate performance metrics
        processing_time = time.time() - start_time
        avg_price = forecast_df['predicted_price'].mean() if len(forecast_df) > 0 else 0
        price_volatility = forecast_df['predicted_price'].std() if len(forecast_df) > 0 else 0
        
        # Update system state
        system_state.last_forecast = forecast_df
        
        return ForecastResponse(
            forecast=forecast_data,
            metadata={
                "periods": request.periods,
                "model_type": "advanced" if request.use_advanced else "standard",
                "features_used": 104 if hasattr(system_state.forecaster, 'feature_engineer') else 0,
                "avg_predicted_price": float(avg_price),
                "price_volatility": float(price_volatility)
            },
            performance_metrics={
                "processing_time_ms": processing_time * 1000,
                "forecast_accuracy": "N/A",  # Would need historical validation
                "model_confidence": "high" if processing_time < 2.0 else "medium"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Forecast error: {str(e)}")

@app.post("/api/v1/optimization/allocate", response_model=OptimizationResponse)
async def optimize_allocation(request: OptimizationRequest):
    """Optimize resource allocation using game theory and MPC."""
    try:
        start_time = time.time()
        
        # Get required data
        if system_state.last_prices is None:
            system_state.last_prices = get_prices()
        
        if system_state.last_inventory is None:
            system_state.last_inventory = get_inventory()
        
        if system_state.last_forecast is None:
            # Generate forecast first
            if system_state.forecaster is None:
                system_state.forecaster = get_forecaster()
            system_state.last_forecast = system_state.forecaster.predict_next(
                system_state.last_prices, periods=request.forecast_periods
            )
        
        # Build bid vector using MPC
        current_price = system_state.last_prices['price'].iloc[-1]
        soc = system_state.last_inventory['battery_soc']
        
        uncertainty_df = pd.DataFrame(system_state.last_forecast[["σ_energy","σ_hash","σ_token"]])
        bids = build_bid_vector(
            current_price=current_price,
            forecast=system_state.last_forecast,
            uncertainty=uncertainty_df,
            soc=soc,
            lambda_deg=request.lambda_deg
        )
        
        # Run VCG auction
        allocation, payments = vcg_allocate(bids, system_state.last_inventory["power_total"])
        
        # Calculate optimization metrics
        efficiency_metrics = auction_efficiency_metrics(allocation, bids)
        processing_time = time.time() - start_time
        
        # Check constraints
        total_allocation = sum(allocation.values())
        constraints_satisfied = total_allocation <= system_state.last_inventory["power_total"]
        
        # Update system state
        system_state.last_allocation = allocation
        system_state.update_metrics({
            "last_optimization_time": processing_time,
            "total_allocation_kw": total_allocation,
            "constraints_satisfied": constraints_satisfied
        })
        
        return OptimizationResponse(
            allocation=allocation,
            payments=payments,
            optimization_metrics={
                "processing_time_ms": processing_time * 1000,
                "social_welfare": efficiency_metrics.get("social_welfare", 0),
                "allocation_efficiency": efficiency_metrics.get("allocation_efficiency", 0),
                "total_allocation_kw": total_allocation,
                "utilization": total_allocation / system_state.last_inventory["power_total"]
            },
            constraints_satisfied=constraints_satisfied
        )
        
    except Exception as e:
        logger.error(f"Error in optimization: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")

@app.post("/api/v1/dispatch/execute")
async def execute_dispatch():
    """Execute dispatch based on current allocation."""
    try:
        start_time = time.time()
        
        # Ensure we have all required data
        if not all([system_state.last_allocation, system_state.last_inventory]):
            raise HTTPException(status_code=400, detail="No allocation or inventory data available")
        
        # Calculate cooling requirements
        inference_power = system_state.last_allocation.get("inference", 0)
        cooling_kw, cooling_metrics = cooling_for_gpu_kW(inference_power)
        
        # Build dispatch payload
        payload = build_payload(
            allocation=system_state.last_allocation,
            inventory=system_state.last_inventory,
            soc=system_state.last_inventory['battery_soc'],
            cooling_kw=cooling_kw,
            power_limit=system_state.last_inventory["power_total"]
        )
        
        # Submit to market (in production - for demo, we'll simulate)
        processing_time = time.time() - start_time
        
        return {
            "dispatch_result": {
                "status": "success",
                "payload": payload,
                "cooling_requirements": {
                    "cooling_kw": cooling_kw,
                    "cop": cooling_metrics["cop"],
                    "efficiency": cooling_metrics["efficiency"]
                }
            },
            "performance_metrics": {
                "processing_time_ms": processing_time * 1000,
                "constraints_satisfied": payload["constraints_satisfied"],
                "total_power_kw": payload["power_requirements"]["total_power_kw"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in dispatch: {e}")
        raise HTTPException(status_code=500, detail=f"Dispatch error: {str(e)}")

@app.post("/api/v1/system/run-full-cycle")
async def run_full_cycle(
    simulate: bool = True,
    seed: int = 8257,
    as_of: Optional[datetime] = None,
):
    """Run complete GridPilot-GT optimization cycle."""
    try:
        start_time = time.time()
        
        # Run main system cycle
        result = main.run_gridpilot_gt(
            simulate=simulate,
            seed=seed if simulate else None,
            as_of=(as_of.isoformat().replace("+00:00", "Z") if as_of else main.DEFAULT_FIXTURE_AS_OF)
            if simulate else None,
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Full cycle failed: {result.get('error', 'unknown error')}",
            )
        
        processing_time = time.time() - start_time
        
        # Update system state with results
        if result.get('success'):
            system_state.update_metrics({
                "last_full_cycle": processing_time,
                "cycle_success": True,
                "revenue": result.get('revenue', {}),
                "total_power": result.get('total_power', 0)
            })
        
        return {
            "cycle_result": result,
            "scope": (
                "provider-free synthetic fixture; no market submission"
                if simulate else "live provider execution; not covered by offline verification"
            ),
            "offline_receipt": main.build_offline_receipt(result) if simulate else None,
            "performance_metrics": {
                "total_time_ms": processing_time * 1000,
                "success": result.get('success', False)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in full cycle: {e}")
        raise HTTPException(status_code=500, detail=f"Full cycle error: {str(e)}")

# WebSocket endpoint for real-time data
@app.websocket("/ws/live-data")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time system data streaming."""
    await websocket.accept()
    system_state.websocket_clients.add(websocket)
    
    try:
        while True:
            # Send current system state
            data = {
                "timestamp": datetime.now().isoformat(),
                "prices": {
                    "current": system_state.last_prices['price'].iloc[-1] if system_state.last_prices is not None else None,
                    "trend": "stable"  # Could calculate trend
                },
                "inventory": {
                    "power_available": system_state.last_inventory.get("power_available", 0) if system_state.last_inventory else 0,
                    "battery_soc": system_state.last_inventory.get("battery_soc", 0) if system_state.last_inventory else 0
                },
                "allocation": system_state.last_allocation or {},
                "system_metrics": system_state.system_metrics
            }
            
            await websocket.send_json(data)
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except WebSocketDisconnect:
        system_state.websocket_clients.remove(websocket)
        logger.info("WebSocket client disconnected")

# Background tasks
async def background_data_refresh():
    """Background task to refresh data periodically."""
    while True:
        try:
            # Refresh prices every 5 minutes
            system_state.last_prices = get_prices()
            
            # Refresh inventory every 2 minutes
            system_state.last_inventory = get_inventory()
            
            # Broadcast to WebSocket clients
            if system_state.websocket_clients:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "data_refresh",
                    "latest_price": system_state.last_prices['price'].iloc[-1] if system_state.last_prices is not None else None
                }
                
                # Send to all connected clients
                disconnected_clients = set()
                for client in system_state.websocket_clients:
                    try:
                        await client.send_json(data)
                    except:
                        disconnected_clients.add(client)
                
                # Remove disconnected clients
                system_state.websocket_clients -= disconnected_clients
            
            await asyncio.sleep(120)  # Refresh every 2 minutes
            
        except Exception as e:
            logger.error(f"Background refresh error: {e}")
            await asyncio.sleep(60)  # Retry in 1 minute

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - app.state.start_time
    }

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 