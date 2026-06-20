import logging
import os

if not os.path.exists("data"):
    os.makedirs("data")
    
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/app.log", encoding="utf-8")
    ]
)

logger = logging.getLogger("portfolio_backend")