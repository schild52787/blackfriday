# Troubleshooting Guide & FAQ

## Common Issues

### Installation Problems

**Issue: `ModuleNotFoundError: No module named 'yaml'`**

```bash
# Solution: Install PyYAML
pip install pyyaml --break-system-packages
# Or in a venv:
pip install pyyaml
```

**Issue: `command not found: python`**

```bash
# On macOS, use python3
python3 -m app

# Or create alias
echo 'alias python=python3' >> ~/.zshrc
source ~/.zshrc
```

**Issue: Virtual environment not activating**

```bash
# Make sure you're using uv or standard venv
uv venv .venv
source .venv/bin/activate

# Verify:
which python  # Should show .venv path
```

---

### Runtime Errors

**Issue: `Config not found at config/settings.yaml`**

The app creates defaults, but ensure you're in the right directory:

```bash
cd travel-deal-optimizer
ls config/  # Should show settings.yaml
python -m app
```

**Issue: `No deals to compare`**

You need to add deals first:

```bash
python -m app --entry  # Add some deals
python -m app --compare  # Then compare
```

**Issue: Data not saving**

Check that the `data/` directory exists and is writable:

```bash
ls -la data/
# Should show deals.json, price_history.json, etc.
```

---

### Alert System Issues

**Issue: Alerts not sending**

1. Check email configuration in `config/settings.yaml`:
```yaml
alerts:
  email:
    enabled: true
    sender: "your.email@gmail.com"
    recipient: "your.email@gmail.com"
```

2. Set the app password environment variable:
```bash
export EMAIL_APP_PASSWORD="your-16-char-app-password"
```

3. For Gmail, you need an "App Password":
   - Go to Google Account → Security → 2-Step Verification
   - Scroll down to "App passwords"
   - Generate new password for "Mail" on "Mac"
   - Use this 16-character password

4. Test:
```bash
python -m app --test-alert
```

**Issue: Alerts during quiet hours**

By default, alerts won't send between 10pm-7am Central. To override:

```yaml
alerts:
  quiet_hours:
    start: "23:00"  # Later start
    end: "06:00"    # Earlier end
```

---

## FAQ

### General

**Q: Why doesn't this scrape Delta/travel sites automatically?**

A: Three reasons:
1. No public APIs for award availability
2. Scraping violates Terms of Service
3. Black Friday traffic triggers aggressive bot detection

The tool's value is in calculations and comparisons, not data collection. Manually checking prices takes 5 minutes; the analysis would take hours by hand.

**Q: How often should I check for deals?**

A: During Black Friday week (Nov 25 - Dec 2):
- Check morning (~8am) and evening (~8pm)
- Enter any promising deals into the tool
- Run `--compare` to see rankings

**Q: What's a good CPP value?**

For Delta SkyMiles:
- 1.0-1.2cpp = Minimum acceptable
- 1.5cpp = Good value
- 2.0+ cpp = Excellent (book it!)

For Amex MR:
- 1.2-1.5cpp = Minimum acceptable
- 2.0cpp = Good value
- 2.5+ cpp = Excellent

**Q: Should I transfer Amex MR to Delta or use directly?**

Generally:
- **Transfer to Delta** for award flights (1:1 ratio)
- **Transfer to partners** (Virgin Atlantic, Air France) for potential better rates on specific routes
- **Never** transfer to hotels (poor value except Hilton for specific promos)

---

### Technical

**Q: Can I add custom destinations?**

Yes! Edit `config/settings.yaml`:

```yaml
destinations:
  custom:
    priority: 3
    type: "hotel_separate"
    airports:
      - "LHR"  # London
      - "CDG"  # Paris
```

**Q: How do I export data to a spreadsheet?**

```bash
python -m app --export -o my_deals.csv
```

Then open in Excel or Google Sheets.

**Q: Can I run this on a schedule?**

Yes, use cron (macOS/Linux):

```bash
# Edit crontab
crontab -e

# Add line to run at 8am and 8pm daily:
0 8,20 * * * cd /path/to/travel-deal-optimizer && python -m app --report
```

**Q: How do I reset all data?**

```bash
rm -rf data/*.json
python -m app --summary  # Fresh start
```

---

### Trip-Specific

**Q: All-inclusive vs separate bookings for Mexico?**

For families with young kids: **All-inclusive recommended**
- Predictable costs
- No meal logistics
- Kids activities included
- Less stress

Target: Under $350/person/night all-in for a quality resort.

**Q: Best time to book for March/April travel?**

- **Black Friday week**: Best for flights (Nov 25-Dec 2)
- **January**: Good for all-inclusive packages
- **6-8 weeks before**: Last chance for award availability

**Q: Diamond Medallion - should I factor in upgrades?**

The tool adds ~40% upgrade probability value for Delta flights. This is conservative; actual rates vary by route. For MSP routes:
- CUN: Lower upgrade rates (popular leisure)
- FCO: Higher upgrade rates (business traffic)

---

## Getting Help

If you encounter issues not covered here:

1. Check the logs: `data/optimizer.log`
2. Run with verbose mode: `python -m app -v`
3. Verify config syntax: `python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"`
