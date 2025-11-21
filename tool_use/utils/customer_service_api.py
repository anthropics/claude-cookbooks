"""
Customer Support Ticket System - Mock API
Generate realistic support tickets for compaction demonstration
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


# Ticket Categories
class TicketCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    PRODUCT = "product"
    SHIPPING = "shipping"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    NEW = "new"
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class Ticket:
    """Represents a customer support ticket"""

    id: str
    customer_name: str
    customer_email: str
    subject: str
    description: str
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    status: TicketStatus = TicketStatus.NEW
    created_at: datetime | None = None
    assigned_team: str | None = None
    notes: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


# Mock data generation
class TicketGenerator:
    """Generate realistic support tickets for testing"""

    TICKET_TEMPLATES = [
        # Billing issues
        {
            "category": TicketCategory.BILLING,
            "subjects": [
                "Double charged for subscription",
                "Unable to update payment method",
                "Unexpected charge on my account",
                "Refund request for cancelled service",
                "Billing cycle confusion",
            ],
            "descriptions": [
                "I was charged twice for my monthly subscription. The first charge was on {date1} for ${amount} and another on {date2} for ${amount}. Please refund the duplicate charge.",
                "I've been trying to update my credit card information for the past week but keep getting an error message saying 'Payment method could not be updated.' My card expires next month.",
                "I noticed a charge of ${amount} on {date1} that I don't recognize. I haven't used the service in over a month. Can you help me understand what this charge is for?",
                "I cancelled my subscription on {date1} but was still charged on {date2}. According to your terms, I should not have been billed. Please process a refund.",
                "I'm confused about when my billing cycle starts. I signed up on {date1} but was charged on {date2}, which seems early. Can you clarify?",
            ],
        },
        # Technical issues
        {
            "category": TicketCategory.TECHNICAL,
            "subjects": [
                "Application crashes on startup",
                "Cannot sync data across devices",
                "Export feature not working",
                "Slow performance after recent update",
                "Error message when uploading files",
            ],
            "descriptions": [
                "Ever since the latest update ({version}), the app crashes immediately when I try to open it. I'm on {device} running {os}. I've tried reinstalling but the problem persists.",
                "My data isn't syncing between my phone and desktop. I made changes on my phone yesterday but they're not showing up on my computer. Both devices are connected to the internet.",
                "When I try to export my data as CSV, I get an error: '{error_msg}'. This has been happening for the past 3 days. The export to PDF works fine.",
                "Since updating to version {version} last week, the app has become noticeably slower. Loading times have increased from 2-3 seconds to 15-20 seconds.",
                "I'm trying to upload a {file_type} file ({file_size}MB) but keep getting the error: '{error_msg}'. Files under 10MB upload fine, but anything larger fails.",
            ],
        },
        # Account issues
        {
            "category": TicketCategory.ACCOUNT,
            "subjects": [
                "Cannot reset password",
                "Email verification not working",
                "Account locked after failed login",
                "Want to change email address",
                "Two-factor authentication issues",
            ],
            "descriptions": [
                "I requested a password reset 3 times but haven't received any emails. I've checked spam and all folders. My email is {email}.",
                "I created a new account but never received the verification email. I've tried resending it multiple times. Without verification, I can't access premium features.",
                "My account was locked after I entered the wrong password too many times. I can now remember my correct password but the unlock email link isn't working.",
                "I need to change my account email from {old_email} to {new_email} because I no longer have access to my old email. How can I do this?",
                "I enabled two-factor authentication but lost my phone. I have my backup codes but the system won't accept them. I can't access my account at all now.",
            ],
        },
        # Product questions
        {
            "category": TicketCategory.PRODUCT,
            "subjects": [
                "How to use advanced features",
                "Feature request: Dark mode",
                "Is there a mobile app?",
                "Difference between plans",
                "Integration with third-party tools",
            ],
            "descriptions": [
                "I upgraded to the Pro plan to access the {feature} feature, but I can't figure out how to use it. Is there documentation or a tutorial available?",
                "I would love to see a dark mode option. I use the app late at night and the bright interface strains my eyes. This would be a great addition.",
                "Is there a mobile app for iOS/Android? I can only find the web version and it's not very mobile-friendly. Would really help my workflow.",
                "What's the difference between the Standard and Premium plans? The pricing page mentions 'advanced analytics' but doesn't explain what that includes.",
                "Does your product integrate with {tool_name}? I use it for {workflow} and would love to connect the two. If not, are there plans to add this integration?",
            ],
        },
        # Shipping/delivery
        {
            "category": TicketCategory.SHIPPING,
            "subjects": [
                "Order hasn't arrived yet",
                "Wrong item delivered",
                "Package damaged during shipping",
                "Need to change delivery address",
                "Tracking number not working",
            ],
            "descriptions": [
                "I ordered {product} on {date1} (Order #{order_id}). Tracking shows it was delivered on {date2}, but I never received it. Can you investigate?",
                "I received my order #{order_id} today but it's the wrong item. I ordered {ordered_item} but received {received_item} instead. How do we fix this?",
                "My package (Order #{order_id}) arrived today but the box was badly damaged and the product inside is broken. I need a replacement.",
                "I need to change the delivery address for Order #{order_id}. It hasn't shipped yet according to tracking. Can you update it to {new_address}?",
                "The tracking number {tracking_num} you sent me doesn't work on the carrier's website. It says 'invalid tracking number.' Can you verify?",
            ],
        },
    ]

    @staticmethod
    def generate_ticket(ticket_id: int = None) -> Ticket:
        """Generate a single realistic ticket"""
        template = random.choice(TicketGenerator.TICKET_TEMPLATES)
        category = template["category"]

        # Random values for placeholder substitution
        date1 = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        date2 = (datetime.now() - timedelta(days=random.randint(1, 15))).strftime("%Y-%m-%d")
        amount = random.choice([9.99, 19.99, 29.99, 49.99, 99.99])

        subject = random.choice(template["subjects"])
        description_template = random.choice(template["descriptions"])

        # Replace placeholders
        description = description_template.format(
            date1=date1,
            date2=date2,
            amount=amount,
            email=f"customer{random.randint(1000, 9999)}@example.com",
            old_email=f"old{random.randint(100, 999)}@example.com",
            new_email=f"new{random.randint(100, 999)}@example.com",
            version=f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
            device=random.choice(["iPhone 14", "Samsung Galaxy S23", "iPad Pro", "MacBook Pro"]),
            os=random.choice(["iOS 17", "Android 14", "macOS 14.2", "Windows 11"]),
            error_msg=random.choice(
                ["ERR_CONNECTION_TIMEOUT", "FILE_TOO_LARGE", "INVALID_FORMAT", "PERMISSION_DENIED"]
            ),
            file_type=random.choice(["PDF", "DOCX", "PNG", "CSV"]),
            file_size=random.randint(15, 100),
            feature=random.choice(
                ["analytics dashboard", "bulk import", "API access", "custom reports"]
            ),
            tool_name=random.choice(["Slack", "Salesforce", "Zapier", "Google Sheets"]),
            workflow=random.choice(["project management", "customer tracking", "data analysis"]),
            product=random.choice(
                ["Wireless Headphones", "Smart Watch", "Laptop Stand", "USB-C Hub"]
            ),
            order_id=f"ORD-{random.randint(10000, 99999)}",
            ordered_item=random.choice(["Blue Widget Pro", "Red Gadget Plus", "Green Device Max"]),
            received_item=random.choice(
                ["Yellow Widget Lite", "Purple Gadget Basic", "Orange Device Mini"]
            ),
            new_address="456 New St, Different City, ST 12345",
            tracking_num=f"1Z{random.randint(100000000000, 999999999999)}",
        )

        ticket_id_str = f"TICKET-{ticket_id if ticket_id else random.randint(1000, 9999)}"

        return Ticket(
            id=ticket_id_str,
            customer_name=f"{random.choice(['John', 'Jane', 'Alex', 'Sam', 'Chris', 'Morgan'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Davis'])}",
            customer_email=f"customer{random.randint(1000, 9999)}@example.com",
            subject=subject,
            description=description,
            category=category,
            priority=None,  # To be determined by agent
            status=TicketStatus.NEW,
            created_at=datetime.now() - timedelta(hours=random.randint(0, 48)),
        )

    @staticmethod
    def generate_batch(count: int = 25) -> list[Ticket]:
        """Generate a batch of tickets"""
        return [TicketGenerator.generate_ticket(i + 1) for i in range(count)]


# Knowledge base mock data
KNOWLEDGE_BASE = {
    "billing": {
        "refund_policy": "Refunds are processed within 5-7 business days for valid cancellations. Pro-rated refunds available for annual plans.",
        "payment_methods": "We accept Visa, Mastercard, American Express, and PayPal. Update payment methods in Account Settings.",
        "billing_cycle": "Billing occurs on the same date each month/year from your original signup date.",
    },
    "technical": {
        "common_errors": {
            "ERR_CONNECTION_TIMEOUT": "Check internet connection and firewall settings. Try disabling VPN.",
            "FILE_TOO_LARGE": "Maximum upload size is 100MB per file. Compress or split larger files.",
            "INVALID_FORMAT": "Supported formats: PDF, DOCX, PNG, JPG, CSV. Check file extension.",
        },
        "system_requirements": "Minimum: 4GB RAM, modern browser (Chrome 90+, Firefox 88+, Safari 14+)",
        "troubleshooting": "Clear cache and cookies, try incognito mode, ensure JavaScript is enabled",
    },
    "account": {
        "password_reset": "Password reset emails sent from noreply@support.example.com. Check spam folder. Link expires in 1 hour.",
        "2fa_backup": "Each backup code can be used once. Contact support if all codes are lost with account verification.",
        "email_change": "Email changes require verification of both old and new addresses for security.",
    },
}


# Team routing rules
TEAM_ROUTING = {
    TicketCategory.BILLING: "billing-team",
    TicketCategory.TECHNICAL: "tech-support",
    TicketCategory.ACCOUNT: "account-services",
    TicketCategory.PRODUCT: "product-success",
    TicketCategory.SHIPPING: "logistics-team",
}


# Priority rules
def determine_priority(ticket: Ticket) -> TicketPriority:
    """Simple priority determination rules"""
    urgent_keywords = ["can't access", "locked out", "lost access", "urgent", "immediately"]
    high_keywords = ["not working", "broken", "error", "crashes", "failed"]

    description_lower = ticket.description.lower()

    if any(keyword in description_lower for keyword in urgent_keywords):
        return TicketPriority.URGENT
    elif any(keyword in description_lower for keyword in high_keywords):
        return TicketPriority.HIGH
    elif ticket.category == TicketCategory.BILLING:
        return TicketPriority.HIGH
    else:
        return TicketPriority.MEDIUM


def process_ticket(ticket: Ticket) -> Ticket:
    """Process a ticket: assign priority and team"""
    ticket.priority = determine_priority(ticket)
    if ticket.category:
        ticket.assigned_team = TEAM_ROUTING.get(ticket.category, "general-support")
    else:
        ticket.assigned_team = "general-support"
    return ticket


def main():
    """Demonstrate the customer service ticket system"""
    print("=" * 80)
    print("Customer Support Ticket System - Demo")
    print("=" * 80)
    print()

    # Generate batch of tickets
    num_tickets = 50
    print(f"Generating {num_tickets} support tickets...")
    tickets = TicketGenerator.generate_batch(num_tickets)
    print(f"✓ Generated {len(tickets)} tickets\n")

    # Process tickets
    print("Processing tickets (categorization, prioritization, routing)...")
    processed_tickets = [process_ticket(ticket) for ticket in tickets]
    print(f"✓ Processed {len(processed_tickets)} tickets\n")

    # Summary statistics
    print("=" * 80)
    print("Summary Statistics")
    print("=" * 80)

    category_counts = {}
    priority_counts = {}
    team_counts = {}

    for ticket in processed_tickets:
        if ticket.category:
            category_counts[ticket.category.value] = (
                category_counts.get(ticket.category.value, 0) + 1
            )
        if ticket.priority:
            priority_counts[ticket.priority.value] = (
                priority_counts.get(ticket.priority.value, 0) + 1
            )
        if ticket.assigned_team:
            team_counts[ticket.assigned_team] = team_counts.get(ticket.assigned_team, 0) + 1

    print("\nBy Category:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category.capitalize()}: {count}")

    print("\nBy Priority:")
    for priority, count in sorted(
        priority_counts.items(), key=lambda x: ["low", "medium", "high", "urgent"].index(x[0])
    ):
        print(f"  {priority.capitalize()}: {count}")

    print("\nBy Team:")
    for team, count in sorted(team_counts.items()):
        print(f"  {team}: {count}")

    # Display sample tickets
    print("\n" + "=" * 80)
    print("Sample Tickets")
    print("=" * 80)

    for i, ticket in enumerate(processed_tickets[:10], 1):
        print(f"\nTicket #{i}")
        print(f"  ID: {ticket.id}")
        print(f"  Customer: {ticket.customer_name} ({ticket.customer_email})")
        print(f"  Subject: {ticket.subject}")
        print(f"  Category: {ticket.category.value if ticket.category else 'unclassified'}")
        print(f"  Priority: {ticket.priority.value if ticket.priority else 'unset'}")
        print(f"  Status: {ticket.status.value}")
        print(f"  Assigned Team: {ticket.assigned_team or 'unassigned'}")
        print(
            f"  Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.created_at else 'unknown'}"
        )
        print(f"  Description: {ticket.description[:100]}...")

    print("\n" + "=" * 80)
    print(f"Demo complete! {len(processed_tickets)} tickets ready for processing.")
    print("=" * 80)

    return processed_tickets


if __name__ == "__main__":
    main()
