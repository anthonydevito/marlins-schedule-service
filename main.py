from fastapi import FastAPI
from datetime import date

app = FastAPI(
    title="Marlins Schedule Service",
    description="Abstraction layer for MLB Stats API to fetch daily affiliate schedules",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    ## quick health check
    return {"status": "we are good to go"}


## will fetch schedule for Marlins & all of its affiliates
## if no date provided, use today's YYYY-MM-DD as default
@app.get("/schedule")
async def get_schedule(target_date: date = None):

    if not target_date:
        target_date = date.today()
        
    # TODO: Implement schedule fetching logic
    return {"message": f"Fetching schedule for {target_date}"}
