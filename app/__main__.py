#!/usr/bin/env python3
"""
Travel Deal Optimizer - Main CLI

Black Friday 2025 Edition
For: Kyle's Family Trip (March 2026)

Usage:
    python -m app                    # Interactive menu
    python -m app --entry            # Quick deal entry
    python -m app --report           # Generate reports
    python -m app --compare          # Compare saved deals
    python -m app --cpp 800 45000 50 # Quick CPP calculation
    
Agent-friendly commands (JSON output):
    python -m app add-flight --origin MSP --dest CUN --depart 2026-03-27 --return 2026-04-03 --price 1600
    python -m app add-award --origin MSP --dest CUN --depart 2026-03-27 --return 2026-04-03 --points 25000
    python -m app add-resort --dest CUN --property "Hyatt Ziva" --checkin 2026-03-27 --checkout 2026-04-03 --total 7000
    python -m app --summary --json
    python -m app --compare --json
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime, date

from .models import DealType, DealStatus, FlightDeal, HotelDeal, TripPackage, CabinClass
from .calculator import ValueCalculator, ValueConfig, quick_cpp_calc, should_use_points
from .tracker import DealTracker
from .alerts import AlertSystem, create_alert_system
from .reports import ReportGenerator
from .entry import interactive_menu, DataEntry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/optimizer.log')
    ]
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Ensure required directories exist."""
    Path("data").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    Path("config").mkdir(exist_ok=True)


def load_components(config_path: str = "config/settings.yaml"):
    """Load all application components."""
    # Check if config exists
    if not Path(config_path).exists():
        print(f"⚠️ Config not found at {config_path}")
        print("Creating default configuration...")
        # Use defaults
        config = ValueConfig(
            baseline_cpp={"delta_skymiles": 1.2, "amex_mr": 1.5, "hilton": 0.5},
            target_cpp={"delta_skymiles": 1.5, "amex_mr": 2.0, "hilton": 0.6},
            min_cpp={"delta_skymiles": 1.0, "amex_mr": 1.2, "hilton": 0.4},
        )
    else:
        config = ValueConfig.from_yaml(config_path)
    
    calculator = ValueCalculator(config)
    tracker = DealTracker("data")
    reporter = ReportGenerator("reports")
    
    try:
        alert_system = create_alert_system(config_path)
    except Exception:
        alert_system = AlertSystem()
    
    return calculator, tracker, reporter, alert_system


def cmd_interactive(args):
    """Run interactive menu."""
    calculator, tracker, _, _ = load_components(args.config)
    interactive_menu(calculator, tracker)


def cmd_entry(args):
    """Quick deal entry mode."""
    calculator, tracker, _, _ = load_components(args.config)
    entry = DataEntry(calculator, tracker)
    
    print("\nQuick Entry Mode")
    print("=" * 40)
    print("1. Flight (Cash)")
    print("2. Flight (Award)")
    print("3. All-Inclusive Resort")
    print("4. Hotel")
    
    choice = input("\nSelect type (1-4): ").strip()
    
    if choice == "1":
        entry.quick_flight_cash()
    elif choice == "2":
        entry.quick_flight_award()
    elif choice == "3":
        entry.quick_all_inclusive()
    elif choice == "4":
        entry.quick_hotel_cash()
    else:
        print("Invalid selection")


