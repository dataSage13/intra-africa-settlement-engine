# Multi-Currency Intra-African Liquidity & FX Settlement Engine

A high-performance backend settlement engine inspired by the architecture of the **Pan-African Payment and Settlement System (PAPSS)**. It eliminates the traditional requirement of routing intra-African trade through USD or EUR intermediaries, allowing instant settlement using cross-currency graph routing and automated central bank liquidity guardrails.

## 🛠️ Tech Stack & CS Concepts Applied
- **Core Engineering:** Python 3, FastAPI, Uvicorn, SQLite
- **Graph Optimization:** NetworkX implementing **Dijkstra's Algorithm** to calculate optimal multi-hop currency settlement corridors when direct channels are illiquid.
- **Data Analytics:** NumPy variance modeling to calculate a **Liquidity Vulnerability Score (LVS)** based on rolling historical stress indicators.

## 📁 System Architecture
1. `database.py`: Pre-funded central bank ledger schema tracking reserve allocations.
2. `rates_ingestion.py`: Live ingestion pipeline updating cross-currency matrix metrics.
3. `router.py`: Graph routing state-machine ensuring transaction execution safety rails.
4. `main.py`: Restful API exposing execution routing and predictive stress analysis.

## 🚀 Local Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Initialize database matrices & fetch active live rates:
   ```bash
   python database.py
   python rates_ingestion.py
   ```
3. Boot the FastAPI gateway server:
   ```bash
   uvicorn main:app --reload
   ```
4. Access interactive API documentation at: `http://127.0.0`
