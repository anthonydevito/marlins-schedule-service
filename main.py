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

### cache for team IDs & sport IDs
TEAM_IDS_CACHE = [str(MARLINS_TEAM_ID)] # marlins as default
SPORT_IDS_CACHE = {"1"} # mlb as default

### fetches the current affiliate team IDs & sport IDs for the Marlins
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
                sport_id = team.get("sport", {}).get("id")

                if team_id and team_id != MARLINS_TEAM_ID:
                    affiliate_ids.append(str(team_id)) # add affiliates to Marlins from cache

                if sport_id:
                    SPORT_IDS_CACHE.add(str(sport_id))
                    
            logger.info(f"Successfully loaded {len(affiliate_ids)} affiliate IDs across {len(SPORT_IDS_CACHE)} sport levels")
            return affiliate_ids
            
        except httpx.HTTPError as error:
            logger.error(f"Failed hitting affiliates API: {url} - {error}")
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

    return {
        "status": "we are good to go", 
        "cached_team_count": len(TEAM_IDS_CACHE),
        "cached_sport_count": len(SPORT_IDS_CACHE)
    }

### quick helper to fetch raw schedule from MLB Stats API
async def fetch_raw_schedule(target_date: date) -> dict:

    url = f"{MLB_API_BASE_URL}/schedule"
    params = {
        "sportId": ",".join(SPORT_IDS_CACHE),
        "teamId": ",".join(TEAM_IDS_CACHE),
        "date": target_date.strftime("%Y-%m-%d")
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as error:
            logger.error(f"Failed to fetch schedule data for {target_date}: {error}")
            return {}


### main endpoint
@app.get("/schedule")
async def get_schedule(target_date: date = None):

    if not target_date:
        target_date = date.today()

    raw_schedule_data = await fetch_raw_schedule(target_date)
        
    return raw_schedule_data # will parse later