def cmd_report(args):
    """Generate reports."""
    calculator, tracker, reporter, _ = load_components(args.config)
    
    print("\n📊 Generating Reports...")
    
    # Get all deals
    deals = tracker.get_all_deals()
    
    if not deals:
        print("No deals to report on. Add some deals first!")
        return
    
    # Build comparison matrix from packages (or create packages from deals)
    packages = []
    for deal in deals:
        if deal.get('flight') or deal.get('hotel'):
            # Already a package
            packages.append(deal)
        elif 'flight' in deal.get('deal_type', ''):
            # Create simple package from flight
            flight = FlightDeal.from_dict(deal)
            pkg = TripPackage(
                destination=deal['destination'],
                departure_date=flight.departure_date,
                return_date=flight.return_date,
                flight=flight
            )
            pkg = calculator.evaluate_trip_package(pkg)
            packages.append(pkg.to_dict())
    
    if packages:
        comparison = calculator.compare_options([
            TripPackage(
                destination=p.get('destination', ''),
                departure_date=datetime.fromisoformat(p['departure_date']).date() if isinstance(p.get('departure_date'), str) else p.get('departure_date'),
                return_date=datetime.fromisoformat(p['return_date']).date() if isinstance(p.get('return_date'), str) else p.get('return_date'),
                total_cash_cost=p.get('total_cash_cost', 0),
                status=DealStatus(p.get('status', 'acceptable'))
            ) for p in packages if p.get('departure_date') and p.get('return_date')
        ]) if packages else {}
    else:
        comparison = {"ranked_options": [], "note": "No complete packages to compare"}
    
    # Generate all reports
    saved = reporter.generate_all_reports(
        comparison_matrix=comparison,
        deals=deals,
        best_package=packages[0] if packages else None,
        points_portfolio={
            "amex_mr": 170000,
            "delta_skymiles": 100000
        }
    )
    
    print("\n✅ Reports generated:")
    for name, path in saved.items():
        print(f"   - {name}: {path}")
    
    # Print summary
    summary = tracker.get_deals_summary()
    print(f"\n📈 Summary:")
    print(f"   Total deals: {summary['total_deals']}")
    print(f"   Excellent: {summary.get('excellent_count', 0)}")
    print(f"   Good: {summary.get('good_count', 0)}")


def cmd_compare(args):
    """Compare saved deals."""
    calculator, tracker, reporter, _ = load_components(args.config)
    
    deals = tracker.get_all_deals()
    
    if len(deals) < 2:
        print("Need at least 2 deals to compare. Add more deals first!")
        return
    
    print("\n📊 Deal Comparison")
    print("=" * 60)
    
    # Sort by status
    status_order = {
        'excellent': 0, 'good': 1, 'acceptable': 2, 'poor': 3, 'expired': 4
    }
    deals.sort(key=lambda d: status_order.get(d.get('status', 'poor'), 5))
    
    for i, deal in enumerate(deals[:10], 1):
        status = deal.get('status', 'unknown')
        emoji = {'excellent': '🔥', 'good': '✅', 'acceptable': '👍', 'poor': '⚠️'}.get(status, '❓')
        
        dest = deal.get('destination', 'Unknown')
        price = deal.get('price_cash') or deal.get('total_price_cash') or deal.get('total_cash_cost', 0)
        cpp = deal.get('cpp_value')
        
        print(f"{i}. {emoji} {dest}")
        print(f"   Price: ${price:,.0f}", end="")
        if cpp:
            print(f" | CPP: {cpp:.2f}")
        else:
            print()
        print(f"   Status: {status}")
        print()


def cmd_cpp(args):
    """Quick CPP calculation."""
    if len(args.values) < 2:
        print("Usage: --cpp <cash_price> <points> [taxes]")
        print("Example: --cpp 800 45000 50")
        return
    
    cash = float(args.values[0])
    points = int(args.values[1])
    taxes = float(args.values[2]) if len(args.values) > 2 else 0
    
    cpp = quick_cpp_calc(cash, points, taxes)
    
    print(f"\n💰 CPP Calculation")
    print(f"   Cash price: ${cash:,.0f}")
    print(f"   Points: {points:,}")
    print(f"   Taxes/fees: ${taxes:,.0f}")
    print(f"\n   ➡️ CPP Value: {cpp:.2f} cents/point")
    
    # Quick assessment
    if cpp >= 2.0:
        print("   🔥 EXCELLENT value - book it!")
    elif cpp >= 1.5:
        print("   ✅ Good value - worth booking")
    elif cpp >= 1.2:
        print("   👍 Acceptable - meets threshold")
    else:
        print("   ⚠️ Below threshold - consider paying cash")


