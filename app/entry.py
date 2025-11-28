"""
Data Entry Interface

Interactive interface for manually entering deal data.
Designed to be quick and efficient for rapid deal capture.
"""

from datetime import date, datetime
from typing import Optional, Tuple
import sys

from .models import (
    FlightDeal, HotelDeal, TripPackage,
    DealType, CabinClass, DealStatus
)
from .calculator import ValueCalculator, ValueConfig
from .tracker import DealTracker


class DataEntry:
    """
    Interactive data entry for travel deals.
    
    Two modes:
    1. Quick entry - minimal required fields
    2. Full entry - all fields with validation
    """
    
    def __init__(
        self, 
        calculator: ValueCalculator, 
        tracker: DealTracker
    ):
        self.calc = calculator
        self.tracker = tracker
    
    def _prompt(
        self, 
        message: str, 
        default: str = None,
        required: bool = True
    ) -> str:
        """Get input with optional default."""
        if default:
            display = f"{message} [{default}]: "
        else:
            display = f"{message}: "
        
        value = input(display).strip()
        
        if not value and default:
            return default
        if not value and required:
            print("  ⚠️ This field is required")
            return self._prompt(message, default, required)
        
        return value
    
    def _prompt_float(
        self, 
        message: str, 
        default: float = None
    ) -> Optional[float]:
        """Get float input."""
        default_str = str(default) if default else None
        value = self._prompt(message, default_str, required=False)
        
        if not value:
            return default
        
        try:
            return float(value.replace(',', '').replace('$', ''))
        except ValueError:
            print("  ⚠️ Please enter a valid number")
            return self._prompt_float(message, default)
    
    def _prompt_int(
        self, 
        message: str, 
        default: int = None
    ) -> Optional[int]:
        """Get integer input."""
        default_str = str(default) if default else None
        value = self._prompt(message, default_str, required=False)
        
        if not value:
            return default
        
        try:
            return int(value.replace(',', ''))
        except ValueError:
            print("  ⚠️ Please enter a valid number")
            return self._prompt_int(message, default)
    
    def _prompt_date(
        self, 
        message: str, 
        default: date = None
    ) -> date:
        """Get date input (YYYY-MM-DD)."""
        default_str = default.isoformat() if default else None
        value = self._prompt(message + " (YYYY-MM-DD)", default_str)
        
        try:
            return date.fromisoformat(value)
        except ValueError:
            print("  ⚠️ Please enter date as YYYY-MM-DD")
            return self._prompt_date(message, default)
    
    def _prompt_choice(
        self, 
        message: str, 
        choices: list,
        default: str = None
    ) -> str:
        """Get choice from list."""
        choices_str = ", ".join(choices)
        print(f"  Options: {choices_str}")
        
        value = self._prompt(message, default)
        
        if value.lower() not in [c.lower() for c in choices]:
            print(f"  ⚠️ Please choose from: {choices_str}")
            return self._prompt_choice(message, choices, default)
        
        return value.lower()
    
    # -------------------------------------------------------------------------
    # Quick Entry Modes
    # -------------------------------------------------------------------------
    
    def quick_flight_cash(self) -> FlightDeal:
        """
        Quick entry for cash flight deals.
        Minimum fields for fast capture.
        """
        print("\n=== Quick Flight Entry (Cash) ===\n")
        
        # Essential fields
        origin = self._prompt("Origin airport", "MSP")
        destination = self._prompt("Destination airport")
        departure = self._prompt_date("Departure date")
        return_date = self._prompt_date("Return date")
        price = self._prompt_float("Total price (family of 4)")
        
        # Optional
        airline = self._prompt("Airline", "Delta", required=False)
        stops = self._prompt_int("Number of stops", 0)
        source = self._prompt("Source (where you found it)", "Manual", required=False)
        
        deal = FlightDeal(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=departure,
            return_date=return_date,
            deal_type=DealType.FLIGHT_CASH,
            price_cash=price,
            airline=airline,
            stops=stops or 0,
            source=source or "Manual",
            found_at=datetime.now()
        )
        
        # Evaluate and save
        deal = self.calc.evaluate_flight_deal(deal)
        self.tracker.add_deal(deal)
        
        self._print_deal_result(deal)
        return deal
    
    def quick_flight_award(self) -> FlightDeal:
        """Quick entry for award flight deals."""
        print("\n=== Quick Flight Entry (Award) ===\n")
        
        # Essential fields
        origin = self._prompt("Origin airport", "MSP")
        destination = self._prompt("Destination airport")
        departure = self._prompt_date("Departure date")
        return_date = self._prompt_date("Return date")
        
        # Award specifics
        points_per_person = self._prompt_int("Points per person (one-way × 2 if RT)")
        taxes_per_person = self._prompt_float("Taxes/fees per person", 5.60)
        
        currency = self._prompt_choice(
            "Points currency",
            ["delta_skymiles", "amex_mr", "virgin_atlantic", "air_france", "british_airways"],
            "delta_skymiles"
        )
        
        # Cash comparison (for CPP calc)
        cash_equivalent = self._prompt_float(
            "What's the cash price for same flight? (for CPP calc)",
            None
        )
        
        # Optional
        airline = self._prompt("Airline", "Delta", required=False)
        cabin = self._prompt_choice(
            "Cabin class",
            ["economy", "premium_economy", "business", "first"],
            "economy"
        )
        
        deal = FlightDeal(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=departure,
            return_date=return_date,
            deal_type=DealType.FLIGHT_AWARD,
            price_points=points_per_person,
            points_currency=currency,
            taxes_fees=taxes_per_person,
            airline=airline,
            cabin_class=CabinClass(cabin),
            source="Manual",
            found_at=datetime.now()
        )
        
        # Evaluate
        deal = self.calc.evaluate_flight_deal(deal, baseline_cash_price=cash_equivalent)
        self.tracker.add_deal(deal)
        
        self._print_deal_result(deal)
        return deal
    
    def quick_all_inclusive(self) -> HotelDeal:
        """Quick entry for all-inclusive resort deals."""
        print("\n=== Quick All-Inclusive Entry ===\n")
        
        # Essential fields
        destination = self._prompt("Destination (airport code)")
        property_name = self._prompt("Resort name")
        check_in = self._prompt_date("Check-in date")
        check_out = self._prompt_date("Check-out date")
        
        total_price = self._prompt_float("Total price (for whole family)")
        
        # Optional
        source = self._prompt("Source", "Manual", required=False)
        booking_url = self._prompt("Booking URL", "", required=False)
        
        deal = HotelDeal(
            destination=destination.upper(),
            property_name=property_name,
            check_in=check_in,
            check_out=check_out,
            deal_type=DealType.ALL_INCLUSIVE,
            total_price_cash=total_price,
            is_all_inclusive=True,
            includes_meals=True,
            includes_drinks=True,
            includes_activities=True,
            source=source or "Manual",
            booking_url=booking_url,
            found_at=datetime.now()
        )
        
        # Evaluate
        deal = self.calc.evaluate_hotel_deal(deal)
        self.tracker.add_deal(deal)
        
        self._print_deal_result(deal)
        return deal
    
    def quick_hotel_cash(self) -> HotelDeal:
        """Quick entry for cash hotel deals."""
        print("\n=== Quick Hotel Entry (Cash) ===\n")
        
        destination = self._prompt("Destination")
        property_name = self._prompt("Hotel name")
        check_in = self._prompt_date("Check-in date")
        check_out = self._prompt_date("Check-out date")
        
        per_night = self._prompt_float("Price per night")
        resort_fees = self._prompt_float("Resort/destination fees per night", 0)
        
        deal = HotelDeal(
            destination=destination.upper(),
            property_name=property_name,
            check_in=check_in,
            check_out=check_out,
            deal_type=DealType.HOTEL_CASH,
            price_per_night_cash=per_night,
            total_price_cash=per_night * (check_out - check_in).days,
            resort_fees=resort_fees * (check_out - check_in).days,
            is_all_inclusive=False,
            source="Manual",
            found_at=datetime.now()
        )
        
        deal = self.calc.evaluate_hotel_deal(deal)
        self.tracker.add_deal(deal)
        
        self._print_deal_result(deal)
        return deal
    
    # -------------------------------------------------------------------------
    # Package Builder
    # -------------------------------------------------------------------------
    
    def build_package(
        self,
        flight: FlightDeal = None,
        hotel: HotelDeal = None
    ) -> TripPackage:
        """Build a complete trip package from components."""
        print("\n=== Building Trip Package ===\n")
        
        # If no components provided, use most recent deals
        if not flight:
            print("Select a flight deal or enter new one:")
            choice = self._prompt_choice(
                "Enter (n)ew or (s)elect existing",
                ["n", "s"],
                "n"
            )
            if choice == "n":
                flight = self.quick_flight_cash()
            else:
                # Show recent flights
                flights = [d for d in self.tracker.get_all_deals() 
                          if 'flight' in d.get('deal_type', '')]
                if flights:
                    for i, f in enumerate(flights[:5]):
                        print(f"  {i+1}. {f.get('destination')} - ${f.get('price_cash', 0):,.0f}")
                    idx = self._prompt_int("Select number", 1)
                    flight = FlightDeal.from_dict(flights[idx-1])
                else:
                    print("No flights saved. Enter a new one:")
                    flight = self.quick_flight_cash()
        
        if not hotel:
            print("\nSelect a hotel/resort or enter new one:")
            choice = self._prompt_choice(
                "Enter (n)ew or (s)elect existing",
                ["n", "s"],
                "n"
            )
            if choice == "n":
                is_ai = self._prompt_choice(
                    "All-inclusive?",
                    ["y", "n"],
                    "y"
                )
                if is_ai == "y":
                    hotel = self.quick_all_inclusive()
                else:
                    hotel = self.quick_hotel_cash()
            else:
                hotels = [d for d in self.tracker.get_all_deals()
                         if 'hotel' in d.get('deal_type', '') or 'inclusive' in d.get('deal_type', '')]
                if hotels:
                    for i, h in enumerate(hotels[:5]):
                        print(f"  {i+1}. {h.get('property_name')} - ${h.get('total_price_cash', 0):,.0f}")
                    idx = self._prompt_int("Select number", 1)
                    hotel = HotelDeal.from_dict(hotels[idx-1])
                else:
                    print("No hotels saved. Enter a new one:")
                    hotel = self.quick_all_inclusive()
        
        # Build package
        package = TripPackage(
            destination=flight.destination if flight else hotel.destination,
            departure_date=flight.departure_date if flight else hotel.check_in,
            return_date=flight.return_date if flight else hotel.check_out,
            flight=flight,
            hotel=hotel
        )
        
        # Evaluate
        package = self.calc.evaluate_trip_package(package)
        self.tracker.add_deal(package)
        
        self._print_package_result(package)
        return package
    
    # -------------------------------------------------------------------------
    # Output
    # -------------------------------------------------------------------------
    
    def _print_deal_result(self, deal):
        """Print deal evaluation result."""
        status_emoji = {
            DealStatus.EXCELLENT: "🔥",
            DealStatus.GOOD: "✅",
            DealStatus.ACCEPTABLE: "👍",
            DealStatus.POOR: "⚠️"
        }
        
        emoji = status_emoji.get(deal.status, "❓")
        
        print(f"\n{emoji} Deal Status: {deal.status.value.upper()}")
        
        if deal.cpp_value:
            print(f"   CPP Value: {deal.cpp_value:.2f} cents/point")
        if deal.total_value:
            print(f"   Cash Equivalent: ${deal.total_value:,.0f}")
        if deal.savings_vs_cash:
            print(f"   Points Savings: ${deal.savings_vs_cash:,.0f}")
        if hasattr(deal, 'per_person_per_night') and deal.per_person_per_night:
            print(f"   Per Person/Night: ${deal.per_person_per_night:,.0f}")
        
        print(f"\n   ✅ Deal saved to tracker\n")
    
    def _print_package_result(self, package: TripPackage):
        """Print package evaluation result."""
        print("\n" + "=" * 50)
        print(f"📦 TRIP PACKAGE: {package.destination}")
        print("=" * 50)
        print(f"\nDates: {package.departure_date} to {package.return_date}")
        print(f"Total Cash: ${package.total_cash_cost:,.0f}")
        print(f"Points Used: {package.total_points_used:,}")
        print(f"Per Person: ${package.cost_per_person:,.0f}")
        print(f"Per Person/Day: ${package.cost_per_person_per_day:,.0f}")
        print(f"\nStatus: {package.status.value.upper()}")
        print("\nRecommendation:")
        print(package.recommendation)
        print("\n" + "=" * 50 + "\n")


