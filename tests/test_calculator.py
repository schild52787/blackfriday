"""
Tests for the Value Calculator.

Run: pytest tests/test_calculator.py -v
"""

import pytest
from datetime import date
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.calculator import ValueCalculator, ValueConfig, quick_cpp_calc, should_use_points
from app.models import FlightDeal, HotelDeal, DealType, CabinClass, DealStatus


@pytest.fixture
def config():
    """Create test configuration."""
    return ValueConfig(
        baseline_cpp={"delta_skymiles": 1.2, "amex_mr": 1.5, "hilton": 0.5},
        target_cpp={"delta_skymiles": 1.5, "amex_mr": 2.0, "hilton": 0.6},
        min_cpp={"delta_skymiles": 1.0, "amex_mr": 1.2, "hilton": 0.4},
        family_size=4,
        max_budget=12000,
        target_budget=10000,
    )


@pytest.fixture
def calculator(config):
    """Create calculator with test config."""
    return ValueCalculator(config)


class TestQuickCPP:
    """Test quick CPP calculation function."""
    
    def test_basic_calculation(self):
        """Test basic CPP calculation."""
        # $800 flight, 45000 points, $50 taxes
        # (800 - 50) / 45000 * 100 = 1.67
        result = quick_cpp_calc(800, 45000, 50)
        assert result == 1.67
    
    def test_no_taxes(self):
        """Test CPP without taxes."""
        # $900 / 50000 * 100 = 1.8
        result = quick_cpp_calc(900, 50000)
        assert result == 1.8
    
    def test_zero_points(self):
        """Test with zero points returns 0."""
        result = quick_cpp_calc(800, 0)
        assert result == 0.0
    
    def test_excellent_value(self):
        """Test excellent value calculation."""
        # $1500 flight, 50000 points, $100 taxes
        # (1500 - 100) / 50000 * 100 = 2.8 cpp
        result = quick_cpp_calc(1500, 50000, 100)
        assert result == 2.8


class TestShouldUsePoints:
    """Test points vs cash decision function."""
    
    def test_excellent_value_yes(self):
        """Test recommends points for excellent value."""
        use_points, reason = should_use_points(
            cash_price=1500,
            points_price=50000,
            taxes_fees=100,
            points_currency="delta_skymiles",
            min_cpp={"delta_skymiles": 1.0}
        )
        assert use_points is True
        assert "Excellent" in reason or "YES" in reason
    
    def test_poor_value_no(self):
        """Test recommends cash for poor value."""
        use_points, reason = should_use_points(
            cash_price=400,
            points_price=50000,
            taxes_fees=50,
            points_currency="delta_skymiles",
            min_cpp={"delta_skymiles": 1.0}
        )
        # (400-50)/50000*100 = 0.7 cpp - below threshold
        assert use_points is False
        assert "NO" in reason


class TestValueCalculator:
    """Test the ValueCalculator class."""
    
    def test_cpp_calculation(self, calculator):
        """Test CPP calculation method."""
        cpp = calculator.calculate_cpp(
            cash_price=800,
            points_price=45000,
            taxes_fees=50
        )
        assert cpp == 1.67
    
    def test_evaluate_flight_cash_deal(self, calculator):
        """Test evaluating a cash flight deal."""
        deal = FlightDeal(
            origin="MSP",
            destination="CUN",
            departure_date=date(2026, 3, 27),
            return_date=date(2026, 4, 3),
            deal_type=DealType.FLIGHT_CASH,
            price_cash=1600,  # $400/person - good for Cancun
            airline="Delta",
            cabin_class=CabinClass.ECONOMY,
            stops=0
        )
        
        result = calculator.evaluate_flight_deal(deal)
        
        assert result.total_value == 1600
        assert result.status in [DealStatus.EXCELLENT, DealStatus.GOOD, DealStatus.ACCEPTABLE]
    
    def test_evaluate_flight_award_deal(self, calculator):
        """Test evaluating an award flight deal."""
        deal = FlightDeal(
            origin="MSP",
            destination="CUN",
            departure_date=date(2026, 3, 27),
            return_date=date(2026, 4, 3),
            deal_type=DealType.FLIGHT_AWARD,
            price_points=25000,  # Per person RT
            points_currency="delta_skymiles",
            taxes_fees=5.60,
            airline="Delta",
            cabin_class=CabinClass.ECONOMY
        )
        
        result = calculator.evaluate_flight_deal(deal, baseline_cash_price=1600)
        
        assert result.cpp_value is not None
        assert result.cpp_value > 0
        assert result.status is not None
    
    def test_evaluate_hotel_all_inclusive(self, calculator):
        """Test evaluating an all-inclusive hotel deal."""
        deal = HotelDeal(
            destination="CUN",
            property_name="Hyatt Ziva Cancun",
            check_in=date(2026, 3, 27),
            check_out=date(2026, 4, 3),
            deal_type=DealType.ALL_INCLUSIVE,
            total_price_cash=5600,  # $800/night for 7 nights
            is_all_inclusive=True,
            includes_meals=True,
            includes_drinks=True
        )
        
        result = calculator.evaluate_hotel_deal(deal)
        
        # 5600 / 7 nights / 4 people = 200/person/night - excellent!
        assert result.per_person_per_night is not None
        assert result.per_person_per_night == 200
        assert result.status == DealStatus.EXCELLENT


class TestDealStatus:
    """Test deal status evaluation."""
    
    def test_excellent_cpp_award(self, calculator):
        """Test excellent status for high CPP award."""
        deal = FlightDeal(
            origin="MSP",
            destination="FCO",
            departure_date=date(2026, 3, 27),
            return_date=date(2026, 4, 3),
            deal_type=DealType.FLIGHT_AWARD,
            price_points=50000,
            points_currency="delta_skymiles",
            taxes_fees=100,
            airline="Delta"
        )
        
        # With $4000 cash price, CPP = (4000 - 400) / 200000 * 100 = 1.8
        result = calculator.evaluate_flight_deal(deal, baseline_cash_price=4000)
        
        # 1.8 cpp is above target (1.5) so should be good or excellent
        assert result.status in [DealStatus.EXCELLENT, DealStatus.GOOD]
    
    def test_poor_cpp_award(self, calculator):
        """Test poor status for low CPP award."""
        deal = FlightDeal(
            origin="MSP",
            destination="CUN",
            departure_date=date(2026, 3, 27),
            return_date=date(2026, 4, 3),
            deal_type=DealType.FLIGHT_AWARD,
            price_points=80000,  # High points
            points_currency="delta_skymiles",
            taxes_fees=100,
            airline="Delta"
        )
        
        # With $1200 cash price, CPP = (1200 - 400) / 320000 * 100 = 0.25
        result = calculator.evaluate_flight_deal(deal, baseline_cash_price=1200)
        
        assert result.status == DealStatus.POOR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