def cmd_summary(args):
    """Show summary of tracked deals."""
    _, tracker, _, _ = load_components(args.config)
    
    summary = tracker.get_deals_summary()
    
    print("\n📈 Deal Tracker Summary")
    print("=" * 40)
    print(f"Total deals tracked: {summary['total_deals']}")
    print()
    
    print("By Status:")
    for status, count in summary.get('by_status', {}).items():
        emoji = {'excellent': '🔥', 'good': '✅', 'acceptable': '👍', 'poor': '⚠️'}.get(status, '❓')
        print(f"  {emoji} {status}: {count}")
    
    print()
    print("By Destination:")
    for dest, count in summary.get('by_destination', {}).items():
        print(f"  📍 {dest}: {count}")
    
    # Show excellent deals
    excellent = tracker.get_excellent_deals()
    if excellent:
        print()
        print("🔥 Excellent Deals:")
        for deal in excellent[:5]:
            dest = deal.get('destination', 'Unknown')
            price = deal.get('price_cash') or deal.get('total_cash_cost', 0)
            print(f"  - {dest}: ${price:,.0f}")


def cmd_export(args):
    """Export deals to CSV."""
    _, tracker, _, _ = load_components(args.config)
    
    output_path = args.output or "reports/deals_export.csv"
    csv_content = tracker.export_deals_csv(output_path)
    
    if getattr(args, 'json', False):
        print(json.dumps({"success": True, "path": output_path}))
    else:
        print(f"\n✅ Deals exported to: {output_path}")


def cmd_alert_test(args):
    """Test alert system."""
    _, _, _, alert_system = load_components(args.config)
    
    print("\n🔔 Testing Alert System...")
    
    test_deal = {
        '_key': 'test_deal',
        'status': 'excellent',
        'destination': 'CUN',
        'deal_type': 'flight_cash',
        'origin': 'MSP',
        'departure_date': '2026-03-27',
        'return_date': '2026-04-03',
        'price_cash': 1200,
        'airline': 'Delta'
    }
    
    success = alert_system.alert_deal(test_deal, force=True)
    
    if success:
        print("✅ Test alert sent successfully!")
    else:
        print("⚠️ Alert system not fully configured (check email settings)")
        print("   Alert was printed to console instead")


# =============================================================================
# AGENT-FRIENDLY COMMANDS (Programmatic with JSON output)
# =============================================================================

def cmd_add_flight(args):
    """Add a cash flight deal programmatically."""
    calculator, tracker, _, _ = load_components(args.config)
    
    deal = FlightDeal(
        origin=args.origin.upper(),
        destination=args.dest.upper(),
        departure_date=date.fromisoformat(args.depart),
        return_date=date.fromisoformat(args.return_date),
        deal_type=DealType.FLIGHT_CASH,
        price_cash=args.price,
        airline=args.airline or "Delta",
        stops=args.stops or 0,
        source=args.source or "CLI",
        found_at=datetime.now()
    )
    
    deal = calculator.evaluate_flight_deal(deal)
    key = tracker.add_deal(deal)
    
    result = {
        "success": True,
        "deal_key": key,
        "status": deal.status.value,
        "total_value": deal.total_value,
        "route": f"{deal.origin} → {deal.destination}"
    }
    
    print(json.dumps(result, indent=2))


def cmd_add_award(args):
    """Add an award flight deal programmatically."""
    calculator, tracker, _, _ = load_components(args.config)
    
    deal = FlightDeal(
        origin=args.origin.upper(),
        destination=args.dest.upper(),
        departure_date=date.fromisoformat(args.depart),
        return_date=date.fromisoformat(args.return_date),
        deal_type=DealType.FLIGHT_AWARD,
        price_points=args.points,
        points_currency=args.currency or "delta_skymiles",
        taxes_fees=args.taxes or 5.60,
        airline=args.airline or "Delta",
        cabin_class=CabinClass(args.cabin or "economy"),
        source="CLI",
        found_at=datetime.now()
    )
    
    cash_comparison = args.cash_price
    deal = calculator.evaluate_flight_deal(deal, baseline_cash_price=cash_comparison)
    key = tracker.add_deal(deal)
    
    result = {
        "success": True,
        "deal_key": key,
        "status": deal.status.value,
        "cpp_value": deal.cpp_value,
        "route": f"{deal.origin} → {deal.destination}"
    }
    
    print(json.dumps(result, indent=2))


