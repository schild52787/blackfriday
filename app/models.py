"""
Data models for travel deal tracking.

Defines structures for:
- Flight deals (cash and award)
- Hotel/resort deals
- Package deals (all-inclusive)
- Historical price tracking
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional
import json


class DealType(Enum):
    """Types of travel deals."""
    FLIGHT_CASH = "flight_cash"
    FLIGHT_AWARD = "flight_award"
    HOTEL_CASH = "hotel_cash"
    HOTEL_POINTS = "hotel_points"
    ALL_INCLUSIVE = "all_inclusive"
    PACKAGE = "package"


class CabinClass(Enum):
    """Flight cabin classes."""
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


class DealStatus(Enum):
    """Deal evaluation status."""
    EXCELLENT = "excellent"  # Alert immediately
    GOOD = "good"           # Worth considering
    ACCEPTABLE = "acceptable"  # Meets baseline
    POOR = "poor"           # Below value threshold
    EXPIRED = "expired"     # No longer available


@dataclass
class FlightDeal:
    """Represents a flight deal (cash or award)."""
    
    # Route info
    origin: str
    destination: str
    departure_date: date
    return_date: date
    
    # Pricing
    deal_type: DealType
    price_cash: Optional[float] = None  # Total for family of 4
    price_points: Optional[int] = None  # Per person
    points_currency: Optional[str] = None  # e.g., "delta_skymiles", "amex_mr"
    taxes_fees: float = 0.0  # Cash portion even for awards
    
    # Flight details
    airline: str = ""
    cabin_class: CabinClass = CabinClass.ECONOMY
    stops: int = 0
    flight_numbers: list = field(default_factory=list)
    
    # Value calculations (populated by calculator)
    cpp_value: Optional[float] = None  # Cents per point
    total_value: Optional[float] = None  # Cash-equivalent value
    savings_vs_cash: Optional[float] = None
    
    # Metadata
    source: str = ""  # Where deal was found
    booking_url: str = ""
    found_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: DealStatus = DealStatus.ACCEPTABLE
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "origin": self.origin,
            "destination": self.destination,
            "departure_date": self.departure_date.isoformat(),
            "return_date": self.return_date.isoformat(),
            "deal_type": self.deal_type.value,
            "price_cash": self.price_cash,
            "price_points": self.price_points,
            "points_currency": self.points_currency,
            "taxes_fees": self.taxes_fees,
            "airline": self.airline,
            "cabin_class": self.cabin_class.value,
            "stops": self.stops,
            "cpp_value": self.cpp_value,
            "total_value": self.total_value,
            "savings_vs_cash": self.savings_vs_cash,
            "source": self.source,
            "booking_url": self.booking_url,
            "found_at": self.found_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FlightDeal":
        """Create from dictionary."""
        return cls(
            origin=data["origin"],
            destination=data["destination"],
            departure_date=date.fromisoformat(data["departure_date"]),
            return_date=date.fromisoformat(data["return_date"]),
            deal_type=DealType(data["deal_type"]),
            price_cash=data.get("price_cash"),
            price_points=data.get("price_points"),
            points_currency=data.get("points_currency"),
            taxes_fees=data.get("taxes_fees", 0),
            airline=data.get("airline", ""),
            cabin_class=CabinClass(data.get("cabin_class", "economy")),
            stops=data.get("stops", 0),
            cpp_value=data.get("cpp_value"),
            total_value=data.get("total_value"),
            savings_vs_cash=data.get("savings_vs_cash"),
            source=data.get("source", ""),
            booking_url=data.get("booking_url", ""),
            found_at=datetime.fromisoformat(data["found_at"]) if data.get("found_at") else datetime.now(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            status=DealStatus(data.get("status", "acceptable")),
            notes=data.get("notes", ""),
        )


@dataclass
class HotelDeal:
    """Represents a hotel or resort deal."""
    
    # Location
    destination: str
    property_name: str
    check_in: date
    check_out: date
    
    # Pricing
    deal_type: DealType
    price_per_night_cash: Optional[float] = None
    price_per_night_points: Optional[int] = None
    points_currency: Optional[str] = None
    total_price_cash: Optional[float] = None
    total_price_points: Optional[int] = None
    resort_fees: float = 0.0
    
    # Property details
    room_type: str = ""
    beds: str = ""
    is_all_inclusive: bool = False
    includes_meals: bool = False
    includes_drinks: bool = False
    includes_activities: bool = False
    
    # Value calculations
    cpp_value: Optional[float] = None
    per_person_per_night: Optional[float] = None  # For all-inclusive comparison
    
    # Metadata
    source: str = ""
    booking_url: str = ""
    found_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: DealStatus = DealStatus.ACCEPTABLE
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "destination": self.destination,
            "property_name": self.property_name,
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
            "deal_type": self.deal_type.value,
            "price_per_night_cash": self.price_per_night_cash,
            "price_per_night_points": self.price_per_night_points,
            "points_currency": self.points_currency,
            "total_price_cash": self.total_price_cash,
            "total_price_points": self.total_price_points,
            "resort_fees": self.resort_fees,
            "room_type": self.room_type,
            "is_all_inclusive": self.is_all_inclusive,
            "includes_meals": self.includes_meals,
            "cpp_value": self.cpp_value,
            "per_person_per_night": self.per_person_per_night,
            "source": self.source,
            "booking_url": self.booking_url,
            "found_at": self.found_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "HotelDeal":
        """Create from dictionary."""
        return cls(
            destination=data["destination"],
            property_name=data["property_name"],
            check_in=date.fromisoformat(data["check_in"]),
            check_out=date.fromisoformat(data["check_out"]),
            deal_type=DealType(data["deal_type"]),
            price_per_night_cash=data.get("price_per_night_cash"),
            price_per_night_points=data.get("price_per_night_points"),
            points_currency=data.get("points_currency"),
            total_price_cash=data.get("total_price_cash"),
            total_price_points=data.get("total_price_points"),
            resort_fees=data.get("resort_fees", 0),
            room_type=data.get("room_type", ""),
            is_all_inclusive=data.get("is_all_inclusive", False),
            includes_meals=data.get("includes_meals", False),
            cpp_value=data.get("cpp_value"),
            per_person_per_night=data.get("per_person_per_night"),
            source=data.get("source", ""),
            booking_url=data.get("booking_url", ""),
            found_at=datetime.fromisoformat(data["found_at"]) if data.get("found_at") else datetime.now(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            status=DealStatus(data.get("status", "acceptable")),
            notes=data.get("notes", ""),
        )


@dataclass
class TripPackage:
    """Represents a complete trip package (flights + accommodations)."""
    
    # Core info
    destination: str
    departure_date: date
    return_date: date
    
    # Components
    flight: Optional[FlightDeal] = None
    hotel: Optional[HotelDeal] = None
    
    # Package pricing (if booked as package)
    package_price: Optional[float] = None
    
    # Totals
    total_cash_cost: float = 0.0
    total_points_used: int = 0
    points_currencies_used: list = field(default_factory=list)
    
    # Value metrics
    total_value: float = 0.0  # Cash-equivalent value of package
    cost_per_person: float = 0.0
    cost_per_person_per_day: float = 0.0
    
    # Comparison metrics
    savings_vs_baseline: float = 0.0
    savings_pct: float = 0.0
    
    # Status
    status: DealStatus = DealStatus.ACCEPTABLE
    recommendation: str = ""
    booking_steps: list = field(default_factory=list)
    
    def calculate_totals(self, family_size: int = 4):
        """Calculate total costs and per-person metrics."""
        self.total_cash_cost = 0.0
        self.total_points_used = 0
        
        if self.flight:
            if self.flight.price_cash:
                self.total_cash_cost += self.flight.price_cash
            if self.flight.price_points:
                self.total_points_used += self.flight.price_points * family_size
            self.total_cash_cost += self.flight.taxes_fees
            
        if self.hotel:
            if self.hotel.total_price_cash:
                self.total_cash_cost += self.hotel.total_price_cash
            if self.hotel.total_price_points:
                self.total_points_used += self.hotel.total_price_points
            self.total_cash_cost += self.hotel.resort_fees
            
        # Per-person metrics
        num_days = (self.return_date - self.departure_date).days
        self.cost_per_person = self.total_cash_cost / family_size
        self.cost_per_person_per_day = self.cost_per_person / num_days if num_days > 0 else 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "destination": self.destination,
            "departure_date": self.departure_date.isoformat(),
            "return_date": self.return_date.isoformat(),
            "flight": self.flight.to_dict() if self.flight else None,
            "hotel": self.hotel.to_dict() if self.hotel else None,
            "package_price": self.package_price,
            "total_cash_cost": self.total_cash_cost,
            "total_points_used": self.total_points_used,
            "total_value": self.total_value,
            "cost_per_person": self.cost_per_person,
            "cost_per_person_per_day": self.cost_per_person_per_day,
            "savings_vs_baseline": self.savings_vs_baseline,
            "savings_pct": self.savings_pct,
            "status": self.status.value,
            "recommendation": self.recommendation,
            "booking_steps": self.booking_steps,
        }


@dataclass
class PriceHistory:
    """Tracks price history for a route/property."""
    
    route_key: str  # e.g., "MSP-CUN-2026-03-27"
    prices: list = field(default_factory=list)  # List of (timestamp, price) tuples
    
    def add_price(self, price: float, timestamp: datetime = None):
        """Add a price observation."""
        if timestamp is None:
            timestamp = datetime.now()
        self.prices.append({"timestamp": timestamp.isoformat(), "price": price})
        
    def get_baseline(self) -> float:
        """Get baseline price (average of first 3 observations or all if fewer)."""
        if not self.prices:
            return 0.0
        num_baseline = min(3, len(self.prices))
        return sum(p["price"] for p in self.prices[:num_baseline]) / num_baseline
    
    def get_current(self) -> float:
        """Get most recent price."""
        return self.prices[-1]["price"] if self.prices else 0.0
    
    def get_lowest(self) -> float:
        """Get lowest observed price."""
        return min(p["price"] for p in self.prices) if self.prices else 0.0
    
    def get_trend(self) -> str:
        """Get price trend direction."""
        if len(self.prices) < 2:
            return "stable"
        recent = self.prices[-3:] if len(self.prices) >= 3 else self.prices
        first = recent[0]["price"]
        last = recent[-1]["price"]
        change_pct = (last - first) / first * 100 if first > 0 else 0
        
        if change_pct < -10:
            return "dropping"
        elif change_pct > 10:
            return "rising"
        return "stable"
    
    def to_dict(self) -> dict:
        return {
            "route_key": self.route_key,
            "prices": self.prices,
            "baseline": self.get_baseline(),
            "current": self.get_current(),
            "lowest": self.get_lowest(),
            "trend": self.get_trend(),
        }
