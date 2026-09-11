# ============================================================
# IMPORTS
# ============================================================

# Path provides an object-oriented way to handle filesystem
# paths. It works correctly on all platforms (Windows, Mac,
# Linux) without needing to manually join strings with slashes.
from pathlib import Path

# traceback lets us print the full error call stack to the
# console when an exception occurs. This makes debugging much
# easier than just printing the error message alone.
import traceback

# uvicorn is the ASGI server that actually runs FastAPI.
# ASGI (Asynchronous Server Gateway Interface) is the
# modern async alternative to WSGI (used by Flask/Django).
import uvicorn

# FastAPI is the main web framework.
# Request represents an incoming HTTP request and is needed
# when rendering HTML templates so Jinja2 can access request
# metadata (like headers, URL, etc.).
from fastapi import FastAPI, Request

# HTMLResponse tells FastAPI to return the response with
# Content-Type: text/html instead of application/json.
#
# JSONResponse lets us manually construct a JSON response
# and control the HTTP status code (e.g. 400, 500).
from fastapi.responses import HTMLResponse, JSONResponse

# StaticFiles allows FastAPI to serve files from a directory
# directly over HTTP without any Python code involved.
# Used for serving CSS, JavaScript, and image files.
from fastapi.staticfiles import StaticFiles

# Jinja2Templates is an HTML templating engine.
# It allows us to render .html files and inject Python
# variables into them using {{ variable }} syntax.
from fastapi.templating import Jinja2Templates

# BaseModel from pydantic is used to define the expected
# shape and types of incoming JSON request bodies.
# FastAPI uses it to automatically validate requests and
# return a 422 Unprocessable Entity error if data is wrong.
from pydantic import BaseModel

# This imports the main function from our backend module.
# run_travel_agent() triggers the entire LangGraph pipeline:
# flight search → hotel search → itinerary generation.
from backend import run_travel_agent


# ============================================================
# BASE DIRECTORY
# ============================================================

# __file__ is a Python built-in that holds the path to the
# current file (app.py).
#
# .resolve() converts it to an absolute path, removing any
# relative path components (e.g. ../app.py -> C:/project/app.py).
#
# .parent goes one level up to get the folder that contains
# app.py — i.e. the project root directory.
#
# We use BASE_DIR to build paths to static/ and templates/
# in a way that works regardless of which directory you run
# the server from.
BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# CREATE FASTAPI APPLICATION INSTANCE
# ============================================================

# FastAPI() creates the main application object.
# All routes, middleware, and configuration are attached here.
#
# title, description, and version appear in the auto-generated
# interactive API docs at http://localhost:8000/docs
app = FastAPI(
    title="TripMate AI",
    description="LangGraph Multi-Agent Travel Planner with FastAPI Frontend",
    version="1.0.0"
)


# ============================================================
# MOUNT STATIC FILES
# ============================================================

# app.mount() registers a sub-application that handles all
# requests matching a given URL prefix.
#
# Here, any request to /static/... is handled by StaticFiles,
# which simply reads and returns the file from the disk.
#
# Example:
#   Request: GET /static/style.css
#   FastAPI reads: BASE_DIR/static/style.css
#   Returns:       the CSS file content
#
# name="static" allows you to reference this mount by name
# inside Jinja2 templates using url_for("static", path="...").
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


# ============================================================
# CONFIGURE JINJA2 TEMPLATES
# ============================================================

# Jinja2Templates points to the folder containing .html files.
#
# When we call templates.TemplateResponse("index.html", ...),
# Jinja2 looks for the file at BASE_DIR/templates/index.html.
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


# ============================================================
# REQUEST BODY MODEL
# ============================================================

# TravelRequest defines the structure of the JSON body that
# the frontend must send when calling POST /api/travel.
#
# Pydantic automatically:
#   - Validates that "message" is a non-null string
#   - Validates that "thread_id" is a string or null
#   - Returns HTTP 422 with error details if validation fails
#
# Example valid request body:
# {
#     "message": "Plan a 7 day Japan trip",
#     "thread_id": "user_abc123"   <- optional
# }
class TravelRequest(BaseModel):

    # The user's travel query. Required field.
    message: str

    # Optional conversation thread ID.
    # If provided, the LangGraph state for this thread is
    # resumed from PostgreSQL (continuing the conversation).
    # If None, the backend generates a new thread ID.
    thread_id: str | None = None


# ============================================================
# ROUTE: GET /
# Home page — serves the HTML frontend
# ============================================================