def cmd_add_resort(args):
    """Add an all-inclusive resort deal programmatically."""
    calculator, tracker, _, _ = load_components(args.config)
    
    deal = HotelDeal(
        destination=args.dest.upper(),
        property_name=args.property,
        check_in=date.fromisoformat(args.checkin),
        check_out=date.fromisoformat(args.checkout),
        deal_type=DealType.ALL_INCLUSIVE,
        total_price_cash=args.total,
        is_all_inclusive=True,
        includes_meals=True,
        includes_drinks=True,
        source=args.source or "CLI",
        found_at=datetime.now()
    )
    
    deal = calculator.evaluate_hotel_deal(deal)
    key = tracker.add_deal(deal)
    
    result = {
        "success": True,
        "deal_key": key,
        "status": deal.status.value,
        "per_person_per_night": deal.per_person_per_night,
        "property": deal.property_name
    }
    
    print(json.dumps(result, indent=2))


def cmd_cpp_json(args):
    """CPP calculation with JSON output."""
    if len(args.values) < 2:
        print(json.dumps({"error": "Usage: --cpp <cash_price> <points> [taxes]"}))
        return
    
    cash = float(args.values[0])
    points = int(args.values[1])
    taxes = float(args.values[2]) if len(args.values) > 2 else 0
    
    cpp = quick_cpp_calc(cash, points, taxes)
    
    # Determine status
    if cpp >= 2.0:
        status = "excellent"
    elif cpp >= 1.5:
        status = "good"
    elif cpp >= 1.2:
        status = "acceptable"
    else:
        status = "poor"
    
    result = {
        "cpp": cpp,
        "status": status,
        "cash_price": cash,
        "points": points,
        "taxes": taxes
    }
    
    print(json.dumps(result, indent=2))


