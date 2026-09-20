from pathlib import Path
import asyncio
import concurrent.futures
import logging
from contextlib import asynccontextmanager
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field

from backend import close_resources, run_travel_agent, resume_travel_agent


BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    _executor.shutdown(wait=False, cancel_futures=True)
    close_resources()

app = FastAPI(
    title="TripMate AI",
    description="LangGraph Multi-Agent Travel Planner with FastAPI Frontend",
    version="2.0.0",
    lifespan=lifespan,
)


# check_dir=False skips the anyio os.stat() call that breaks
# on Python 3.14 with the current starlette/anyio versions.
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static"), check_dir=False),
    name="static"
)


templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


class TravelRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=4_000)
    thread_id: str | None = Field(default=None, max_length=200)


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    thread_id: str = Field(min_length=1, max_length=200)
    approved: bool
    feedback: str = Field(default="", max_length=4_000)


# Thread pool for running the synchronous LangGraph agent
# without blocking the async event loop.
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def api_response(result: dict) -> dict:
    """Keep both travel endpoints contract-compatible and consistent."""
    fields = (
        "requires_approval", "approval_request", "flight_results",
        "hotel_results", "weather_results", "budget_results", "itinerary",
        "selected_agents", "trip_constraints", "supervisor_reasoning",
        "guardrail_allowed", "guardrail_reason", "approved", "human_feedback",
        "llm_calls",
    )
    return {
        "success": True,
        "thread_id": result["thread_id"],
        "answer": result["answer"],
        **{field: result.get(field) for field in fields},
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.post("/api/travel")
async def travel_planner(request_data: TravelRequest):
    try:
        user_message = request_data.message.strip()

        if not user_message:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Message cannot be empty."
                }
            )

        # Run the synchronous agent in a thread so it doesn't
        # block the event loop, and its own async calls
        # (run_async in backend.py) get a clean thread context.
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: run_travel_agent(
                user_input=user_message,
                thread_id=request_data.thread_id
            )
        )

        return JSONResponse(content=api_response(result))

    except Exception:
        logger.exception("Travel-planning request failed")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Unable to create a travel plan right now. Please try again."
            }
        )


@app.post("/api/travel/approve")
async def approve_itinerary(request_data: ApprovalRequest):
    """Human-in-the-Loop: approve or request changes to the draft itinerary."""
    try:
        if not request_data.thread_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "thread_id is required."
                }
            )

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _executor,
            lambda: resume_travel_agent(
                thread_id=request_data.thread_id,
                approved=request_data.approved,
                feedback=request_data.feedback.strip(),
            )
        )

        return JSONResponse(content=api_response(result))

    except Exception:
        logger.exception("Travel-plan approval failed")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Unable to finalize this travel plan right now. Please try again."
            }
        )


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "AI Travel Planner API is running"
    }


@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8001,
        reload=False
    )
