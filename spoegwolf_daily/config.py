import os
from dotenv import load_dotenv

load_dotenv()

CFG = {
    "TZ": os.getenv("TZ", "Africa/Johannesburg"),
    "PLANKTON_AUTH": os.getenv("PLANKTON_AUTH"),
    "PLANKTON_COOKIE": os.getenv("PLANKTON_COOKIE"),
    # Shopify
    "SHOPIFY_BASE": os.getenv("SHOPIFY_BASE"),
    "SHOPIFY_ACCESS_TOKEN": os.getenv("SHOPIFY_ACCESS_TOKEN"),
    #GMAIL
    "EMAIL_HOST": os.getenv("EMAIL_HOST", "smtp.gmail.com"),
    "EMAIL_PORT": os.getenv("EMAIL_PORT", "465"),
    "EMAIL_USER": os.getenv("EMAIL_USER"),
    "EMAIL_PASS": os.getenv("EMAIL_PASS"),
    "EMAIL_TO":   os.getenv("EMAIL_TO"),  # comma-separated list
        # --- Quicket ---
    "QUICKET_API_KEY": os.getenv("QUICKET_API_KEY"),
    "QUICKET_USERTOKEN": os.getenv("QUICKET_USERTOKEN"),
}

# You’ll manually maintain this list (like SHOWS)
# Example structure; update names/capacities/types to your real events:
QUICKET_EVENTS = [
    # {
    #   "id": 329997,
    #   "name": "Your Quicket Show",
    #   "capacity": 10000,
    #   "groups": {
    #       "Adults": ["Algemene Toegang","Adult GA"],
    #       "Kids":   ["Kinders","Kids"],
    #       "exclude":["Honorary","Complimentary","Merchandise"]  # optional
    #   }
    # },
    {
      "id": 342395,
      "name": "Stanford Hills",
      "capacity": 1200,
      "event_date": "2025-12-16",  # optional override
      "groups": {
          "Adults": ["General Admission"],
          "Kids":   ["Kids Under 13"],
          "exclude":["Honorary","Complimentary","Merchandise"]  # optional
      }
    },
    {
      "id": 342479,
      "name": "Stilbaai (2 aande)",
      "capacity": 1000,
      "event_date": "2025-12-17",  # optional override
      "groups": {
          "Adults": ["Algemene Toegang"],
          "Kids":   ["Kids Under 13"],
          "exclude":["Honorary","Complimentary","Merchandise"]  # optional
      }
    },
    {
      "id": 344383,
      "name": "NYE Daisy Jones",
      "capacity": 550,
      "event_date": "2025-12-31",  # optional override
      "groups": {
          "Adults": ["Algemene Toegang", "VIP Balkon"],
          "Kids":   ["Kids Under 13"],
          "exclude":["Honorary","Complimentary","Merchandise"]  # optional
      }
    },
]

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