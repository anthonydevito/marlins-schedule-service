# Marlins Schedule Service

A lightweight FastAPI abstraction layer that interfaces with the MLB Stats API to fetch daily schedules for the Miami Marlins and their minor league affiliates.

## Architecture & Optimizations

* **Async:** Built with `FastAPI` and `httpx` to handle non-blocking, async requests.
* **Caching:** To prevent excessive network requests and potential crashing, the service fetches and caches the IDs and maps during startup.
* **Hydrate:** Utilizes the MLB API's `hydrate` parameter to fetch linescores, probable pitchers, and decisions in a single network request rather than querying individual game endpoints.

## Assumptions Made

1.  **JSON Compliance:** The prompt requested a response where the team ID is the key for an object. But the keys have to be strings, so I structured the response as a list of objects containing a `team` (the ID) and `gameInfo` (the nested object).
2.  **Level Mapping:** The `gameType` provided in the base schedule payload returns shortend strings (ex. "R" for Regular Season). To provide the specific league string requested (ex. "Triple-A"), I utilized a manual dictionary mapping based on the `sportId`.

## Prerequisites

* Python 3.9+
* `pip` (Python package installer)

## Local Setup

1. **Clone or extract the repository:**
   ```bash
   cd marlins-schedule-service
   ```

2. **Install the required dependencies:**
  ```bash
  pip install -r requirements.txt
  ```

3. **Run the FastAPI server:**
  ```bash
  uvicorn main:app --reload
  ```

The server will start at http://127.0.0.1:8000. You will see startup logs indicating the affiliate and parent club caches have successfully loaded.


## Endpoints

`GET /schedule`
Fetches the schedule for the Marlins and all affiliates for a given date.

Parameters:

`target_date`: The date to query in `YYYY-MM-DD` format. If left blank, will use today's date.

Example Request:

[http://127.0.0.1:8000/schedule?target_date=2026-04-29](http://127.0.0.1:8000/schedule?target_date=2026-04-29)

`GET /health`
A quick intro health check to confirm service is running and view team counts.