from fastapi import FastAPI
from datetime import date
import httpx
import logging
from contextlib import asynccontextmanager

### basic logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

### constants for api
MARLINS_TEAM_ID = 146
MLB_API_BASE_URL = "https://statsapi.mlb.com/api/v1"

### cache for team IDs, with Marlins as default
TEAM_IDS_CACHE = [str(MARLINS_TEAM_ID)]


### fetches the current affiliate team IDs for the Marlins
async def fetch_affiliate_ids() -> list:

    url = f"{MLB_API_BASE_URL}/teams/affiliates"
    params = {
        "teamIds": MARLINS_TEAM_ID,
        "year": date.today().year
    }
    
    affiliate_ids = []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            teams = data.get("teams", []) # get the teams ids
            for team in teams:
                team_id = team.get("id")

                if team_id and team_id != MARLINS_TEAM_ID:
                    affiliate_ids.append(str(team_id)) # add affiliates to Marlins from cache
                    
            logger.info(f"Successfully loaded {len(affiliate_ids)} affiliate IDs")
            return affiliate_ids
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch affiliates from Stats API: {e}")
            return [] # return empty array upon failure


### gets affiliate_ids on startup and adds to cache
@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("starting up...")
    affiliates = await fetch_affiliate_ids()
    TEAM_IDS_CACHE.extend(affiliates)
    
    yield
    
    logger.info("startup complete...")


app = FastAPI(
    title="Marlins Schedule Service",
    description="Abstraction layer for MLB Stats API to fetch daily affiliate schedules",
    version="1.0.0",
    lifespan=lifespan
)


### quick health check
@app.get("/health")
async def health_check():

    return {"status": "we are good to go", "cached_team_count": len(TEAM_IDS_CACHE)}


### will fetch schedule for Marlins & all of its affiliates
### if no date provided, use today's YYYY-MM-DD as default
### returns target_date and teams to query
@app.get("/schedule")
async def get_schedule(target_date: date = None):

    if not target_date:
        target_date = date.today()
        
    return {
        "target_date": target_date,
        "team_ids_to_query": TEAM_IDS_CACHE
    }
