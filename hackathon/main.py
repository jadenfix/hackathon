#!/usr/bin/env python3
"""
Energy Management System - Main Application
Entry point for the energy management dashboard and system components.
Combines MARA API GridPilot-GT functionality with LLM integration.
"""

import argparse
from datetime import datetime
import json
import pandas as pd
import numpy as np
import time
import sys
import os
import logging
from pathlib import Path

DEFAULT_FIXTURE_AS_OF = "2026-10-13T00:00:00Z"

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import toml
    from llm_integration.mock_interface import MockLLMInterface
    from llm_integration.unified_interface import UnifiedLLMInterface
    
    # GridPilot-GT imports (optional - only if modules exist)
    try:
        from api_client.client import get_prices, get_inventory, submit_bid
        from forecasting.forecaster import Forecaster
        from game_theory.bid_generators import build_bid_vector
        from game_theory.vcg_auction import vcg_allocate
        from control.cooling_model import cooling_for_gpu_kW
        from dispatch.dispatch_agent import build_payload
        GRIDPILOT_AVAILABLE = True
    except ImportError:
        GRIDPILOT_AVAILABLE = False
        print("⚠️ GridPilot-GT modules not available - gridpilot mode will not work")
        
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install streamlit pandas plotly toml anthropic")
    sys.exit(1)


def load_config(config_path: str = "config.toml") -> dict:
    """Load configuration from TOML file."""
    try:
        with open(config_path, 'r') as f:
            return toml.load(f)
    except FileNotFoundError:
        print(f"Configuration file {config_path} not found. Using defaults.")
        return {}
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}


def setup_logging(config: dict):
    """Setup logging configuration."""
    log_config = config.get('logging', {})
    level = getattr(logging, log_config.get('level', 'INFO'))
    
    logging.basicConfig(
        level=level,
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_config.get('file', 'energy_management.log'))
        ]
    )


def test_llm_interface():
    """Test the LLM interface functionality."""
    print("Testing LLM Interface...")
    
    # Use unified interface that automatically selects the best provider
    try:
        interface = UnifiedLLMInterface()
        if interface.is_available():
            provider_info = interface.get_provider_info()
            print(f"✅ Using {provider_info['provider']} LLM provider")
            return interface
        else:
            print("⚠️ No LLM providers available")
    except Exception as e:
        print(f"⚠️ Error with unified LLM interface: {e}")
    
    # Fall back to mock interface
    interface = MockLLMInterface()
    print("✅ Mock LLM interface loaded")
    return interface


def run_tests():
    """Run system tests."""
    print("Running system tests...")
    
    # Test LLM interface
    interface = test_llm_interface()
    
    # Test sample queries
    test_queries = [
        "What are the benefits of demand response?",
        "Explain the battery management strategy",
        "How can I optimize energy costs?"
    ]
    
    print("\nTesting sample queries:")
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = interface.process_query(query)
        print(f"Response: {response[:100]}...")
    
    print("\n✅ All tests completed successfully!")


