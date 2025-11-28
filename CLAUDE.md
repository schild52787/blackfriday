# Travel Deal Optimizer

## Project Overview

A CLI tool for tracking and evaluating Black Friday travel deals. Compares cash vs points redemptions with CPP (cents-per-point) analysis for family travel planning.

## Setup (Run First!)

```bash
chmod +x setup.sh && ./setup.sh
```

Or manually:
```bash
uv venv .venv && source .venv/bin/activate
pip install pyyaml pytest
python -m app --summary  # Verify
```

## Key Commands

```bash
# Quick CPP calculation
python -m app --cpp <cash_price> <points> [taxes]

# Interactive deal entry
python -m app --entry

# Generate reports
python -m app --report
```

## Agent-Friendly Commands (JSON Output)

These are designed for programmatic use by Claude Code:

```bash
# Add cash flight deal
python -m app add-flight --origin MSP --dest CUN --depart 2026-03-27 --return 2026-04-03 --price 1600

# Add award flight deal  
python -m app add-award --origin MSP --dest CUN --depart 2026-03-27 --return 2026-04-03 --points 25000 --cash-price 1800

# Add all-inclusive resort
python -m app add-resort --dest CUN --property "Hyatt Ziva" --checkin 2026-03-27 --checkout 2026-04-03 --total 7000

# Get summary (JSON)
python -m app --summary --json

# Compare deals (JSON)
python -m app --compare --json

# CPP calculation (JSON)
python -m app --cpp 3200 180000 200 --json
```

## MCP Server Integration

To use as an MCP server with Claude Code:

1. Add to `~/.claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "travel-deals": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/path/to/travel-deal-optimizer"
    }
  }
}
```

2. Available MCP tools:
   - `calculate_cpp` - CPP value calculation
   - `add_flight_deal` - Add cash flight
   - `add_award_flight` - Add award flight
   - `add_resort_deal` - Add all-inclusive
   - `list_deals` - List tracked deals
   - `compare_deals` - Compare and rank
   - `get_summary` - Summary stats
   - `generate_report` - Create reports

## Architecture

```
app/
├── calculator.py   # Value calculations (CPP, comparisons)
├── tracker.py      # Deal storage (JSON in data/)
├── alerts.py       # Email notifications  
├── reports.py      # Markdown/JSON reports
├── entry.py        # Interactive CLI
├── mcp_server.py   # MCP server for Claude Code
└── __main__.py     # Entry point
```

## Data Storage

- `data/deals.json` - All tracked deals
- `data/price_history.json` - Historical prices
- `data/baseline_prices.json` - Pre-configured baselines

## User Context

- **Traveler**: Kyle (Diamond Medallion, MSP-based)
- **Family**: 4 people (2 adults, 2 kids ages 5-7)
- **Trip**: March 27 - April 5, 2026
- **Budget**: $12k ceiling, $10k target
- **Points**: 170k Amex MR, 100k Delta SkyMiles
- **Targets**: Mexico/Caribbean all-inclusive OR Southern Europe

## CPP Quick Reference

| Currency | Minimum | Target | Excellent |
|----------|---------|--------|-----------|
| Delta SM | 1.0 | 1.5 | 2.0+ |
| Amex MR | 1.2 | 2.0 | 2.5+ |

## Common Tasks for Claude Code

**"Check if this flight is a good deal"**
→ `python -m app --cpp <cash> <points> <taxes> --json`

**"Add a deal I found"**
→ `python -m app add-flight ...` or `add-award ...` or `add-resort ...`

**"Compare my options"**
→ `python -m app --compare --json`

**"What's my best option?"**
→ `python -m app --compare --json` (check "best" field)
