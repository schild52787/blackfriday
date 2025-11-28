"""
Value Calculation Engine

The brain of the deal optimizer. Calculates:
- Cents per point (CPP) values
- Cash vs. points comparison
- Total trip values
- Deal quality scores
- Savings calculations
"""

from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from datetime import date
import yaml
import logging

from .models import (
    FlightDeal, HotelDeal, TripPackage, 
    DealType, DealStatus, CabinClass
)

logger = logging.getLogger(__name__)


@dataclass
class ValueConfig:
    """Configuration for value calculations."""
    
    # Point valuations (cents per point)
    baseline_cpp: Dict[str, float]
    target_cpp: Dict[str, float]
    min_cpp: Dict[str, float]
    
    # Diamond Medallion benefits
    upgrade_probability: float = 0.40
    upgrade_value_multiplier: float = 1.5
    companion_cert_value: float = 800
    
    # Family size
    family_size: int = 4
    adults: int = 2
    children: int = 2
    
    # Budget constraints
    max_budget: float = 12000
    target_budget: float = 10000
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "ValueConfig":
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        value_calc = config.get("value_calc", {})
        traveler = config.get("traveler", {})
        budget = config.get("budget", {})
        diamond = value_calc.get("diamond_benefits", {})
        
        return cls(
            baseline_cpp=value_calc.get("baseline_cpp", {}),
            target_cpp=value_calc.get("target_cpp", {}),
            min_cpp=value_calc.get("min_cpp", {}),
            upgrade_probability=diamond.get("upgrade_probability", 0.4),
            upgrade_value_multiplier=diamond.get("upgrade_value_multiplier", 1.5),
            companion_cert_value=diamond.get("companion_certificate_value", 800),
            family_size=traveler.get("family_size", 4),
            adults=traveler.get("adults", 2),
            children=len(traveler.get("children", [])),
            max_budget=budget.get("max_total_cash", 12000),
            target_budget=budget.get("target_total", 10000),
        )