def run_gridpilot_gt(
    simulate: bool = False,
    *,
    seed: int | None = None,
    as_of: str | None = None,
):
    """Main orchestration loop for GridPilot-GT.
    
    Args:
        simulate: If True, run in simulation mode with mock data
    """
    if simulate and seed is not None:
        np.random.seed(seed)

    fixture_time = None
    fixture_label = None
    if simulate:
        fixture_label = as_of or DEFAULT_FIXTURE_AS_OF
        fixture_time = datetime.fromisoformat(fixture_label.replace("Z", "+00:00"))

    start_time = time.time()
    print("🚀 GridPilot-GT Starting...")
    print(f"Simulation mode: {simulate}")
    print(f"Timestamp: {fixture_label or datetime.now().isoformat()}")
    
    try:
        # Step 1: Get market data
        print("\n📊 Fetching market data...")
        if simulate:
            from api_client.client import _generate_fallback_prices, _generate_fallback_inventory
            prices = _generate_fallback_prices(as_of=fixture_time)
            inventory = _generate_fallback_inventory(as_of=fixture_time)
        else:
            prices = get_prices()
            inventory = get_inventory()
        print(f"Retrieved {len(prices)} price records")
        print(f"Current power available: {inventory['power_available']} kW")
        
        # Step 2: Generate forecasts
        print("\n🔮 Generating forecasts...")
        forecaster = Forecaster(use_prophet=not simulate, use_ensemble=not simulate)
        if simulate:
            forecast = forecaster._predict_simple(prices, periods=24)  # type: ignore  # pylint: disable=protected-access
        else:
            forecast = forecaster.predict_next(prices)
        print(f"Generated {len(forecast)} hour forecast")
        
        # Step 3: Optimize bids
        print("\n💰 Optimizing bids...")
        current_price = prices['price'].iloc[-1] if len(prices) > 0 else 50.0
        soc = inventory['battery_soc']
        lambda_deg = 0.0002  # Battery degradation cost
        
        uncertainty_df = pd.DataFrame(forecast[["σ_energy","σ_hash","σ_token"]])
        bids = build_bid_vector(
            current_price=current_price,
            forecast=forecast,
            uncertainty=uncertainty_df,
            soc=soc,
            lambda_deg=lambda_deg
        )
        print(f"Generated bid vector with {len(bids)} periods")
        
        # Step 4: Run VCG auction
        print("\n🏛️ Running VCG auction...")
        allocation, payments = vcg_allocate(bids, inventory["power_total"])
        print(f"Allocation: {allocation}")
        print(f"Payments: {payments}")
        
        # Step 5: Calculate cooling requirements
        print("\n❄️ Calculating cooling requirements...")
        inference_power = allocation.get("inference", 0)  # Already in kW
        cooling_kw, cooling_metrics = cooling_for_gpu_kW(inference_power)
        print(f"Cooling required: {cooling_kw:.2f} kW (COP: {cooling_metrics['cop']:.2f})")
        
        # Step 6: Build dispatch payload
        print("\n📤 Building dispatch payload...")
        payload = build_payload(
            allocation=allocation,
            inventory=inventory,
            soc=soc,
            cooling_kw=cooling_kw,
            power_limit=inventory["power_total"]
        )
        
        # Step 7: Submit to market (if not simulation)
        if not simulate:
            print("\n🚀 Submitting to market...")
            response = submit_bid(payload)
            print(f"Market response: {response}")
        else:
            print("\n🎯 SIMULATION - Would submit payload:")
            print(f"Total power: {payload['power_requirements']['total_power_kw']:.2f} kW")
            print(f"Constraints satisfied: {payload['constraints_satisfied']}")
            print(f"System utilization: {payload['system_state']['utilization']:.1%}")
        
        print("\n✅ GridPilot-GT cycle completed successfully!")
        
        # Summary metrics
        print("\n📈 Summary Metrics:")
        print(f"  • GPU Allocation: {sum(allocation.values()):.3f}")
        print(f"  • Total Power: {payload['power_requirements']['total_power_kw']:.1f} kW")
        print(f"  • Battery SOC: {soc:.1%}")
        print(f"  • Cooling Load: {cooling_kw:.1f} kW")
        print(f"  • Efficiency: {cooling_metrics['efficiency']:.1%}")
        
        # Return success result for testing (with interface compatibility)
        return {
            'success': True,
            'mode': 'synthetic-simulation' if simulate else 'live',
            'elapsed_time': time.time() - start_time,
            'soc': soc,
            'total_power': payload['power_requirements']['total_power_kw'],
            'revenue': payments,
            'allocation': allocation,
            'cooling_kw': cooling_kw,
            'efficiency': cooling_metrics['efficiency'],
            'fixture_seed': seed if simulate else None,
            'as_of': fixture_label if simulate else None,
            'payload': payload,
            # Interface compatibility fields
            'power_requirements': payload['power_requirements'],
            'constraints_satisfied': payload['constraints_satisfied'],
            'system_state': payload['system_state'],
            'performance_metrics': {
                'build_time_ms': (time.time() - start_time) * 1000 * 0.1,  # Estimate build time as 10% of total
                'total_time_ms': (time.time() - start_time) * 1000
            }
        }
        
    except Exception as e:
        print(f"❌ Error in GridPilot-GT: {e}")
        print(f"💡 Run with simulate=True for testing")
        return {
            'success': False,
            'error': str(e),
            'elapsed_time': time.time() - start_time
        }


