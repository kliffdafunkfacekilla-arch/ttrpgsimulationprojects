import asyncio
import sys
sys.path.append('.')
from main import start_campaign, StartCampaignRequest
import traceback

async def run_test():
    try:
        req = StartCampaignRequest(
            player_id="test_500",
            starting_hex_id=200500,
            world_id="W_001",
            party_size="SOLO",
            difficulty="STANDARD",
            style="GRITTY",
            length="SAGA",
            no_fly_list=[]
        )
        res = await start_campaign(req)
        print("SUCCESS!")
        print(res)
    except Exception as e:
        print("FAILED!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
