"""
Report Generator

Creates:
- Comparison reports (Markdown)
- Decision matrices
- Deal summaries
- Booking instruction guides
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional

from .models import DealStatus


class ReportGenerator:
    """
    Generates reports and comparison matrices for deal analysis.
    
    Output formats:
    - Markdown (for viewing in terminals/editors)
    - JSON (for programmatic use)
    - HTML (for email/web viewing)
    """
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    # -------------------------------------------------------------------------
    # Main Report Types
    # -------------------------------------------------------------------------
    
    def generate_comparison_report(
        self,
        comparison_matrix: Dict,
        title: str = "Trip Comparison Report"
    ) -> str:
        """
        Generate a comparison report from a comparison matrix.
        
        This is the main output format - shows all options side by side.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        lines = [
            f"# {title}",
            f"*Generated: {timestamp}*",
            "",
            "---",
            ""
        ]
        
        # Summary stats
        best_value = comparison_matrix.get('best_value', 'N/A')
        lowest_cost = comparison_matrix.get('lowest_cost', 'N/A')
        
        lines.extend([
            "## Quick Picks",
            "",
            f"- **Best Value:** {best_value}",
            f"- **Lowest Cost:** {lowest_cost}",
            "",
            "---",
            ""
        ])
        
        # Detailed options
        lines.append("## Ranked Options")
        lines.append("")
        
        for option in comparison_matrix.get('ranked_options', []):
            status_emoji = {
                'excellent': '🔥',
                'good': '✅',
                'acceptable': '👍',
                'poor': '⚠️'
            }.get(option.get('status', ''), '❓')
            
            lines.extend([
                f"### #{option['rank']}: {option['destination']} {status_emoji}",
                "",
                f"**Dates:** {option['dates']}",
                f"**Total Cost:** ${option['total_cost']:,.0f}",
            ])
            
            if option.get('points_used'):
                lines.append(f"**Points Used:** {option['points_used']:,}")
            
            if option.get('savings_pct'):
                lines.append(f"**Savings:** {option['savings_pct']:.0f}% below baseline")
            
            lines.append("")
            
            # Pros/Cons
            if option.get('pros'):
                lines.append("**Pros:**")
                for pro in option['pros']:
                    lines.append(f"- ✓ {pro}")
                lines.append("")
            
            if option.get('cons'):
                lines.append("**Cons:**")
                for con in option['cons']:
                    lines.append(f"- ✗ {con}")
                lines.append("")
            
            # Recommendation
            lines.extend([
                "**Assessment:**",
                "```",
                option.get('recommendation', 'No recommendation available'),
                "```",
                ""
            ])
            
            # Booking steps
            if option.get('booking_steps'):
                lines.append("**Booking Steps:**")
                for step in option['booking_steps']:
                    lines.append(f"{step['step']}. {step['action']}")
                    if step.get('notes'):
                        lines.append(f"   *{step['notes']}*")
                    if step.get('url'):
                        lines.append(f"   Link: {step['url']}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_deal_summary(
        self,
        deals: List[dict],
        title: str = "Deal Summary"
    ) -> str:
        """Generate a summary report of all tracked deals."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        lines = [
            f"# {title}",
            f"*Generated: {timestamp}*",
            "",
            f"**Total Deals:** {len(deals)}",
            ""
        ]
        
        # Group by status
        by_status = {}
        for deal in deals:
            status = deal.get('status', 'unknown')
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(deal)
        
        # Excellent deals first
        if 'excellent' in by_status:
            lines.extend([
                "## 🔥 Excellent Deals",
                ""
            ])
            for deal in by_status['excellent']:
                lines.append(self._format_deal_summary_line(deal))
            lines.append("")
        
        # Good deals
        if 'good' in by_status:
            lines.extend([
                "## ✅ Good Deals",
                ""
            ])
            for deal in by_status['good']:
                lines.append(self._format_deal_summary_line(deal))
            lines.append("")
        
        # Others
        other_statuses = [s for s in by_status.keys() if s not in ['excellent', 'good']]
        if other_statuses:
            lines.append("## Other Deals")
            lines.append("")
            for status in other_statuses:
                for deal in by_status[status]:
                    lines.append(self._format_deal_summary_line(deal))
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_deal_summary_line(self, deal: dict) -> str:
        """Format a single deal for summary listing."""
        deal_type = deal.get('deal_type', '')
        
        if 'flight' in deal_type:
            route = f"{deal.get('origin', '?')} → {deal.get('destination', '?')}"
            price = f"${deal.get('price_cash', 0):,.0f}" if deal.get('price_cash') else f"{deal.get('price_points', 0):,} pts"
            return f"- ✈️ {route} | {deal.get('departure_date', '')} | {price} | {deal.get('airline', '')}"
        
        elif 'hotel' in deal_type or 'inclusive' in deal_type:
            prop = deal.get('property_name', 'Unknown')[:30]
            price = f"${deal.get('price_per_night_cash', 0):,.0f}/night" if deal.get('price_per_night_cash') else "N/A"
            return f"- 🏨 {prop} | {deal.get('check_in', '')} | {price}"
        
        else:
            return f"- {deal.get('destination', 'Unknown')} | {deal.get('departure_date', '')}"
    
    # -------------------------------------------------------------------------
    # Decision Matrix
    # -------------------------------------------------------------------------
    
    def generate_decision_matrix(
        self,
        options: List[dict],
        criteria: List[str] = None
    ) -> str:
        """
        Generate a decision matrix table.
        
        Default criteria: Cost, Value, Convenience, Experience
        """
        if criteria is None:
            criteria = ['Total Cost', 'Value Score', 'Convenience', 'Family Friendly']
        
        lines = [
            "# Decision Matrix",
            "",
            "| Option | " + " | ".join(criteria) + " | **Score** |",
            "|--------|" + "|".join(["--------"] * len(criteria)) + "|---------|"
        ]
        
        for opt in options:
            dest = opt.get('destination', 'Unknown')[:15]
            
            # Calculate scores for each criterion
            scores = []
            
            for criterion in criteria:
                if criterion == 'Total Cost':
                    cost = opt.get('total_cost', 0)
                    # Lower is better - normalize to 1-5
                    if cost <= 5000:
                        score = 5
                    elif cost <= 7500:
                        score = 4
                    elif cost <= 10000:
                        score = 3
                    elif cost <= 12000:
                        score = 2
                    else:
                        score = 1
                    scores.append(f"${cost:,.0f} ({score}⭐)")
                    
                elif criterion == 'Value Score':
                    status = opt.get('status', '')
                    score_map = {'excellent': 5, 'good': 4, 'acceptable': 3, 'poor': 1}
                    score = score_map.get(status, 2)
                    scores.append(f"{status} ({score}⭐)")
                    
                elif criterion == 'Convenience':
                    # Based on stops, direct flights
                    pros = opt.get('pros', [])
                    score = 3  # Base
                    if 'Nonstop flights' in pros:
                        score += 1
                    if 'All-inclusive' in pros:
                        score += 1
                    scores.append(f"{score}⭐")
                    
                elif criterion == 'Family Friendly':
                    # Default to 4 for known destinations
                    scores.append("4⭐")
                    
                else:
                    scores.append("N/A")
            
            # Calculate total score
            total = sum([
                int(s.split('(')[1][0]) if '(' in str(s) and '⭐' in str(s) else 3
                for s in scores
            ])
            
            row = f"| {dest} | " + " | ".join(str(s) for s in scores) + f" | **{total}** |"
            lines.append(row)
        
        lines.extend([
            "",
            "*Higher scores = better option*"
        ])
        
        return "\n".join(lines)
    
    # -------------------------------------------------------------------------
    # Booking Guide
    # -------------------------------------------------------------------------
    
    def generate_booking_guide(
        self,
        package: dict,
        points_portfolio: dict = None
    ) -> str:
        """Generate step-by-step booking instructions."""
        
        lines = [
            "# Booking Guide",
            f"**Destination:** {package.get('destination')}",
            f"**Dates:** {package.get('departure_date')} to {package.get('return_date')}",
            "",
            "---",
            ""
        ]
        
        # Points transfer section
        if package.get('total_points_used', 0) > 0:
            lines.extend([
                "## Step 1: Transfer Points",
                "",
                "Before booking, transfer points if using award flights:",
                ""
            ])
            
            if points_portfolio:
                lines.append(f"**Your Portfolio:**")
                for currency, balance in points_portfolio.items():
                    lines.append(f"- {currency}: {balance:,}")
                lines.append("")
            
            lines.extend([
                "**Transfer Links:**",
                "- Amex MR: https://global.americanexpress.com/rewards/summary",
                "- Note: Transfers typically complete in 24-48 hours",
                "",
            ])
        
        # Flight booking
        if package.get('flight'):
            flight = package['flight']
            lines.extend([
                "## Step 2: Book Flights",
                "",
                f"**Route:** {flight.get('origin', 'MSP')} → {flight.get('destination', '')}",
                f"**Airline:** {flight.get('airline', 'Unknown')}",
                ""
            ])
            
            if flight.get('deal_type') == 'flight_award':
                lines.extend([
                    "**Award Booking:**",
                    f"- Points needed: {flight.get('price_points', 0):,} per person",
                    f"- Total for family: {flight.get('price_points', 0) * 4:,}",
                    f"- Taxes/fees: ${flight.get('taxes_fees', 0) * 4:,.0f}",
                    ""
                ])
            else:
                lines.extend([
                    "**Cash Booking:**",
                    f"- Total: ${flight.get('price_cash', 0):,.0f}",
                    ""
                ])
            
            lines.extend([
                f"**Book at:** {flight.get('booking_url', 'delta.com')}",
                "",
            ])
        
        # Hotel booking
        if package.get('hotel'):
            hotel = package['hotel']
            lines.extend([
                "## Step 3: Book Accommodations",
                "",
                f"**Property:** {hotel.get('property_name', '')}",
                f"**Dates:** {hotel.get('check_in')} to {hotel.get('check_out')}",
                ""
            ])
            
            if hotel.get('is_all_inclusive'):
                lines.append("🌴 **All-Inclusive** - Meals, drinks, and activities included!")
                lines.append("")
            
            lines.extend([
                f"**Price:** ${hotel.get('total_price_cash', 0):,.0f} total",
                f"**Per Person/Night:** ${hotel.get('per_person_per_night', 0):,.0f}",
                "",
                f"**Book at:** {hotel.get('booking_url', '')}",
                ""
            ])
        
        # Summary
        lines.extend([
            "---",
            "",
            "## Cost Summary",
            "",
            f"- **Total Cash:** ${package.get('total_cash_cost', 0):,.0f}",
            f"- **Points Used:** {package.get('total_points_used', 0):,}",
            f"- **Per Person:** ${package.get('cost_per_person', 0):,.0f}",
            "",
            "*Remember: Black Friday deals may have limited availability - book quickly!*"
        ])
        
        return "\n".join(lines)
    
    # -------------------------------------------------------------------------
    # File Output
    # -------------------------------------------------------------------------
    
    def save_report(
        self,
        content: str,
        filename: str,
        format: str = "md"
    ) -> str:
        """Save report to file."""
        if not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        return str(filepath)
    
    def save_json_report(self, data: dict, filename: str) -> str:
        """Save report as JSON."""
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(filepath)
    
    def generate_all_reports(
        self,
        comparison_matrix: dict,
        deals: List[dict],
        best_package: dict = None,
        points_portfolio: dict = None
    ) -> Dict[str, str]:
        """Generate all report types and save to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        saved_files = {}
        
        # Comparison report
        comparison = self.generate_comparison_report(comparison_matrix)
        saved_files['comparison'] = self.save_report(
            comparison, 
            f"comparison_{timestamp}"
        )
        
        # Deal summary
        summary = self.generate_deal_summary(deals)
        saved_files['summary'] = self.save_report(
            summary,
            f"summary_{timestamp}"
        )
        
        # Decision matrix
        if comparison_matrix.get('ranked_options'):
            matrix = self.generate_decision_matrix(comparison_matrix['ranked_options'])
            saved_files['matrix'] = self.save_report(
                matrix,
                f"decision_matrix_{timestamp}"
            )
        
        # Booking guide for best option
        if best_package:
            guide = self.generate_booking_guide(best_package, points_portfolio)
            saved_files['booking_guide'] = self.save_report(
                guide,
                f"booking_guide_{timestamp}"
            )
        
        # JSON data export
        saved_files['data_json'] = self.save_json_report(
            {
                'comparison': comparison_matrix,
                'deals': deals,
                'generated_at': timestamp
            },
            f"data_{timestamp}"
        )
        
        return saved_files
