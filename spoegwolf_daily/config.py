import os
from dotenv import load_dotenv

load_dotenv()

CFG = {
    "TZ": os.getenv("TZ", "Africa/Johannesburg"),
    "PLANKTON_AUTH": os.getenv("PLANKTON_AUTH"),     # e.g., "Bearer abc123" or another scheme
    "PLANKTON_COOKIE": os.getenv("PLANKTON_COOKIE"), # e.g., ".AspNetCore.Session=..."
}

# Shows we care about (string GUIDs). Capacity is your own target number.
SHOWS = [
    {
        "name": "Droomland Pretoria",
        "event_guid": "4607d90a-e34f-4fd4-965f-fff45f528a57",  # replace if needed
        "capacity": 10000,
        # Group mapping for this event: exact names (case/space tolerant)
        "groups": {
            "GA (Adults)": [
                "Early Bird",
                "Phase 1",
                "Phase 2",
                "Phase 3",
            ],
            "Kids Tickets": [
                "Kids Under 12",
                "Kids Under 18",
            ],
            "Goue Kraal": [
                "Goue Kraal (VIP/Golden Circle)",
            ],
            "exclude": [
                "Physical Ticket",
                "Honorary Ranger",
            ],
        },
    },
    {
        "name": "Droomland Kaap",
        "event_guid": "df6e673e-445c-4b75-87e8-790eedc82f0e",  # replace if needed
        "capacity": 3500,
        # Group mapping for this event: exact names (case/space tolerant)
        "groups": {
            "GA (Adults)": [
                "Early Bird",
                "Phase 1",
                "Phase 2",
                "Phase 3",
                "Phase 4",
            ],
            "Kids Tickets": [
                "Kids Under 12",
                "Kids Under 18",
            ],
            "Goue Kraal": [
                "Goue Kraal (VIP)",
            ],
            "exclude": [

            ],
        },
    },
    # Add more shows with their own groups here if needed
]