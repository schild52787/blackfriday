"""
Alert System

Handles:
- Email notifications for excellent deals
- Alert throttling (quiet hours, deduplication)
- Alert formatting and templates
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, time
from typing import Optional, List, Dict
import os
import json
from pathlib import Path

from .models import DealStatus, FlightDeal, HotelDeal, TripPackage

logger = logging.getLogger(__name__)


class AlertSystem:
    """
    Manages deal alerts and notifications.
    
    Features:
    - Email alerts for excellent/good deals
    - Quiet hours (no notifications 10pm-7am)
    - Alert deduplication (don't spam same deal)
    - Alert history tracking
    """
    
    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: str = "",
        recipient_email: str = "",
        password_env_var: str = "EMAIL_APP_PASSWORD",
        quiet_start: str = "22:00",
        quiet_end: str = "07:00",
        timezone: str = "America/Chicago",
        data_dir: str = "data"
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.recipient_email = recipient_email
        self.password = os.environ.get(password_env_var, "")
        
        # Parse quiet hours
        self.quiet_start = datetime.strptime(quiet_start, "%H:%M").time()
        self.quiet_end = datetime.strptime(quiet_end, "%H:%M").time()
        self.timezone = timezone
        
        # Alert history
        self.data_dir = Path(data_dir)
        self.alert_history_file = self.data_dir / "alert_history.json"
        self.alert_history = self._load_alert_history()
    
    def _load_alert_history(self) -> Dict[str, dict]:
        """Load alert history from file."""
        if self.alert_history_file.exists():
            try:
                with open(self.alert_history_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _save_alert_history(self):
        """Save alert history to file."""
        self.data_dir.mkdir(exist_ok=True)
        with open(self.alert_history_file, 'w') as f:
            json.dump(self.alert_history, f, indent=2)
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        now = datetime.now().time()
        
        # Handle overnight quiet hours (e.g., 22:00 - 07:00)
        if self.quiet_start > self.quiet_end:
            return now >= self.quiet_start or now <= self.quiet_end
        else:
            return self.quiet_start <= now <= self.quiet_end
    
    def _was_recently_alerted(self, deal_key: str, hours: int = 24) -> bool:
        """Check if we already alerted for this deal recently."""
        if deal_key not in self.alert_history:
            return False
        
        last_alert = self.alert_history[deal_key].get('last_alert')
        if not last_alert:
            return False
        
        last_time = datetime.fromisoformat(last_alert)
        age_hours = (datetime.now() - last_time).total_seconds() / 3600
        
        return age_hours < hours
    
    def _record_alert(self, deal_key: str, alert_type: str):
        """Record that we sent an alert."""
        self.alert_history[deal_key] = {
            'last_alert': datetime.now().isoformat(),
            'alert_type': alert_type,
            'count': self.alert_history.get(deal_key, {}).get('count', 0) + 1
        }
        self._save_alert_history()
    
    # -------------------------------------------------------------------------
    # Alert Decision
    # -------------------------------------------------------------------------
    
    def should_alert(
        self, 
        deal: dict, 
        force: bool = False,
        ignore_quiet_hours: bool = False
    ) -> tuple[bool, str]:
        """
        Determine if we should send an alert for this deal.
        
        Returns:
            (should_alert: bool, reason: str)
        """
        deal_key = deal.get('_key', str(deal))
        status = deal.get('status', '')
        
        # Always allow forced alerts
        if force:
            return True, "Forced alert"
        
        # Check status threshold
        if status not in ['excellent', 'good']:
            return False, f"Deal status '{status}' below alert threshold"
        
        # Check quiet hours
        if not ignore_quiet_hours and self._is_quiet_hours():
            return False, "Quiet hours - alert queued"
        
        # Check for recent duplicate
        if self._was_recently_alerted(deal_key):
            return False, "Already alerted for this deal in last 24 hours"
        
        return True, f"Alert triggered for {status} deal"
    
    # -------------------------------------------------------------------------
    # Alert Formatting
    # -------------------------------------------------------------------------
    
    def _format_flight_deal(self, deal: dict) -> str:
        """Format flight deal for alert."""
        lines = [
            f"✈️ **FLIGHT DEAL** - {deal.get('status', '').upper()}",
            "",
            f"**Route:** {deal.get('origin')} → {deal.get('destination')}",
            f"**Dates:** {deal.get('departure_date')} to {deal.get('return_date')}",
            f"**Airline:** {deal.get('airline', 'Unknown')}",
            f"**Cabin:** {deal.get('cabin_class', 'economy').title()}",
            ""
        ]
        
        if deal.get('price_cash'):
            lines.append(f"**Cash Price:** ${deal['price_cash']:,.0f}")
        if deal.get('price_points'):
            lines.append(f"**Award Price:** {deal['price_points']:,} {deal.get('points_currency', 'points')}/person")
            lines.append(f"**Taxes/Fees:** ${deal.get('taxes_fees', 0):.0f}")
        if deal.get('cpp_value'):
            lines.append(f"**Value:** {deal['cpp_value']:.2f} cents/point")
        
        lines.extend([
            "",
            f"**Source:** {deal.get('source', 'Manual entry')}",
            f"**Booking:** {deal.get('booking_url', 'N/A')}"
        ])
        
        return "\n".join(lines)
    
    def _format_hotel_deal(self, deal: dict) -> str:
        """Format hotel deal for alert."""
        lines = [
            f"🏨 **HOTEL DEAL** - {deal.get('status', '').upper()}",
            "",
            f"**Property:** {deal.get('property_name')}",
            f"**Destination:** {deal.get('destination')}",
            f"**Dates:** {deal.get('check_in')} to {deal.get('check_out')}",
            ""
        ]
        
        if deal.get('is_all_inclusive'):
            lines.append("🌴 **ALL-INCLUSIVE**")
        
        if deal.get('price_per_night_cash'):
            lines.append(f"**Per Night:** ${deal['price_per_night_cash']:,.0f}")
        if deal.get('total_price_cash'):
            lines.append(f"**Total:** ${deal['total_price_cash']:,.0f}")
        if deal.get('per_person_per_night'):
            lines.append(f"**Per Person/Night:** ${deal['per_person_per_night']:,.0f}")
        
        lines.extend([
            "",
            f"**Source:** {deal.get('source', 'Manual entry')}",
            f"**Booking:** {deal.get('booking_url', 'N/A')}"
        ])
        
        return "\n".join(lines)
    
    def _format_package_deal(self, deal: dict) -> str:
        """Format package deal for alert."""
        lines = [
            f"📦 **TRIP PACKAGE** - {deal.get('status', '').upper()}",
            "",
            f"**Destination:** {deal.get('destination')}",
            f"**Dates:** {deal.get('departure_date')} to {deal.get('return_date')}",
            "",
            f"**Total Cost:** ${deal.get('total_cash_cost', 0):,.0f}",
            f"**Points Used:** {deal.get('total_points_used', 0):,}",
            f"**Per Person/Day:** ${deal.get('cost_per_person_per_day', 0):,.0f}",
            ""
        ]
        
        if deal.get('savings_pct'):
            lines.append(f"**Savings:** {deal['savings_pct']:.0f}% below baseline")
        
        lines.extend([
            "",
            "**Recommendation:**",
            deal.get('recommendation', 'N/A')
        ])
        
        return "\n".join(lines)
    
    def format_deal_alert(self, deal: dict) -> str:
        """Format a deal for alert notification."""
        deal_type = deal.get('deal_type', '')
        
        if 'flight' in deal_type:
            return self._format_flight_deal(deal)
        elif 'hotel' in deal_type or 'inclusive' in deal_type:
            return self._format_hotel_deal(deal)
        elif deal.get('flight') or deal.get('hotel'):
            return self._format_package_deal(deal)
        else:
            # Generic format
            return f"Deal Alert: {json.dumps(deal, indent=2, default=str)}"
    
    # -------------------------------------------------------------------------
    # Send Alerts
    # -------------------------------------------------------------------------
    
    def send_email_alert(
        self,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send email alert.
        
        Returns:
            True if sent successfully
        """
        if not self.sender_email or not self.recipient_email or not self.password:
            logger.warning("Email not configured - alert not sent")
            print(f"\n📧 ALERT (email not configured):\n{subject}\n\n{body}")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Plain text
            msg.attach(MIMEText(body, 'plain'))
            
            # HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(msg)
            
            logger.info(f"Alert sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            print(f"\n📧 ALERT (send failed):\n{subject}\n\n{body}")
            return False
    
    def alert_deal(
        self,
        deal: dict,
        force: bool = False
    ) -> bool:
        """
        Send alert for a deal if appropriate.
        
        Returns:
            True if alert was sent
        """
        deal_key = deal.get('_key', str(hash(str(deal))))
        
        # Check if we should alert
        should_send, reason = self.should_alert(deal, force=force)
        
        if not should_send:
            logger.debug(f"Alert skipped: {reason}")
            return False
        
        # Format the alert
        body = self.format_deal_alert(deal)
        
        # Determine subject
        status = deal.get('status', 'deal')
        dest = deal.get('destination', 'Unknown')
        subject = f"🔥 {status.upper()} Travel Deal: {dest}"
        
        # Send
        success = self.send_email_alert(subject, body)
        
        if success:
            self._record_alert(deal_key, status)
        
        return success
    
    def alert_multiple_deals(
        self,
        deals: List[dict],
        force: bool = False
    ) -> int:
        """
        Send alerts for multiple deals.
        
        Returns:
            Number of alerts sent
        """
        sent = 0
        for deal in deals:
            if self.alert_deal(deal, force=force):
                sent += 1
        return sent
    
    def send_daily_summary(self, summary: Dict) -> bool:
        """Send daily summary email."""
        subject = f"📊 Travel Deal Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        lines = [
            "# Daily Travel Deal Summary",
            "",
            f"**Total Deals Tracked:** {summary.get('total_deals', 0)}",
            f"**Excellent Deals:** {summary.get('excellent_count', 0)}",
            f"**Good Deals:** {summary.get('good_count', 0)}",
            "",
            "## By Destination:",
        ]
        
        for dest, count in summary.get('by_destination', {}).items():
            lines.append(f"- {dest}: {count}")
        
        lines.extend([
            "",
            "## By Status:",
        ])
        
        for status, count in summary.get('by_status', {}).items():
            lines.append(f"- {status}: {count}")
        
        body = "\n".join(lines)
        
        return self.send_email_alert(subject, body)


def create_alert_system(config_path: str = "config/settings.yaml") -> AlertSystem:
    """Create alert system from config file."""
    import yaml
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    alerts_config = config.get('alerts', {})
    email_config = alerts_config.get('email', {})
    quiet_hours = alerts_config.get('quiet_hours', {})
    
    return AlertSystem(
        smtp_server=email_config.get('smtp_server', 'smtp.gmail.com'),
        smtp_port=email_config.get('smtp_port', 587),
        sender_email=email_config.get('sender', ''),
        recipient_email=email_config.get('recipient', ''),
        password_env_var=email_config.get('password_env_var', 'EMAIL_APP_PASSWORD'),
        quiet_start=quiet_hours.get('start', '22:00'),
        quiet_end=quiet_hours.get('end', '07:00'),
        timezone=quiet_hours.get('timezone', 'America/Chicago')
    )
