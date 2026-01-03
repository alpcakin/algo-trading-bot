# Algorithmic Trading Bot

Price action based trend-following strategy for forex markets.

## Strategy Overview
- **Timeframe:** 1 minute
- **Pairs:** EURUSD, GBPUSD, USDJPY
- **Trading Hours:** 13:00 - 20:00 (Hungary time)
- **Entry Logic:** Scale in on every trend-aligned candle
- **Exit Logic:** Trend reversal or individual TP hit

## Setup

### 1. Install MT5
Download and install MetaTrader 5

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Settings
Edit `config.py` with your MT5 credentials (optional for data collection)

## Usage

### Collect Data from MT5
```bash
python src/data_collector.py
```

### Run Backtest
```bash
python src/backtester.py
```

## Project Structure
```
├── src/              # Source code
├── data/             # Historical data
├── notebooks/        # Analysis notebooks
└── tests/            # Unit tests
```

## Strategy Details

### Trend Determination
- Trend changes when price closes beyond last counter-trend candle's high/low
- Mitigation level updates with each new high/low
- Bias remains until opposite mitigation is broken

### Position Management
- Risk: 0.01% of balance per candle
- Individual TP: 15 pips from entry
- Emergency SL: 2% of balance (wick protection)
- News filter: No trading 15min before & 30min after high-impact news

## Development Status
🚧 In Development