def main():
    """Main entry point."""
    setup_environment()
    
    parser = argparse.ArgumentParser(
        description="Travel Deal Optimizer - Black Friday 2025",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app                     # Interactive menu
  python -m app --entry             # Quick deal entry
  python -m app --report            # Generate reports
  python -m app --compare           # Compare deals
  python -m app --cpp 800 45000 50  # Calculate CPP
  python -m app --summary           # Show summary
  python -m app --export            # Export to CSV
  
Agent-friendly (JSON output):
  python -m app add-flight --origin MSP --dest CUN --depart 2026-03-27 --return 2026-04-03 --price 1600
  python -m app add-award --origin MSP --dest CUN --depart 2026-03-27 --return 2026-04-03 --points 25000
  python -m app add-resort --dest CUN --property "Hyatt Ziva" --checkin 2026-03-27 --checkout 2026-04-03 --total 7000
  python -m app --summary --json
  python -m app --compare --json
        """
    )
    
    # Global arguments
    parser.add_argument('--config', '-c', default='config/settings.yaml', help='Config file path')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON (agent-friendly)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Subparsers for agent commands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # add-flight subcommand
    flight_parser = subparsers.add_parser('add-flight', help='Add cash flight deal')
    flight_parser.add_argument('--origin', required=True, help='Origin airport (e.g., MSP)')
    flight_parser.add_argument('--dest', required=True, help='Destination airport (e.g., CUN)')
    flight_parser.add_argument('--depart', required=True, help='Departure date (YYYY-MM-DD)')
    flight_parser.add_argument('--return', dest='return_date', required=True, help='Return date (YYYY-MM-DD)')
    flight_parser.add_argument('--price', type=float, required=True, help='Total price for family')
    flight_parser.add_argument('--airline', default='Delta', help='Airline name')
    flight_parser.add_argument('--stops', type=int, default=0, help='Number of stops')
    flight_parser.add_argument('--source', default='CLI', help='Deal source')
    
    # add-award subcommand
    award_parser = subparsers.add_parser('add-award', help='Add award flight deal')
    award_parser.add_argument('--origin', required=True, help='Origin airport')
    award_parser.add_argument('--dest', required=True, help='Destination airport')
    award_parser.add_argument('--depart', required=True, help='Departure date (YYYY-MM-DD)')
    award_parser.add_argument('--return', dest='return_date', required=True, help='Return date')
    award_parser.add_argument('--points', type=int, required=True, help='Points per person')
    award_parser.add_argument('--currency', default='delta_skymiles', help='Points currency')
    award_parser.add_argument('--taxes', type=float, default=5.60, help='Taxes per person')
    award_parser.add_argument('--cash-price', type=float, help='Cash comparison price (for CPP)')
    award_parser.add_argument('--airline', default='Delta', help='Airline')
    award_parser.add_argument('--cabin', default='economy', help='Cabin class')
    
    # add-resort subcommand
    resort_parser = subparsers.add_parser('add-resort', help='Add all-inclusive resort deal')
    resort_parser.add_argument('--dest', required=True, help='Destination airport code')
    resort_parser.add_argument('--property', required=True, help='Resort name')
    resort_parser.add_argument('--checkin', required=True, help='Check-in date (YYYY-MM-DD)')
    resort_parser.add_argument('--checkout', required=True, help='Check-out date')
    resort_parser.add_argument('--total', type=float, required=True, help='Total price for family')
    resort_parser.add_argument('--source', default='CLI', help='Deal source')
    
    # Legacy flag arguments
    parser.add_argument('--entry', '-e', action='store_true', help='Quick deal entry mode')
    parser.add_argument('--report', '-r', action='store_true', help='Generate reports')
    parser.add_argument('--compare', action='store_true', help='Compare saved deals')
    parser.add_argument('--cpp', nargs='*', dest='values', metavar='VALUE', help='CPP calculation')
    parser.add_argument('--summary', '-s', action='store_true', help='Show deal summary')
    parser.add_argument('--export', action='store_true', help='Export deals to CSV')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--test-alert', action='store_true', help='Test alert system')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Route to appropriate command
    if args.command == 'add-flight':
        cmd_add_flight(args)
    elif args.command == 'add-award':
        cmd_add_award(args)
    elif args.command == 'add-resort':
        cmd_add_resort(args)
    elif args.entry:
        cmd_entry(args)
    elif args.report:
        cmd_report(args)
    elif args.compare:
        if args.json:
            cmd_compare_json(args)
        else:
            cmd_compare(args)
    elif args.values is not None:
        if args.json:
            cmd_cpp_json(args)
        else:
            cmd_cpp(args)
    elif args.summary:
        if args.json:
            cmd_summary_json(args)
        else:
            cmd_summary(args)
    elif args.export:
        cmd_export(args)
    elif args.test_alert:
        cmd_alert_test(args)
    else:
        # Default: interactive menu
        cmd_interactive(args)


def cmd_summary_json(args):
    """Summary with JSON output."""
    _, tracker, _, _ = load_components(args.config)
    summary = tracker.get_deals_summary()
    print(json.dumps(summary, indent=2))


def cmd_compare_json(args):
    """Compare with JSON output."""
    _, tracker, _, _ = load_components(args.config)
    deals = tracker.get_all_deals()
    
    if not deals:
        print(json.dumps({"deals": [], "message": "No deals to compare"}))
        return
    
    status_order = {'excellent': 0, 'good': 1, 'acceptable': 2, 'poor': 3}
    deals.sort(key=lambda d: status_order.get(d.get('status', 'poor'), 5))
    
    ranked = []
    for i, d in enumerate(deals[:10], 1):
        ranked.append({
            "rank": i,
            "destination": d.get("destination"),
            "status": d.get("status"),
            "price": d.get("price_cash") or d.get("total_price_cash") or d.get("total_cash_cost", 0),
            "cpp": d.get("cpp_value"),
            "type": d.get("deal_type")
        })
    
    result = {
        "total": len(deals),
        "ranked_options": ranked,
        "best": ranked[0] if ranked else None
    }
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