def interactive_menu(calculator: ValueCalculator, tracker: DealTracker):
    """Run interactive data entry menu."""
    entry = DataEntry(calculator, tracker)
    
    while True:
        print("\n" + "=" * 40)
        print("TRAVEL DEAL ENTRY")
        print("=" * 40)
        print("1. Quick Flight (Cash)")
        print("2. Quick Flight (Award)")
        print("3. Quick All-Inclusive Resort")
        print("4. Quick Hotel (Cash)")
        print("5. Build Trip Package")
        print("6. View Saved Deals")
        print("7. Exit")
        print("=" * 40)
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            entry.quick_flight_cash()
        elif choice == "2":
            entry.quick_flight_award()
        elif choice == "3":
            entry.quick_all_inclusive()
        elif choice == "4":
            entry.quick_hotel_cash()
        elif choice == "5":
            entry.build_package()
        elif choice == "6":
            deals = tracker.get_all_deals()
            print(f"\n📋 {len(deals)} deals saved:")
            for d in deals[:10]:
                dest = d.get('destination', 'Unknown')
                status = d.get('status', 'unknown')
                print(f"  - {dest}: {status}")
        elif choice == "7":
            print("\nGoodbye! 👋\n")
            break
        else:
            print("Invalid option. Please choose 1-7.")
