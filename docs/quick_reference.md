# Quick Reference Card

## Daily Commands

```bash
# Quick CPP check
python -m app --cpp 3200 180000 200

# Enter a deal
python -m app --entry

# Compare all deals
python -m app --compare

# Generate full reports
python -m app --report

# Show summary
python -m app --summary
```

## CPP Targets

| Currency | Pay Cash | Acceptable | Good | Excellent |
|----------|----------|------------|------|-----------|
| Delta SM | <1.0 | 1.0-1.5 | 1.5-2.0 | 2.0+ |
| Amex MR | <1.2 | 1.2-2.0 | 2.0-2.5 | 2.5+ |
| Hilton | <0.4 | 0.4-0.6 | 0.6-0.8 | 0.8+ |

## All-Inclusive Targets (Per Person/Night)

| Rating | Price |
|--------|-------|
| 🔥 Excellent | Under $250 |
| ✅ Good | $250-350 |
| 👍 Acceptable | $350-450 |
| ⚠️ Pass | Over $450 |

## Flight Targets (Family of 4, RT)

| Destination | Cash Target | Award Target |
|-------------|-------------|--------------|
| CUN | Under $1,600 | Under 100k |
| FCO | Under $3,200 | Under 240k |
| BCN | Under $3,000 | Under 200k |

## Black Friday Checklist

**Before (Nov 20-24):**
- [ ] Capture baseline prices
- [ ] Set up email alerts (optional)
- [ ] Verify tool runs: `python -m app --summary`

**During (Nov 25 - Dec 2):**
- [ ] Check Delta.com AM & PM
- [ ] Check Google Flights
- [ ] Enter deals: `python -m app --entry`
- [ ] Compare: `python -m app --compare`
- [ ] Watch for 🔥 ratings

**Booking (when you find a winner):**
- [ ] Generate report: `python -m app --report`
- [ ] If award: Transfer points FIRST (24-48hr)
- [ ] Book flights
- [ ] Book hotel/resort
- [ ] Confirm all reservations

## Your Portfolio

- **Amex MR:** 170,000
- **Delta SkyMiles:** 100,000
- **Budget Ceiling:** $12,000
- **Target Budget:** $10,000
