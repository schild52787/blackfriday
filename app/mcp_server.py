#!/usr/bin/env python3
"""
Travel Deal Optimizer - MCP Server

Exposes deal tracking tools to Claude Code and other MCP clients.

Usage:
    python -m app.mcp_server

Add to Claude Code config (~/.claude/claude_desktop_config.json):
{
  "mcpServers": {
    "travel-deals": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/path/to/travel-deal-optimizer"
    }
  }
}
"""

import json
import sys
from datetime import date, datetime
from typing import Any
import logging

# MCP protocol implementation
# Using stdio for simplicity - works with Claude Code

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='data/mcp_server.log'
)
logger = logging.getLogger(__name__)

# Import our modules
from .calculator import ValueCalculator, ValueConfig, quick_cpp_calc
from .tracker import DealTracker
from .models import FlightDeal, HotelDeal, DealType, CabinClass, DealStatus
from .reports import ReportGenerator


class TravelDealsMCP:
    """MCP Server for Travel Deal Optimizer."""
    
    def __init__(self):
        self.config = self._load_config()
        self.calculator = ValueCalculator(self.config)
        self.tracker = DealTracker("data")
        self.reporter = ReportGenerator("reports")
    
    def _load_config(self) -> ValueConfig:
        """Load configuration."""
        try:
            return ValueConfig.from_yaml("config/settings.yaml")
        except Exception:
            return ValueConfig(
                baseline_cpp={"delta_skymiles": 1.2, "amex_mr": 1.5},
                target_cpp={"delta_skymiles": 1.5, "amex_mr": 2.0},
                min_cpp={"delta_skymiles": 1.0, "amex_mr": 1.2},
            )
    
    def get_tools(self) -> list:
        """Return list of available tools."""
        return [
            {
                "name": "calculate_cpp",
                "description": "Calculate cents-per-point value for an award redemption. Returns CPP value and recommendation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cash_price": {
                            "type": "number",
                            "description": "Cash price for the same itinerary (total for family)"
                        },
                        "points": {
                            "type": "integer",
                            "description": "Points required (total, not per person)"
                        },
                        "taxes_fees": {
                            "type": "number",
                            "description": "Cash taxes/fees on award booking",
                            "default": 0
                        },
                        "currency": {
                            "type": "string",
                            "description": "Points currency (delta_skymiles, amex_mr, etc)",
                            "default": "delta_skymiles"
                        }
                    },
                    "required": ["cash_price", "points"]
                }
            },
            {
                "name": "add_flight_deal",
                "description": "Add a cash flight deal to tracking. Returns deal evaluation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "Origin airport code (e.g., MSP)"},
                        "destination": {"type": "string", "description": "Destination airport code (e.g., CUN)"},
                        "departure_date": {"type": "string", "description": "Departure date (YYYY-MM-DD)"},
                        "return_date": {"type": "string", "description": "Return date (YYYY-MM-DD)"},
                        "price": {"type": "number", "description": "Total price for family of 4"},
                        "airline": {"type": "string", "description": "Airline name", "default": "Delta"},
                        "stops": {"type": "integer", "description": "Number of stops", "default": 0},
                        "source": {"type": "string", "description": "Where deal was found", "default": "Manual"}
                    },
                    "required": ["origin", "destination", "departure_date", "return_date", "price"]
                }
            },
            {
                "name": "add_award_flight",
                "description": "Add an award flight deal to tracking. Returns deal evaluation with CPP.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "Origin airport code"},
                        "destination": {"type": "string", "description": "Destination airport code"},
                        "departure_date": {"type": "string", "description": "Departure date (YYYY-MM-DD)"},
                        "return_date": {"type": "string", "description": "Return date (YYYY-MM-DD)"},
                        "points_per_person": {"type": "integer", "description": "Points per person (roundtrip)"},
                        "taxes_per_person": {"type": "number", "description": "Taxes/fees per person", "default": 5.60},
                        "currency": {"type": "string", "description": "Points currency", "default": "delta_skymiles"},
                        "cash_comparison": {"type": "number", "description": "Cash price for same flight (for CPP calc)"},
                        "airline": {"type": "string", "default": "Delta"},
                        "cabin": {"type": "string", "default": "economy"}
                    },
                    "required": ["origin", "destination", "departure_date", "return_date", "points_per_person"]
                }
            },
            {
                "name": "add_resort_deal",
                "description": "Add an all-inclusive resort deal to tracking.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "destination": {"type": "string", "description": "Destination airport code"},
                        "property_name": {"type": "string", "description": "Resort name"},
                        "check_in": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                        "check_out": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                        "total_price": {"type": "number", "description": "Total price for family"},
                        "source": {"type": "string", "default": "Manual"}
                    },
                    "required": ["destination", "property_name", "check_in", "check_out", "total_price"]
                }
            },
            {
                "name": "list_deals",
                "description": "List all tracked deals with optional status filter.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter by status (excellent, good, acceptable, poor)",
                            "enum": ["excellent", "good", "acceptable", "poor", "all"]
                        },
                        "limit": {"type": "integer", "default": 10}
                    }
                }
            },
            {
                "name": "compare_deals",
                "description": "Compare all tracked deals and return ranked recommendations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_summary",
                "description": "Get summary statistics of all tracked deals.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "generate_report",
                "description": "Generate comparison report and booking guide. Returns file paths.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_baseline_price",
                "description": "Get baseline price for a route.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                        "month": {"type": "string", "description": "YYYY-MM format"}
                    },
                    "required": ["origin", "destination", "month"]
                }
            }
        ]
    
    def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool and return result."""
        try:
            if name == "calculate_cpp":
                return self._calculate_cpp(arguments)
            elif name == "add_flight_deal":
                return self._add_flight_deal(arguments)
            elif name == "add_award_flight":
                return self._add_award_flight(arguments)
            elif name == "add_resort_deal":
                return self._add_resort_deal(arguments)
            elif name == "list_deals":
                return self._list_deals(arguments)
            elif name == "compare_deals":
                return self._compare_deals(arguments)
            elif name == "get_summary":
                return self._get_summary(arguments)
            elif name == "generate_report":
                return self._generate_report(arguments)
            elif name == "get_baseline_price":
                return self._get_baseline_price(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            logger.error(f"Tool error: {e}")
            return {"error": str(e)}
    
    def _calculate_cpp(self, args: dict) -> dict:
        """Calculate CPP value."""
        cash = args["cash_price"]
        points = args["points"]
        taxes = args.get("taxes_fees", 0)
        currency = args.get("currency", "delta_skymiles")
        
        cpp = quick_cpp_calc(cash, points, taxes)
        
        # Get thresholds
        min_cpp = self.config.min_cpp.get(currency, 1.0)
        target_cpp = self.config.target_cpp.get(currency, 1.5)
        
        if cpp >= target_cpp * 1.3:
            status = "excellent"
            recommendation = "Book immediately - excellent value!"
        elif cpp >= target_cpp:
            status = "good"
            recommendation = "Good value - worth booking"
        elif cpp >= min_cpp:
            status = "acceptable"
            recommendation = "Meets minimum threshold"
        else:
            status = "poor"
            recommendation = f"Below {min_cpp} cpp threshold - pay cash instead"
        
        return {
            "cpp": cpp,
            "status": status,
            "recommendation": recommendation,
            "thresholds": {
                "minimum": min_cpp,
                "target": target_cpp,
                "excellent": target_cpp * 1.3
            }
        }
    
    def _add_flight_deal(self, args: dict) -> dict:
        """Add cash flight deal."""
        deal = FlightDeal(
            origin=args["origin"].upper(),
            destination=args["destination"].upper(),
            departure_date=date.fromisoformat(args["departure_date"]),
            return_date=date.fromisoformat(args["return_date"]),
            deal_type=DealType.FLIGHT_CASH,
            price_cash=args["price"],
            airline=args.get("airline", "Delta"),
            stops=args.get("stops", 0),
            source=args.get("source", "Manual"),
            found_at=datetime.now()
        )
        
        deal = self.calculator.evaluate_flight_deal(deal)
        key = self.tracker.add_deal(deal)
        
        return {
            "success": True,
            "deal_key": key,
            "status": deal.status.value,
            "total_value": deal.total_value,
            "message": f"Flight deal added: {deal.origin} → {deal.destination} ({deal.status.value})"
        }
    
    def _add_award_flight(self, args: dict) -> dict:
        """Add award flight deal."""
        deal = FlightDeal(
            origin=args["origin"].upper(),
            destination=args["destination"].upper(),
            departure_date=date.fromisoformat(args["departure_date"]),
            return_date=date.fromisoformat(args["return_date"]),
            deal_type=DealType.FLIGHT_AWARD,
            price_points=args["points_per_person"],
            points_currency=args.get("currency", "delta_skymiles"),
            taxes_fees=args.get("taxes_per_person", 5.60),
            airline=args.get("airline", "Delta"),
            cabin_class=CabinClass(args.get("cabin", "economy")),
            source="Manual",
            found_at=datetime.now()
        )
        
        cash_comparison = args.get("cash_comparison")
        deal = self.calculator.evaluate_flight_deal(deal, baseline_cash_price=cash_comparison)
        key = self.tracker.add_deal(deal)
        
        return {
            "success": True,
            "deal_key": key,
            "status": deal.status.value,
            "cpp_value": deal.cpp_value,
            "message": f"Award flight added: {deal.cpp_value:.2f} cpp ({deal.status.value})"
        }
    
    def _add_resort_deal(self, args: dict) -> dict:
        """Add all-inclusive resort deal."""
        from .models import HotelDeal, DealType
        
        deal = HotelDeal(
            destination=args["destination"].upper(),
            property_name=args["property_name"],
            check_in=date.fromisoformat(args["check_in"]),
            check_out=date.fromisoformat(args["check_out"]),
            deal_type=DealType.ALL_INCLUSIVE,
            total_price_cash=args["total_price"],
            is_all_inclusive=True,
            includes_meals=True,
            includes_drinks=True,
            source=args.get("source", "Manual"),
            found_at=datetime.now()
        )
        
        deal = self.calculator.evaluate_hotel_deal(deal)
        key = self.tracker.add_deal(deal)
        
        return {
            "success": True,
            "deal_key": key,
            "status": deal.status.value,
            "per_person_per_night": deal.per_person_per_night,
            "message": f"Resort added: ${deal.per_person_per_night:.0f}/person/night ({deal.status.value})"
        }
    
    def _list_deals(self, args: dict) -> dict:
        """List tracked deals."""
        status_filter = args.get("status", "all")
        limit = args.get("limit", 10)
        
        if status_filter == "all":
            deals = self.tracker.get_all_deals()
        else:
            deals = self.tracker.get_all_deals(DealStatus(status_filter))
        
        # Simplify for output
        simplified = []
        for d in deals[:limit]:
            simplified.append({
                "destination": d.get("destination"),
                "type": d.get("deal_type"),
                "status": d.get("status"),
                "price_cash": d.get("price_cash") or d.get("total_price_cash"),
                "cpp_value": d.get("cpp_value"),
                "departure": d.get("departure_date") or d.get("check_in")
            })
        
        return {
            "total": len(deals),
            "showing": len(simplified),
            "deals": simplified
        }
    
    def _compare_deals(self, args: dict) -> dict:
        """Compare all deals."""
        deals = self.tracker.get_all_deals()
        
        if not deals:
            return {"message": "No deals to compare. Add some deals first."}
        
        # Sort by status
        status_order = {'excellent': 0, 'good': 1, 'acceptable': 2, 'poor': 3}
        deals.sort(key=lambda d: status_order.get(d.get('status', 'poor'), 5))
        
        ranked = []
        for i, d in enumerate(deals[:5], 1):
            ranked.append({
                "rank": i,
                "destination": d.get("destination"),
                "status": d.get("status"),
                "price": d.get("price_cash") or d.get("total_price_cash") or d.get("total_cash_cost", 0),
                "cpp": d.get("cpp_value")
            })
        
        best = ranked[0] if ranked else None
        
        return {
            "best_option": best,
            "ranked_options": ranked,
            "total_compared": len(deals)
        }
    
    def _get_summary(self, args: dict) -> dict:
        """Get deal summary."""
        return self.tracker.get_deals_summary()
    
    def _generate_report(self, args: dict) -> dict:
        """Generate reports."""
        deals = self.tracker.get_all_deals()
        
        if not deals:
            return {"error": "No deals to report on"}
        
        # Generate summary report
        summary = self.reporter.generate_deal_summary(deals)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        path = self.reporter.save_report(summary, f"summary_{timestamp}")
        
        return {
            "success": True,
            "report_path": path,
            "deals_count": len(deals)
        }
    
    def _get_baseline_price(self, args: dict) -> dict:
        """Get baseline price for route."""
        price = self.tracker.get_baseline_price(
            args["origin"].upper(),
            args["destination"].upper(),
            args["month"]
        )
        
        if price:
            return {"baseline_price": price, "route": f"{args['origin']}-{args['destination']}"}
        else:
            return {"error": "No baseline price found for this route"}


def handle_message(message: dict, server: TravelDealsMCP) -> dict:
    """Handle incoming MCP message."""
    method = message.get("method", "")
    msg_id = message.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "travel-deals",
                    "version": "1.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": server.get_tools()}
        }
    
    elif method == "tools/call":
        params = message.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        result = server.call_tool(tool_name, arguments)
        
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            }
        }
    
    elif method == "notifications/initialized":
        return None  # No response for notifications
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"}
        }


def main():
    """Run MCP server on stdio."""
    server = TravelDealsMCP()
    logger.info("Travel Deals MCP server started")
    
    # Read from stdin, write to stdout
    for line in sys.stdin:
        try:
            message = json.loads(line.strip())
            response = handle_message(message, server)
            
            if response:
                print(json.dumps(response), flush=True)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