class ValueCalculator:
    """
    Calculates the true value of travel deals.
    
    Core principle: A deal is only good if:
    1. Points redemption exceeds minimum CPP threshold
    2. Total cost stays within budget
    3. Value-per-day meets destination benchmarks
    """
    
    def __init__(self, config: ValueConfig):
        self.config = config
        
    def calculate_cpp(
        self, 
        cash_price: float, 
        points_price: int, 
        taxes_fees: float = 0
    ) -> float:
        """
        Calculate cents per point value.
        
        Formula: (Cash Price - Taxes/Fees) / Points × 100
        
        Args:
            cash_price: Full cash price for same itinerary
            points_price: Points required
            taxes_fees: Cash portion (taxes/fees) on award booking
            
        Returns:
            Cents per point value
        """
        if points_price <= 0:
            return 0.0
        
        value_obtained = cash_price - taxes_fees
        cpp = (value_obtained / points_price) * 100
        
        return round(cpp, 2)
    
    def evaluate_flight_deal(
        self, 
        deal: FlightDeal,
        baseline_cash_price: Optional[float] = None
    ) -> FlightDeal:
        """
        Evaluate a flight deal and populate value metrics.
        
        Args:
            deal: Flight deal to evaluate
            baseline_cash_price: Optional baseline for comparison
            
        Returns:
            FlightDeal with populated value metrics and status
        """
        family_size = self.config.family_size
        
        # Calculate total family cost
        if deal.deal_type == DealType.FLIGHT_CASH:
            deal.total_value = deal.price_cash
            deal.cpp_value = None
            
        elif deal.deal_type == DealType.FLIGHT_AWARD:
            # Get equivalent cash price for comparison
            if baseline_cash_price:
                cash_equivalent = baseline_cash_price
            else:
                # Estimate based on route/cabin
                cash_equivalent = self._estimate_flight_cash_price(deal)
            
            # Total points cost for family
            total_points = deal.price_points * family_size
            total_taxes = deal.taxes_fees * family_size
            
            # CPP calculation
            deal.cpp_value = self.calculate_cpp(
                cash_equivalent,
                total_points,
                total_taxes
            )
            
            # Total "value" = cash equivalent
            deal.total_value = cash_equivalent
            
            # Savings vs paying cash
            deal.savings_vs_cash = cash_equivalent - total_taxes
            
        # Apply Diamond Medallion value adjustment for Delta
        if deal.airline.lower() == "delta" and deal.cabin_class == CabinClass.ECONOMY:
            # Factor in upgrade probability
            upgrade_bonus = (
                self.config.upgrade_probability * 
                deal.total_value * 
                (self.config.upgrade_value_multiplier - 1)
            )
            deal.notes += f" [Diamond upgrade potential: +${upgrade_bonus:.0f} expected value]"
        
        # Determine deal status
        deal.status = self._evaluate_flight_status(deal)
        
        return deal
    
    def _estimate_flight_cash_price(self, deal: FlightDeal) -> float:
        """Estimate cash price based on route characteristics."""
        # Base estimates by region (per person, roundtrip)
        region_bases = {
            "mexico_caribbean": {"CUN": 400, "PVR": 450, "SJD": 500, "MBJ": 500, "PUJ": 550, "AUA": 600},
            "europe": {"FCO": 900, "BCN": 850, "MAD": 850, "ATH": 950, "LIS": 900, "MXP": 900, "NAP": 950}
        }
        
        # Cabin class multipliers
        cabin_multipliers = {
            CabinClass.ECONOMY: 1.0,
            CabinClass.PREMIUM_ECONOMY: 1.8,
            CabinClass.BUSINESS: 4.0,
            CabinClass.FIRST: 8.0
        }
        
        # Find base price
        base_price = 600  # Default
        for region, airports in region_bases.items():
            if deal.destination in airports:
                base_price = airports[deal.destination]
                break
        
        # Apply multipliers
        price = base_price * cabin_multipliers.get(deal.cabin_class, 1.0)
        
        # Adjust for stops (nonstop premium ~20%)
        if deal.stops == 0:
            price *= 1.2
        
        # Family total
        return price * self.config.family_size
    
    def _evaluate_flight_status(self, deal: FlightDeal) -> DealStatus:
        """Determine deal quality status."""
        if deal.deal_type == DealType.FLIGHT_AWARD:
            currency = deal.points_currency or "delta_skymiles"
            
            target_cpp = self.config.target_cpp.get(currency, 1.5)
            min_cpp = self.config.min_cpp.get(currency, 1.0)
            excellent_cpp = target_cpp * 1.3  # 30% above target
            
            if deal.cpp_value >= excellent_cpp:
                return DealStatus.EXCELLENT
            elif deal.cpp_value >= target_cpp:
                return DealStatus.GOOD
            elif deal.cpp_value >= min_cpp:
                return DealStatus.ACCEPTABLE
            else:
                return DealStatus.POOR
        else:
            # Cash deal - compare to estimates
            estimated = self._estimate_flight_cash_price(deal)
            discount_pct = (estimated - deal.price_cash) / estimated * 100
            
            if discount_pct >= 30:
                return DealStatus.EXCELLENT
            elif discount_pct >= 20:
                return DealStatus.GOOD
            elif discount_pct >= 0:
                return DealStatus.ACCEPTABLE
            else:
                return DealStatus.POOR
    
    def evaluate_hotel_deal(
        self,
        deal: HotelDeal,
        baseline_cash_price: Optional[float] = None
    ) -> HotelDeal:
        """Evaluate a hotel deal and populate value metrics."""
        
        # Calculate nights
        nights = (deal.check_out - deal.check_in).days
        
        if deal.deal_type == DealType.HOTEL_CASH or deal.deal_type == DealType.ALL_INCLUSIVE:
            # Calculate per-person-per-night for comparison
            if deal.is_all_inclusive:
                total = deal.total_price_cash or (deal.price_per_night_cash * nights)
                deal.per_person_per_night = total / (nights * self.config.family_size)
                
                # Status based on all-inclusive thresholds
                if deal.per_person_per_night <= 250:
                    deal.status = DealStatus.EXCELLENT
                elif deal.per_person_per_night <= 350:
                    deal.status = DealStatus.GOOD
                elif deal.per_person_per_night <= 450:
                    deal.status = DealStatus.ACCEPTABLE
                else:
                    deal.status = DealStatus.POOR
                    
        elif deal.deal_type == DealType.HOTEL_POINTS:
            # CPP calculation for points hotels
            if baseline_cash_price and deal.total_price_points:
                deal.cpp_value = self.calculate_cpp(
                    baseline_cash_price,
                    deal.total_price_points,
                    deal.resort_fees
                )
                
                currency = deal.points_currency or "hilton"
                target_cpp = self.config.target_cpp.get(currency, 0.5)
                min_cpp = self.config.min_cpp.get(currency, 0.4)
                
                if deal.cpp_value >= target_cpp * 1.3:
                    deal.status = DealStatus.EXCELLENT
                elif deal.cpp_value >= target_cpp:
                    deal.status = DealStatus.GOOD
                elif deal.cpp_value >= min_cpp:
                    deal.status = DealStatus.ACCEPTABLE
                else:
                    deal.status = DealStatus.POOR
        
        return deal
    
    def evaluate_trip_package(
        self,
        package: TripPackage,
        baseline_total: Optional[float] = None
    ) -> TripPackage:
        """
        Evaluate a complete trip package.
        
        This is the key output - a full comparison of trip options.
        """
        # Calculate totals
        package.calculate_totals(self.config.family_size)
        
        # Calculate per-person-per-day
        nights = (package.return_date - package.departure_date).days
        
        # Determine overall status (worst of components)
        statuses = []
        if package.flight:
            statuses.append(package.flight.status)
        if package.hotel:
            statuses.append(package.hotel.status)
            
        if DealStatus.POOR in statuses:
            package.status = DealStatus.POOR
        elif DealStatus.ACCEPTABLE in statuses:
            package.status = DealStatus.ACCEPTABLE
        elif DealStatus.GOOD in statuses:
            package.status = DealStatus.GOOD
        elif DealStatus.EXCELLENT in statuses:
            package.status = DealStatus.EXCELLENT
        
        # Compare to baseline
        if baseline_total:
            package.savings_vs_baseline = baseline_total - package.total_cash_cost
            package.savings_pct = (package.savings_vs_baseline / baseline_total) * 100
        
        # Generate recommendation
        package.recommendation = self._generate_recommendation(package)
        
        # Generate booking steps
        package.booking_steps = self._generate_booking_steps(package)
        
        return package
    
    def _generate_recommendation(self, package: TripPackage) -> str:
        """Generate human-readable recommendation."""
        lines = []
        
        if package.status == DealStatus.EXCELLENT:
            lines.append("🔥 EXCELLENT DEAL - Book immediately if dates work!")
        elif package.status == DealStatus.GOOD:
            lines.append("✅ Good value - Worth booking")
        elif package.status == DealStatus.ACCEPTABLE:
            lines.append("👍 Meets baseline expectations")
        else:
            lines.append("⚠️ Below value threshold - Consider alternatives")
        
        # Add context
        lines.append(f"Total out-of-pocket: ${package.total_cash_cost:,.0f}")
        if package.total_points_used > 0:
            lines.append(f"Points used: {package.total_points_used:,}")
        
        if package.savings_pct > 0:
            lines.append(f"Savings: {package.savings_pct:.0f}% below baseline")
        
        # Budget check
        if package.total_cash_cost > self.config.max_budget:
            lines.append("⛔ OVER BUDGET CEILING")
        elif package.total_cash_cost > self.config.target_budget:
            lines.append("⚠️ Above target budget (but within ceiling)")
        else:
            lines.append("✅ Within target budget")
        
        return "\n".join(lines)
    
    def _generate_booking_steps(self, package: TripPackage) -> list:
        """Generate step-by-step booking instructions."""
        steps = []
        step_num = 1
        
        if package.flight:
            if package.flight.deal_type == DealType.FLIGHT_AWARD:
                steps.append({
                    "step": step_num,
                    "action": f"Transfer {package.flight.price_points * self.config.family_size:,} points to {package.flight.points_currency}",
                    "notes": "Allow 24-48 hours for transfer to complete",
                    "url": "https://global.americanexpress.com/rewards/summary"
                })
                step_num += 1
                
            steps.append({
                "step": step_num,
                "action": f"Book flight: {package.flight.origin} → {package.flight.destination}",
                "dates": f"{package.departure_date} - {package.return_date}",
                "url": package.flight.booking_url or "https://www.delta.com"
            })
            step_num += 1
            
        if package.hotel:
            steps.append({
                "step": step_num,
                "action": f"Book hotel: {package.hotel.property_name}",
                "dates": f"{package.hotel.check_in} - {package.hotel.check_out}",
                "url": package.hotel.booking_url or ""
            })
        
        return steps
    
    def compare_options(
        self,
        packages: list[TripPackage]
    ) -> Dict:
        """
        Compare multiple trip packages and rank them.
        
        Returns a decision matrix with pros/cons for each option.
        """
        if not packages:
            return {"error": "No packages to compare"}
        
        # Evaluate all packages
        evaluated = [self.evaluate_trip_package(p) for p in packages]
        
        # Sort by value (status, then savings)
        status_order = {
            DealStatus.EXCELLENT: 0,
            DealStatus.GOOD: 1,
            DealStatus.ACCEPTABLE: 2,
            DealStatus.POOR: 3,
            DealStatus.EXPIRED: 4
        }
        
        evaluated.sort(key=lambda p: (
            status_order.get(p.status, 5),
            -p.savings_pct if p.savings_pct else 0
        ))
        
        # Build comparison matrix
        matrix = {
            "ranked_options": [],
            "best_value": None,
            "lowest_cost": None,
            "best_experience": None,
        }
        
        for i, pkg in enumerate(evaluated):
            option = {
                "rank": i + 1,
                "destination": pkg.destination,
                "dates": f"{pkg.departure_date} - {pkg.return_date}",
                "total_cost": pkg.total_cash_cost,
                "points_used": pkg.total_points_used,
                "status": pkg.status.value,
                "savings_pct": pkg.savings_pct,
                "pros": [],
                "cons": [],
                "recommendation": pkg.recommendation,
                "booking_steps": pkg.booking_steps
            }
            
            # Generate pros/cons
            if pkg.status in [DealStatus.EXCELLENT, DealStatus.GOOD]:
                option["pros"].append("Strong value")
            if pkg.total_cash_cost <= self.config.target_budget:
                option["pros"].append("Within budget")
            if pkg.flight and pkg.flight.stops == 0:
                option["pros"].append("Nonstop flights")
            if pkg.hotel and pkg.hotel.is_all_inclusive:
                option["pros"].append("All-inclusive (predictable costs)")
            
            if pkg.total_cash_cost > self.config.max_budget:
                option["cons"].append("Over budget ceiling")
            if pkg.status == DealStatus.POOR:
                option["cons"].append("Below value threshold")
            if pkg.flight and pkg.flight.stops > 1:
                option["cons"].append("Multiple connections")
            
            matrix["ranked_options"].append(option)
        
        # Identify superlatives
        if evaluated:
            matrix["best_value"] = evaluated[0].destination
            matrix["lowest_cost"] = min(evaluated, key=lambda p: p.total_cash_cost).destination
        
        return matrix


def quick_cpp_calc(cash_price: float, points: int, taxes: float = 0) -> float:
    """
    Quick CPP calculation for command-line use.
    
    Example:
        >>> quick_cpp_calc(800, 45000, 50)
        1.67
    """
    if points <= 0:
        return 0.0
    return round(((cash_price - taxes) / points) * 100, 2)


def should_use_points(
    cash_price: float,
    points_price: int,
    taxes_fees: float,
    points_currency: str,
    min_cpp: Dict[str, float]
) -> Tuple[bool, str]:
    """
    Quick decision: should I use points or pay cash?
    
    Returns:
        (bool, str): Decision and explanation
    """
    cpp = quick_cpp_calc(cash_price, points_price, taxes_fees)
    threshold = min_cpp.get(points_currency, 1.0)
    
    if cpp >= threshold * 1.5:
        return True, f"YES - Excellent value at {cpp:.2f}cpp (vs {threshold:.2f}cpp min)"
    elif cpp >= threshold:
        return True, f"YES - Good value at {cpp:.2f}cpp (meets {threshold:.2f}cpp threshold)"
    else:
        return False, f"NO - Only {cpp:.2f}cpp (below {threshold:.2f}cpp minimum). Pay cash."
