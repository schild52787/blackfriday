"""
Travel Deal Optimizer

A tool for tracking and evaluating travel deals during Black Friday sales.
Designed for family travel with support for points optimization.
"""

__version__ = "1.0.0"

from .models import FlightDeal, HotelDeal, TripPackage, DealType, DealStatus
from .calculator import ValueCalculator, ValueConfig, quick_cpp_calc
from .tracker import DealTracker
from .alerts import AlertSystem
from .reports import ReportGenerator

__all__ = [
    "FlightDeal",
    "HotelDeal", 
    "TripPackage",
    "DealType",
    "DealStatus",
    "ValueCalculator",
    "ValueConfig",
    "quick_cpp_calc",
    "DealTracker",
    "AlertSystem",
    "ReportGenerator",
]
