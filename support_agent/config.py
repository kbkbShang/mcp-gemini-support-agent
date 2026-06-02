from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
KB_DIR = DATA_DIR / "kb"
TICKETS_DIR = DATA_DIR / "tickets"
TICKETS_FILE = TICKETS_DIR / "history.json"
TICKET_DRAFTS_FILE = TICKETS_DIR / "ticket_drafts.json"