# response_class=HTMLResponse tells FastAPI that this route
# returns HTML, not JSON. This also sets the correct
# Content-Type header on the response.
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # TemplateResponse renders the Jinja2 template and returns
    # it as an HTML response.
    #
    # request=request is required by Jinja2 in newer FastAPI
    # versions — it gives the template access to URL helpers.
    #
    # name="index.html" is the template file to render
    # (looked up inside BASE_DIR/templates/).
    #
    # context={} passes variables to the template. Empty here
    # because index.html doesn't need any server-side data —
    # all dynamic content is loaded via JavaScript fetch calls.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# ============================================================
# ROUTE: POST /api/travel
# Main AI travel planning endpoint
# ============================================================

@app.post("/api/travel")
async def travel_planner(request_data: TravelRequest):
    # FastAPI automatically deserializes the incoming JSON
    # body into a TravelRequest object. If the body is
    # malformed or missing required fields, FastAPI returns
    # a 422 error before this function is even called.

    try:
        # Strip leading/trailing whitespace from the message.
        # This prevents empty-looking inputs like "   " from
        # passing through.
        user_message = request_data.message.strip()

        # ====================================================
        # Input validation: reject empty messages
        # ====================================================

        if not user_message:
            # Return a 400 Bad Request with a structured error.
            # status_code=400 tells the client it sent bad data.
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Message cannot be empty."
                }
            )

        # ====================================================
        # Run the LangGraph multi-agent pipeline
        # ====================================================

        # run_travel_agent() from backend.py:
        #   1. Runs flight_agent  → fetches live flight data
        #   2. Runs hotel_agent   → searches hotels via Tavily
        #   3. Runs itinerary_agent → generates plan with Groq LLM
        #   4. Runs final_agent   → packages the final response
        #
        # thread_id is passed through so PostgreSQL can restore
        # the conversation state for returning users.
        result = run_travel_agent(
            user_input=user_message,
            thread_id=request_data.thread_id
        )

        # ====================================================
        # Return successful response
        # ====================================================

        # JSONResponse with default status 200.
        # The frontend JavaScript reads these fields to render
        # the travel plan in the browser.
        return JSONResponse(
            content={
                # Indicates the request succeeded.
                "success": True,

                # The thread ID (new or existing) for this
                # conversation. The frontend stores this in
                # localStorage to enable follow-up queries.
                "thread_id": result["thread_id"],

                # The final AI-generated travel plan text.
                # This is what gets displayed to the user.
                "answer": result["answer"],

                # Raw text from the AviationStack flight API.
                "flight_results": result["flight_results"],

                # Raw text from the Tavily hotel web search.
                "hotel_results": result["hotel_results"],

                # The day-by-day itinerary generated by the LLM.
                "itinerary": result["itinerary"],

                # Total number of agent/LLM calls made during
                # this pipeline execution.
                "llm_calls": result["llm_calls"],
            }
        )

    except Exception as e:
        # ====================================================
        # Error handling: catch all unexpected exceptions
        # ====================================================

        # Print the exception message to the server console.
        print("ERROR:", e)

        # Print the full stack trace so we can see exactly
        # where in the code the error occurred.
        traceback.print_exc()

        # Return a 500 Internal Server Error response.
        # str(e) converts the exception to a human-readable
        # message that the frontend can display.
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


# ============================================================
# ROUTE: GET /health
# Health check endpoint
# ============================================================

# A simple endpoint that returns 200 OK with a status message.
#
# This is used by:
#   - Deployment platforms (Render, Railway, etc.) to verify
#     the server is alive before routing traffic to it.
#   - Monitoring tools to check uptime.
#   - Developers to quickly confirm the server started correctly.
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "AI Travel Planner API is running"
    }


# ============================================================
# ROUTE: GET /favicon.ico
# Suppress favicon 404 errors
# ============================================================

# Browsers automatically request /favicon.ico when loading a
# page (to show a small icon in the browser tab).
#
# Without this route, FastAPI would return a 404 for every
# page load, polluting the server logs with noise.
#
# We return an empty JSON response instead of a proper icon
# to silently satisfy the browser's request.
@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})


# ============================================================
# DEVELOPMENT SERVER ENTRY POINT
# ============================================================

# This block only executes when you run the file directly:
#
#     python app.py
#
# It does NOT run when FastAPI/uvicorn imports the module
# internally (e.g. uvicorn app:app from the command line).
if __name__ == "__main__":
    uvicorn.run(
        # "app:app" means:
        #   - First "app"  → the Python module name (app.py)
        #   - Second "app" → the FastAPI instance variable name
        "app:app",

        # Only accept connections from localhost.
        # Change to "0.0.0.0" to accept external connections.
        host="127.0.0.1",

        # The port the server listens on.
        # Access via: http://localhost:8000
        port=8000,

        # Auto-restart the server whenever a Python file changes.
        # Useful during development — disable in production.
        reload=True
    )
