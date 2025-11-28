# Travel Deal Optimizer

**Black Friday 2025 Edition**

A Python tool for tracking, evaluating, and comparing travel deals during Black Friday sales. Designed for family travel with sophisticated points-vs-cash analysis.

## Quick Start

```bash
# 1. Navigate to project
cd travel-deal-optimizer

# 2. Create virtual environment
uv venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run interactive mode
python -m app
```

## Features

- **Value Calculator**: Compares cash vs. points with CPP (cents-per-point) analysis
- **Deal Tracker**: Stores and tracks deals with historical pricing
- **Alert System**: Email notifications for excellent deals
- **Report Generator**: Comparison reports, decision matrices, booking guides
- **Interactive Entry**: Quick data entry interface for deal capture

## Usage

### Interactive Mode (Recommended)

```bash
python -m app
```

Opens a menu-driven interface for:
- Adding flight deals (cash or award)
- Adding hotel/resort deals (including all-inclusives)
- Building trip packages
- Viewing saved deals

### Quick CPP Calculation

```bash
# Syntax: --cpp <cash_price> <points> [taxes_fees]
python -m app --cpp 3200 180000 200

# Output:
# CPP Value: 1.67 cents/point
# ✅ Good value - worth booking
```

### Generate Reports

```bash
python -m app --report
```

Generates:
- `reports/comparison_[timestamp].md` - Side-by-side deal comparison
- `reports/summary_[timestamp].md` - Deal summary
- `reports/decision_matrix_[timestamp].md` - Scoring matrix
- `reports/booking_guide_[timestamp].md` - Step-by-step instructions
- `reports/data_[timestamp].json` - Raw data export

### Other Commands

```bash
python -m app --summary      # Quick summary of tracked deals
python -m app --compare      # Compare saved deals
python -m app --export       # Export to CSV
python -m app --test-alert   # Test email alerts
```

## Configuration

Edit `config/settings.yaml` to customize:

### Your Profile
```yaml
traveler:
  family_size: 4
  home_airport: "MSP"
  elite_status: "Diamond"
```

### Points Portfolio
```yaml
points_portfolio:
  amex_mr:
    balance: 170000
  delta_skymiles:
    balance: 100000
```

### Value Thresholds
```yaml
value_calc:
  # Minimum CPP to use points vs cash
  min_cpp:
    delta_skymiles: 1.0
    amex_mr: 1.2
    
  # Target CPP (good redemption)
  target_cpp:
    delta_skymiles: 1.5
    amex_mr: 2.0
```

### Email Alerts (Optional)
```yaml
alerts:
  email:
    enabled: true
    sender: "your.email@gmail.com"
    recipient: "your.email@gmail.com"
```

Set the app password via environment variable:
```bash
export EMAIL_APP_PASSWORD="your-gmail-app-password"
```

## Deal Quality Ratings

| Status | Meaning | Action |
|--------|---------|--------|
| 🔥 Excellent | 30%+ above target value | Book immediately |
| ✅ Good | Meets target CPP | Worth booking |
| 👍 Acceptable | Meets minimum CPP | Consider if convenient |
| ⚠️ Poor | Below minimum CPP | Pay cash instead |

## CPP Quick Reference

For Delta SkyMiles (baseline: 1.2cpp):
- **Under 1.0cpp**: Pay cash
- **1.0-1.5cpp**: Acceptable
- **1.5-2.0cpp**: Good value
- **2.0+ cpp**: Excellent

For Amex MR (baseline: 1.5cpp):
- **Under 1.2cpp**: Pay cash
- **1.2-2.0cpp**: Acceptable
- **2.0-2.5cpp**: Good value
- **2.5+ cpp**: Excellent

## Project Structure

```
travel-deal-optimizer/
├── app/
│   ├── __init__.py       # Package init
│   ├── __main__.py       # CLI entry point
│   ├── models.py         # Data models
│   ├── calculator.py     # Value calculations (the brain)
│   ├── tracker.py        # Deal storage/history
│   ├── alerts.py         # Email notifications
│   ├── entry.py          # Interactive data entry
│   └── reports.py        # Report generation
├── config/
│   └── settings.yaml     # Configuration
├── data/                 # Deal storage (auto-created)
├── reports/              # Generated reports (auto-created)
├── tests/                # Unit tests
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## Workflow: Black Friday Deal Hunting

**STOP-HERE Checkpoint 1: Setup (5 min)**

1. Clone/copy this project to your iMac
2. Set up virtualenv and install deps
3. Verify: `python -m app --summary`

**STOP-HERE Checkpoint 2: Baseline Capture (15 min)**

Before Black Friday starts (Nov 20-24):
1. Check Delta.com for MSP → target destinations (CUN, FCO, BCN, etc.)
2. Note the "normal" prices for your dates
3. Enter as deals with `python -m app --entry`

**STOP-HERE Checkpoint 3: Black Friday Monitoring (Daily, 10 min each)**

Nov 25 - Dec 2:
1. Check Delta.com, Google Flights, resort sites
2. Enter any deals that look good
3. Run `python -m app --compare` to see rankings
4. Watch for 🔥 Excellent ratings

**STOP-HERE Checkpoint 4: Decision & Booking**

When you see an excellent deal:
1. Run `python -m app --report`
2. Review the booking guide
3. If using points, initiate transfer FIRST (24-48 hrs)
4. Book flights, then accommodations

## Tips for Your Trip

### Mexico/Caribbean (All-Inclusive)

- **Target**: Under $350/person/night all-in
- **Excellent**: Under $250/person/night
- **Best brands**: Hyatt Ziva/Zilara, Excellence, Secrets
- **Tip**: Book through hotel direct for perks

### Southern Europe (March/April)

- **Great timing**: Shoulder season = fewer crowds
- **Target flights**: Under $800/person RT (MSP-FCO)
- **Award sweet spot**: ~60k Delta miles RT economy
- **Consider**: Virgin Atlantic for Delta metal flights

### Diamond Medallion Benefits

- Factor in ~40% upgrade probability on Delta
- Companion certificate: Can use for one person
- SkyClub access: Worth $30-50/visit for family

## Troubleshooting

**"Config not found"**
```bash
# The app creates defaults if missing, but ensure you're in the right directory
cd travel-deal-optimizer
python -m app
```

**"No deals to compare"**
```bash
# Add some deals first
python -m app --entry
```

**Alerts not sending**
```bash
# Test the alert system
python -m app --test-alert
# Check that EMAIL_APP_PASSWORD is set
echo $EMAIL_APP_PASSWORD
```

## Why This Approach?

**Why not full automation?**

1. Delta/Amex don't offer public APIs
2. Travel site scraping violates ToS and gets blocked
3. Black Friday traffic = aggressive bot detection
4. The real value is in the **calculation and comparison**, not scraping

**Where the tool adds value:**

- Consistent CPP calculations
- Side-by-side comparisons
- Historical tracking to verify "deals"
- Decision framework with clear recommendations
- Booking step generation

## License

Personal use. Built for Kyle's family trip planning.