def build_offline_receipt(result: dict) -> dict:
    """Build a stable, JSON-safe receipt for the provider-free fixture run."""
    if result.get("mode") != "synthetic-simulation":
        raise ValueError("offline receipts require synthetic simulation mode")

    allocation = {
        key: round(float(value), 6)
        for key, value in sorted(result["allocation"].items())
    }
    return {
        "schema": "gridpilot.offline-receipt.v1",
        "scope": "provider-free synthetic fixture; no market submission",
        "mode": result["mode"],
        "seed": result["fixture_seed"],
        "as_of": result["as_of"],
        "constraints_satisfied": bool(result["constraints_satisfied"]),
        "metrics": {
            "battery_soc": round(float(result["soc"]), 6),
            "total_power_kw": round(float(result["total_power"]), 6),
            "cooling_kw": round(float(result["cooling_kw"]), 6),
            "cooling_efficiency": round(float(result["efficiency"]), 6),
        },
        "allocation_kw": allocation,
    }


def write_json_receipt(path: str, receipt: dict) -> None:
    """Write a receipt atomically so interrupted runs cannot leave partial JSON."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Energy Management System with GridPilot-GT")
    parser.add_argument(
        "--mode", 
        choices=["dashboard", "test", "llm", "gridpilot"], 
        default="dashboard",
        help="Run mode: dashboard (default), test, llm, or gridpilot"
    )
    parser.add_argument(
        "--config", 
        default="config.toml",
        help="Configuration file path"
    )
    parser.add_argument(
        "--port", 
        type=int,
        help="Dashboard port (overrides config)"
    )
    parser.add_argument(
        "--simulate", 
        type=int, 
        default=1,
        help="GridPilot-GT simulation mode (1) or live mode (0)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=8257,
        help="Random seed for the provider-free synthetic fixture",
    )
    parser.add_argument(
        "--as-of",
        default=DEFAULT_FIXTURE_AS_OF,
        help="Label used in deterministic synthetic-fixture receipts",
    )
    parser.add_argument(
        "--receipt",
        help="Write a deterministic JSON receipt (simulation mode only)",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Energy Management System in {args.mode} mode")
    
    if args.mode == "test":
        run_tests()
    
    elif args.mode == "llm":
        # Interactive LLM mode
        interface = test_llm_interface()
        print("\n🤖 Energy Management Assistant")
        print("Type 'quit' to exit")
        print("-" * 50)
        
        while True:
            try:
                query = input("\nYou: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if query:
                    response = interface.process_query(query)
                    print(f"\nAssistant: {response}")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    elif args.mode == "gridpilot":
        # Run GridPilot-GT energy trading system
        if not GRIDPILOT_AVAILABLE:
            print("❌ GridPilot-GT modules not available")
            print("Please ensure all GridPilot-GT dependencies are installed")
            sys.exit(1)
            
        simulate_mode = bool(args.simulate)
        if args.receipt and not simulate_mode:
            parser.error("--receipt is available only with --simulate 1")

        result = run_gridpilot_gt(
            simulate=simulate_mode,
            seed=args.seed if simulate_mode else None,
            as_of=args.as_of if simulate_mode else None,
        )
        
        if result['success']:
            if args.receipt:
                receipt = build_offline_receipt(result)
                write_json_receipt(args.receipt, receipt)
                print(f"Receipt: {args.receipt}")
            print("\n🎉 GridPilot-GT executed successfully!")
            sys.exit(0)
        else:
            print("\n💥 GridPilot-GT failed!")
            sys.exit(1)
    
    elif args.mode == "dashboard":
        from ui.dashboard import main as run_dashboard
        # Run the Streamlit dashboard
        print("Starting Energy Management Dashboard...")
        print("The dashboard will open in your browser.")
        print("Press Ctrl+C to stop the server.")
        
        # Override port if specified
        if args.port:
            config['dashboard']['port'] = args.port
        
        # Run dashboard
        run_dashboard()


if __name__ == "__main__":
    main()
