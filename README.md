# [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](tests/)
[![API](https://img.shields.io/badge/API-MARA%20Hackathon%202025-orange.svg)](https://mara-hackathon-api.onrender.com)
[![Demo](https://img.shields.io/badge/Demo-Loom-blueviolet?logo=loom)](https://www.loom.com/share/25d4038c47e94de4866c095ae6d5c4c9?sid=bf76da66-001d-4a0c-ba37-1a6ee619677b)

A sophisticated energy trading and optimization platform that integrates real-time market data, advanced quantitative forecasting, and intelligent resource allocation for mining and compute operations.

## 🔗 Demo Video

[Click here to watch the demo on Loom](https://www.loom.com/share/25d4038c47e94de4866c095ae6d5c4c9?sid=bf76da66-001d-4a0c-ba37-1a6ee619677b)
## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Demo & Interactive Features](#-demo--interactive-features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Integration](#api-integration)
- [Testing](#testing)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

GridPilot-GT is a comprehensive energy management system designed for the MARA Hackathon 2025. It provides real-time energy trading optimization, advanced forecasting capabilities, and intelligent resource allocation across mining and compute workloads.

### Key Capabilities

- **Real-time Market Integration**: Live pricing data from MARA API
- **Advanced Forecasting**: Multi-model ensemble with uncertainty quantification
- **Intelligent Optimization**: Model Predictive Control (MPC) and game theory
- **Resource Management**: Dynamic allocation across mining and compute assets
- **Interactive Dashboard**: Real-time monitoring and control interface

## ✨ Features

### 🏗️ Core System
- **Multi-lane Architecture**: Modular design across data, optimization, dispatch, and UI
- **Real-time Processing**: Sub-second decision making and allocation
- **Robust Error Handling**: Automatic fallback mechanisms and graceful degradation
- **Comprehensive Testing**: 30+ tests with 100% pass rate

### 📊 Advanced Analytics
- **Quantitative Models**: GARCH volatility, Kalman filtering, Wavelet analysis
- **Machine Learning Ensemble**: XGBoost, Gaussian Process, Prophet forecasting
- **Feature Engineering**: 102+ technical indicators and market patterns
- **Uncertainty Quantification**: Bootstrap sampling and model disagreement metrics

### 🎮 Optimization Engine
- **Model Predictive Control**: CVXPY-based power allocation optimization
- **Game Theory**: Strategic bidding with market equilibrium analysis
- **Portfolio Optimization**: Mean-variance and risk parity allocation
- **Constraint Management**: Battery SOC, thermal limits, grid requirements

## 🏗️ Architecture

The system operates across four integrated development lanes:

```
GridPilot-GT/
├── Lane A: Data & Forecasting     # Real-time data processing & ML models
├── Lane B: Bidding & MPC         # Optimization & game theory
├── Lane C: Auction & Dispatch    # Resource allocation & execution
└── Lane D: UI & LLM              # Dashboard & natural language interface
```

### Lane A: Data & Forecasting
- **MARA API Integration**: Real-time energy, hash, and token prices
- **Advanced Quantitative Models**: GARCH volatility, Kalman filtering, Wavelet analysis
- **Machine Learning Ensemble**: XGBoost + Gaussian Process + Prophet forecasting
- **Feature Engineering**: 102+ technical indicators and market patterns

### Lane B: Bidding & MPC
- **Model Predictive Control**: CVXPY optimization for power allocation
- **Game Theory**: Strategic bidding with market equilibrium analysis
- **Portfolio Optimization**: Mean-variance and risk parity allocation
- **Constraint Handling**: Battery SOC, thermal limits, grid requirements

### Lane C: Auction & Dispatch
- **VCG Auctions**: Vickrey-Clarke-Groves mechanism for fair allocation
- **Real-time Execution**: Sub-second decision making and allocation
- **Load Balancing**: Optimal distribution across mining and compute workloads

### Lane D: UI & LLM
- **Streamlit Dashboard**: Real-time monitoring and control
- **LLM Integration**: Natural language system interaction
- **Performance Analytics**: ROI tracking, efficiency metrics, market insights

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- 8GB+ RAM (for advanced models)
- Internet connection (for MARA API integration)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd hackathon
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Access
```bash
# Edit config.toml with your MARA API credentials
cp config.toml.example config.toml
# Update with your API key and site configuration
```

### 4. Test Installation
```bash
python test_mara_api.py
```

### 5. Launch the System
```bash
python main.py
```

## 🎮 Demo & Interactive Features

### 🚀 Running the Demo

GridPilot includes a comprehensive interactive dashboard that demonstrates all system capabilities. Here's how to get started:

#### 1. Launch the Dashboard
```bash
# Navigate to the hackathon directory
cd hackathon

# Start the Streamlit dashboard
streamlit run ui/dashboard.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

#### 2. Dashboard Overview

The demo dashboard features four main tabs:

**📊 Overview Tab**
- Real-time energy consumption and price charts
- System metrics and performance indicators
- Optimization results display
- Quick statistics and efficiency scores

**💬 Chat Assistant Tab**
- Interactive AI assistant powered by Claude
- Ask questions about energy management
- Get real-time advice on optimization strategies
- Natural language explanations of system decisions

**🤖 AI Insights Tab**
- Auto-generated insights from energy data
- Decision explanations with context
- Market analysis and recommendations
- Performance optimization suggestions

**⚙️ System Status Tab**
- Real-time system health monitoring
- Power utilization metrics
- Temperature and cooling status
- Active alerts and system events

### 🎯 Key Demo Features

#### Real-Time Data Integration
- **Live MARA API Data**: Real-time energy, hash, and token prices
- **Automatic Fallback**: Seamless transition to synthetic data when API unavailable
- **Data Visualization**: Interactive charts showing 24-hour trends

#### Advanced Optimization Demo
1. **Click "🚀 Run Optimization"** in the sidebar
2. **Watch Real-Time Processing**: See the system analyze market conditions
3. **View Results**: Check allocation decisions and performance metrics
4. **Understand Decisions**: Use the AI assistant to explain optimization choices

#### Interactive AI Assistant
- **Ask Questions**: "How should I optimize my power allocation?"
- **Get Insights**: "What's causing the current price volatility?"
- **Request Explanations**: "Why did the system choose this allocation?"

#### System Monitoring
- **Real-Time Metrics**: Battery SOC, power utilization, temperature
- **Performance Tracking**: Efficiency scores and optimization results
- **Alert System**: Active warnings and system status updates

### 🎮 Demo Scenarios

#### Scenario 1: Basic System Exploration
1. Open the dashboard
2. Navigate through all four tabs
3. Observe real-time data updates
4. Try the chat assistant with basic questions

#### Scenario 2: Optimization Demonstration
1. Go to the Overview tab
2. Click "🚀 Run Optimization" in the sidebar
3. Watch the optimization process
4. Review the results in the "Enhanced GridPilot Optimization Results" section
5. Ask the AI assistant to explain the decisions

#### Scenario 3: AI-Powered Analysis
1. Navigate to the AI Insights tab
2. Let the system generate insights automatically
3. Ask specific questions in the Chat Assistant tab
4. Request decision explanations for optimization results

#### Scenario 4: System Monitoring
1. Go to the System Status tab
2. Monitor real-time system health
3. Check power utilization and efficiency metrics
4. Review system events and alerts

### 🔧 Demo Configuration

#### API Integration (Optional)
For full demo experience with real data:
```bash
# Set up MARA API credentials
export MARA_API_KEY="your_api_key_here"
export SITE_NAME="DemoSite"
export SITE_POWER_KW="1000000"
```

#### Demo Mode (Default)
The system runs in demo mode by default with:
- Synthetic market data
- Simulated optimization results
- Mock AI responses (if Claude API unavailable)
- Full dashboard functionality

### 📊 Demo Data Sources

The demo uses multiple data sources:
- **Real MARA API**: When available and configured
- **Synthetic Data**: Fallback with realistic market patterns
- **Simulated Optimization**: Advanced stochastic models
- **Mock AI Responses**: When Claude API unavailable

### 🎯 Demo Learning Objectives

After running the demo, you should understand:
- **Real-time Energy Trading**: How the system optimizes power allocation
- **Advanced Forecasting**: Multi-model ensemble predictions
- **AI-Powered Decision Making**: How LLM integration enhances optimization
- **System Architecture**: Four-lane development structure
- **Market Integration**: MARA API connectivity and fallback mechanisms

### 🚀 Next Steps After Demo

1. **Explore the Code**: Review the implementation in `hackathon/` directory
2. **Run Tests**: Execute `pytest tests/ -v` to see system validation
3. **Customize Configuration**: Modify `config.toml` for your use case
4. **Extend Functionality**: Add new forecasting models or optimization strategies
5. **Deploy**: Use the system for real energy trading operations

---

## 📦 Installation

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: 8GB+ RAM recommended
- **Storage**: 2GB+ free space
- **Network**: Internet connection for API integration

### Dependencies

Core dependencies are managed through `requirements.txt`:

```bash
# Core framework
streamlit>=1.28.0
pandas>=2.0.0
numpy==1.24.4

# Quantitative modeling
arch==5.6.0           # GARCH models
filterpy==1.4.5       # Kalman filtering
PyWavelets==1.4.1     # Wavelet analysis
xgboost==2.0.3        # Gradient boosting
prophet==1.1.5        # Time series forecasting

# Optimization
cvxpy==1.4.1          # Convex optimization
scikit-learn==1.3.2   # Machine learning

# API and utilities
httpx==0.25.2         # HTTP client
requests==2.31.0      # HTTP library
toml>=0.10.2          # Configuration parsing

# Testing and development
pytest==7.4.3         # Testing framework
ruff==0.1.6           # Code linting
```

### Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

### API Configuration
Create or update `config.toml` with your MARA API credentials:

```toml
[api]
api_key = "YOUR_MARA_API_KEY_HERE"
site_name = "YourSiteName"
site_power_kw = 1000000  # 1MW default

[system]
debug = false
log_level = "INFO"
```

### Environment Variables
```bash
export MARA_API_KEY="your_api_key_here"
export SITE_NAME="your_site_name"
export SITE_POWER_KW="1000000"
```

## 🎮 Usage

### Starting the System
```bash
# Run the main application
python main.py

# Or run specific components
python -m hackathon.forecasting.advanced_forecaster
python -m hackathon.game_theory.mpc_controller
```

### Dashboard Access
Once running, access the Streamlit dashboard at:
```
http://localhost:8501
```

### API Testing
```bash
# Test MARA API integration
python test_mara_api.py

# Run comprehensive test suite
pytest tests/ -v
```

## 🔌 API Integration

### MARA Hackathon 2025 API

The system integrates with the MARA Hackathon 2025 API for real-time data:

#### Pricing Data (No Auth Required)
```bash
GET https://mara-hackathon-api.onrender.com/prices
# Returns: energy_price, hash_price, token_price, timestamp
```

#### Inventory Management (Auth Required)
```bash
GET https://mara-hackathon-api.onrender.com/inventory
# Returns: inference assets, miners, power allocation, tokens
```

#### Machine Allocation (Auth Required)
```bash
PUT https://mara-hackathon-api.onrender.com/machines
# Body: {"air_miners": 0, "asic_compute": 5, "gpu_compute": 30, ...}
```

#### Site Registration
```bash
POST https://mara-hackathon-api.onrender.com/sites
# Body: {"api_key": "XXX", "name": "SiteName", "power": 1000000}
```

### API Client Usage
```python
from hackathon.api_client.client import MARAClient

# Initialize client
client = MARAClient(api_key="your_key")

# Fetch real-time prices
prices = client.get_prices()

# Get inventory
inventory = client.get_inventory()

# Allocate machines
allocation = client.allocate_machines({
    "air_miners": 0,
    "asic_compute": 5,
    "gpu_compute": 30
})
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_lane_a.py -v        # Data & Forecasting
pytest tests/test_robustness.py -v    # Robustness & Edge Cases
pytest tests/test_basic.py -v         # Basic Integration

# Run with coverage
pytest tests/ --cov=hackathon --cov-report=html
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component functionality
- **API Tests**: MARA API integration validation
- **Robustness Tests**: Error handling and edge cases
- **Performance Tests**: System performance validation

### Test Coverage
- **30+ comprehensive tests** with 100% pass rate
- **API integration testing** with fallback validation
- **Robustness testing** for missing data, extreme outliers
- **End-to-end simulation** with complete market cycles

## 🛠️ Development

### Project Structure
```
hackathon/
├── api_client/           # MARA API integration
├── control/              # System control and optimization
├── dispatch/             # Resource allocation and execution
├── forecasting/          # Advanced forecasting models
├── game_theory/          # Game theory and bidding strategies
├── llm_integration/      # LLM interface components
├── tests/                # Comprehensive test suite
├── ui/                   # Streamlit dashboard components
├── config.toml           # Configuration file
├── main.py              # Main application entry point
└── requirements.txt     # Python dependencies
```

### Code Quality
```bash
# Run linting
ruff check .

# Format code
ruff format .

# Type checking (if using mypy)
mypy hackathon/
```

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Add** tests for new functionality
5. **Run** the test suite
6. **Submit** a pull request

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Contribution Guidelines
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/jadenfix/hackathon.git
cd hackathon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available

# Run tests
pytest tests/ -v
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write comprehensive docstrings
- Include tests for new functionality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MARA Hackathon 2025** for providing the API and challenge
- **Open source community** for the excellent libraries used in this project
- **Contributors** who have helped improve the system

## 📞 Support

For support and questions:
- **Issues**: [GitHub Issues](https://github.com/jadenfix/hackathon/issues)
- **Documentation**: Check the [docs/](docs/) directory
- **Email**: [jadenfix123@gmail.com]

---

**GridPilot-GT is ready for the MARA Hackathon 2025! 🚀**

## Offline energy-cycle verification

```sh
python hackathon/main.py --mode gridpilot --simulate 1
PYTHONPATH=hackathon python -m pytest -q hackathon/tests/test_offline_cycle.py
```

Simulation uses explicitly synthetic market prices and inventory, executes
forecasting, bidding, allocation, cooling, and dispatch preparation, and never
fetches or submits to the market API. The default synthetic site is 1 MW
(1,000 kW). Dashboard dependencies are loaded when dashboard mode is selected.
The offline check verifies the cycle and external-call exclusion; it does not
validate real-market performance or the full historical test suite.
