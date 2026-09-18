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

 

    #     {
    #   "id": 349783,
    #   "name": "Snowflake Potch",
    #   "capacity": 2000,
    #   "event_date": "2026-02-21",  # optional override
    #   "groups": {
    #       "Adults": ["Early Bird", "Fase Een", "Fase Twee"],
    #       "Kids":   ["Kids Under 13"],
    #       "exclude":["Honorary","Complimentary","Merchandise"]  # optional
    #   }
    # },
]

# Shows we care about (string GUIDs). Capacity is your own target number.
SHOWS = [

    {
        "name": "Droomland Kaap",
        "event_guid": "bb525e91-e9f2-4f5a-9fde-82af179c5f77",  # replace if needed
        "capacity": 3500,
        # Group mapping for this event: exact names (case/space tolerant)
        "groups": {
            "GA (Adults)": [
                "Early Bird",
                "Fase 1",
                "Fase 2",
                "Fase 3",
                "Fase 4",
            ],
            "Kids Tickets": [
                "Kids Under 12",
                "Kids Under 6",
            ],
            "Goue Kraal": [
                "Goue Kraal",
            ],
            "exclude": [

            ],
        },
    },
     {
        "name": "Droomland Pretoria",
        "event_guid": "a171ec24-80e7-4aa5-be79-c2d395050a11",  # replace if needed
        "capacity": 10000,
        # Group mapping for this event: exact names (case/space tolerant)
        "groups": {
            "GA (Adults)": [
                "Early Bird",
                "Fase 1",
                "Fase 2",
                "Fase 3",
                "Fase 4",
            ],
            "Kids Tickets": [
                "Kids Under 12",
                "Kids Under 6",
            ],
            "Goue Kraal": [
                "Goue Kraal",
            ],
            "exclude": [

            ],
        },
    },
    # Add more shows with their own groups here if needed
]

ITICKETS_EVENTS = [
    # {
    #     "eid": "486660",
    #     "name": "Spoegwolf op Ys 2027 (iTickets)",
    #     "capacity": 8000,  # set later if you know cap
    #     "event_date_date": "2027-08-10",
    #     "feed_url_env": "ITICKETS_FEED_OYS",  # GitHub secret name (full URL)
    # }
]