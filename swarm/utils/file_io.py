import os
from ..core.negotiation import Negotiation
from datetime import datetime

def save_log(n: Negotiation) -> None:
    folder = os.path.join("logs", n.id)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "chat.txt"), "w", encoding="utf-8") as f:
        for i, t in enumerate(n.turns):
            # t.timestamp es un float (segundos desde epoch)
            # Puedes formatearlo como fecha legible:
            ts = datetime.fromtimestamp(t.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{i}] [{ts}] {t.sender_id}: {t.message}\n") 