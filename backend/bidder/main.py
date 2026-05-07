import os
from dotenv import load_dotenv

# Load .env before importing any pipeline modules so ANTHROPIC_API_KEY
# is in os.environ when index_extractor.py and criteria_mapper.py are imported.
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from pipeline.pipeline_runner import BidderPipeline

if __name__ == "__main__":
    pipeline = BidderPipeline("data/input/bidder1.pdf")
    pipeline.run()
    pipeline.save_output()