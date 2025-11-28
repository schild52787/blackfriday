"""
Deal Tracker

Manages:
- Deal storage and retrieval
- Historical price tracking
- Baseline price management
- Deal deduplication
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import asdict

from .models import (
    FlightDeal, HotelDeal, TripPackage, 
    PriceHistory, DealStatus, DealType
)

logger = logging.getLogger(__name__)


class DealTracker:
    """
    Tracks deals and maintains historical pricing data.
    
    Storage structure:
    - data/deals.json: All tracked deals
    - data/price_history.json: Historical prices by route
    - data/baseline_prices.json: Baseline prices for comparison
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.deals_file = self.data_dir / "deals.json"
        self.history_file = self.data_dir / "price_history.json"
        self.baseline_file = self.data_dir / "baseline_prices.json"
        
        # Load existing data
        self.deals: Dict[str, dict] = self._load_json(self.deals_file, {})
        self.price_history: Dict[str, dict] = self._load_json(self.history_file, {})
        self.baselines: Dict[str, float] = self._load_json(self.baseline_file, {})
    
    def _load_json(self, path: Path, default: any) -> any:
        """Load JSON file or return default."""
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse {path}, using default")
                return default
        return default
    
    def _save_json(self, path: Path, data: any):
        """Save data to JSON file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _generate_deal_key(self, deal) -> str:
        """Generate unique key for a deal."""
        if isinstance(deal, FlightDeal):
            return f"flight_{deal.origin}_{deal.destination}_{deal.departure_date}_{deal.airline}_{deal.deal_type.value}"
        elif isinstance(deal, HotelDeal):
            return f"hotel_{deal.property_name}_{deal.check_in}_{deal.deal_type.value}"
        elif isinstance(deal, TripPackage):
            return f"package_{deal.destination}_{deal.departure_date}"
        return f"unknown_{datetime.now().timestamp()}"
    
    def _generate_route_key(
        self, 
        origin: str, 
        destination: str, 
        departure_date: date
    ) -> str:
        """Generate key for route-based price tracking."""
        return f"{origin}-{destination}-{departure_date.strftime('%Y-%m')}"
    
    # -------------------------------------------------------------------------
    # Deal Management
    # -------------------------------------------------------------------------
    
    def add_deal(self, deal) -> str:
        """
        Add or update a deal.
        
        Returns:
            Deal key
        """
        key = self._generate_deal_key(deal)
        
        # Convert to dict for storage
        if hasattr(deal, 'to_dict'):
            deal_data = deal.to_dict()
        else:
            deal_data = asdict(deal) if hasattr(deal, '__dataclass_fields__') else vars(deal)
        
        deal_data['_key'] = key
        deal_data['_updated_at'] = datetime.now().isoformat()
        
        # Check if this is a price update
        if key in self.deals:
            old_deal = self.deals[key]
            if deal_data.get('price_cash') != old_deal.get('price_cash'):
                logger.info(f"Price change for {key}: {old_deal.get('price_cash')} -> {deal_data.get('price_cash')}")
        
        self.deals[key] = deal_data
        self._save_json(self.deals_file, self.deals)
        
        # Update price history
        self._update_price_history(deal)
        
        return key
    
    def get_deal(self, key: str) -> Optional[dict]:
        """Get a deal by key."""
        return self.deals.get(key)
    
    def get_all_deals(self, status_filter: Optional[DealStatus] = None) -> List[dict]:
        """Get all deals, optionally filtered by status."""
        deals = list(self.deals.values())
        
        if status_filter:
            deals = [d for d in deals if d.get('status') == status_filter.value]
        
        return deals
    
    def get_excellent_deals(self) -> List[dict]:
        """Get all deals marked as excellent."""
        return self.get_all_deals(DealStatus.EXCELLENT)
    
    def remove_deal(self, key: str):
        """Remove a deal."""
        if key in self.deals:
            del self.deals[key]
            self._save_json(self.deals_file, self.deals)
    
    def expire_old_deals(self, days: int = 7):
        """Mark deals older than N days as expired."""
        cutoff = datetime.now()
        expired_keys = []
        
        for key, deal in self.deals.items():
            found_at = deal.get('found_at')
            if found_at:
                deal_date = datetime.fromisoformat(found_at)
                age = (cutoff - deal_date).days
                if age > days:
                    deal['status'] = DealStatus.EXPIRED.value
                    expired_keys.append(key)
        
        if expired_keys:
            logger.info(f"Expired {len(expired_keys)} old deals")
            self._save_json(self.deals_file, self.deals)
    
    # -------------------------------------------------------------------------
    # Price History
    # -------------------------------------------------------------------------
    
    def _update_price_history(self, deal):
        """Update price history for a deal's route."""
        if isinstance(deal, FlightDeal):
            key = self._generate_route_key(
                deal.origin, 
                deal.destination, 
                deal.departure_date
            )
            price = deal.price_cash if deal.price_cash else 0
        elif isinstance(deal, HotelDeal):
            key = f"hotel-{deal.property_name}-{deal.check_in.strftime('%Y-%m')}"
            price = deal.price_per_night_cash or 0
        else:
            return
        
        if price <= 0:
            return
        
        # Initialize history if needed
        if key not in self.price_history:
            self.price_history[key] = {
                "route_key": key,
                "prices": []
            }
        
        # Add new price observation
        self.price_history[key]["prices"].append({
            "timestamp": datetime.now().isoformat(),
            "price": price
        })
        
        # Keep only last 100 observations
        self.price_history[key]["prices"] = self.price_history[key]["prices"][-100:]
        
        self._save_json(self.history_file, self.price_history)
    
    def get_price_history(self, route_key: str) -> Optional[PriceHistory]:
        """Get price history for a route."""
        data = self.price_history.get(route_key)
        if data:
            history = PriceHistory(route_key=data["route_key"])
            history.prices = data["prices"]
            return history
        return None
    
    def get_baseline_price(
        self, 
        origin: str, 
        destination: str, 
        departure_month: str
    ) -> Optional[float]:
        """Get baseline price for a route."""
        key = f"{origin}-{destination}-{departure_month}"
        return self.baselines.get(key)
    
    def set_baseline_price(
        self,
        origin: str,
        destination: str,
        departure_month: str,
        price: float
    ):
        """Set baseline price for a route."""
        key = f"{origin}-{destination}-{departure_month}"
        self.baselines[key] = price
        self._save_json(self.baseline_file, self.baselines)
    
    def get_all_baselines(self) -> Dict[str, float]:
        """Get all baseline prices."""
        return self.baselines.copy()
    
    # -------------------------------------------------------------------------
    # Analysis
    # -------------------------------------------------------------------------
    
    def calculate_deal_discount(self, deal: dict) -> Optional[float]:
        """Calculate discount percentage vs baseline."""
        if isinstance(deal.get('departure_date'), str):
            dep_date = date.fromisoformat(deal['departure_date'])
        else:
            dep_date = deal.get('departure_date')
        
        if not dep_date:
            return None
        
        baseline = self.get_baseline_price(
            deal.get('origin', ''),
            deal.get('destination', ''),
            dep_date.strftime('%Y-%m')
        )
        
        if not baseline:
            return None
        
        current_price = deal.get('price_cash', 0) or deal.get('total_price_cash', 0)
        if current_price <= 0:
            return None
        
        return ((baseline - current_price) / baseline) * 100
    
    def get_deals_summary(self) -> Dict:
        """Get summary statistics of tracked deals."""
        deals = list(self.deals.values())
        
        if not deals:
            return {
                "total_deals": 0,
                "by_status": {},
                "by_destination": {},
                "by_type": {}
            }
        
        # Count by status
        by_status = {}
        for deal in deals:
            status = deal.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
        
        # Count by destination
        by_destination = {}
        for deal in deals:
            dest = deal.get('destination', 'unknown')
            by_destination[dest] = by_destination.get(dest, 0) + 1
        
        # Count by type
        by_type = {}
        for deal in deals:
            deal_type = deal.get('deal_type', 'unknown')
            by_type[deal_type] = by_type.get(deal_type, 0) + 1
        
        return {
            "total_deals": len(deals),
            "by_status": by_status,
            "by_destination": by_destination,
            "by_type": by_type,
            "excellent_count": by_status.get('excellent', 0),
            "good_count": by_status.get('good', 0)
        }
    
    def export_deals_csv(self, output_path: str = None) -> str:
        """Export deals to CSV for spreadsheet analysis."""
        import csv
        from io import StringIO
        
        output = StringIO()
        fieldnames = [
            'key', 'type', 'destination', 'departure_date', 'return_date',
            'price_cash', 'price_points', 'cpp_value', 'status', 
            'airline', 'property_name', 'source', 'found_at'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for key, deal in self.deals.items():
            row = {
                'key': key,
                'type': deal.get('deal_type', ''),
                'destination': deal.get('destination', ''),
                'departure_date': deal.get('departure_date', ''),
                'return_date': deal.get('return_date', deal.get('check_out', '')),
                'price_cash': deal.get('price_cash', deal.get('total_price_cash', '')),
                'price_points': deal.get('price_points', deal.get('total_price_points', '')),
                'cpp_value': deal.get('cpp_value', ''),
                'status': deal.get('status', ''),
                'airline': deal.get('airline', ''),
                'property_name': deal.get('property_name', ''),
                'source': deal.get('source', ''),
                'found_at': deal.get('found_at', '')
            }
            writer.writerow(row)
        
        csv_content = output.getvalue()
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(csv_content)
        
        return csv_content


# Convenience functions for CLI use
def init_tracker(data_dir: str = "data") -> DealTracker:
    """Initialize a deal tracker."""
    return DealTracker(data_dir)
