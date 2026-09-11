# ============================================================
# IMPORTS & ENVIRONMENT SETUP
# ============================================================

import os
import certifi
from dotenv import load_dotenv


# Load variables from the .env file.
#
# Example .env:
#
# GROQ_API_KEY=your_groq_key
# DATABASE_URL=your_postgres_url
#
load_dotenv()


# ============================================================
# SSL CERTIFICATE CONFIGURATION
# ============================================================

# certifi provides trusted SSL certificates.
#
# These environment variables tell Python libraries
# where to find the trusted SSL certificate bundle.
#
# This helps avoid SSL/HTTPS certificate errors while
# connecting to APIs and PostgreSQL.
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


# ============================================================
# TYPING & UTILITY IMPORTS
# ============================================================

from typing import TypedDict, Annotated

# operator.add will be used by LangGraph to combine
# message lists when state is updated.
import operator

# uuid is used to generate a unique thread ID
# when the user does not provide one.
import uuid


# ============================================================
# POSTGRESQL IMPORTS
# ============================================================

import psycopg

# dict_row makes PostgreSQL query results behave like
# Python dictionaries instead of tuples.
#
# Example:
#
# {"id": 1, "name": "Aditya"}
#
from psycopg.rows import dict_row


# ============================================================
# LANGGRAPH IMPORTS
# ============================================================

from langgraph.graph import (
    StateGraph,
    START,
    END
)

# PostgresSaver is used to save LangGraph state
# into PostgreSQL.
#
# This allows the application to maintain conversation
# state using a thread_id.
from langgraph.checkpoint.postgres import PostgresSaver


# ============================================================
# LANGCHAIN MESSAGE IMPORTS
# ============================================================

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)


# ============================================================
# GROQ LLM
# ============================================================

# ChatGroq allows us to use Groq-hosted LLMs through
# LangChain.
from langchain_groq import ChatGroq


# ============================================================
# CUSTOM TOOLS
# ============================================================

# Tavily tool is responsible for web searching.
#
# We use it mainly for hotel information.
from tools.tavily_tool import tavily_search


# Flight tool searches live flight information using
# the AviationStack API.
from tools.flight_tool import search_flights


# ============================================================
# DATABASE URL FUNCTION
# ============================================================

def get_database_url():
    """
    Gets the PostgreSQL database URL from the .env file.

    The DATABASE_URL should contain the Render PostgreSQL
    External Database URL.

    Example:

    DATABASE_URL=postgresql://username:password@host/database
    """

    # Read DATABASE_URL from environment variables.
    database_url = os.getenv("DATABASE_URL")


    # If DATABASE_URL doesn't exist, stop the application
    # and show a useful error message.
    if not database_url:

        raise ValueError(
            "DATABASE_URL is missing. "
            "Please add your Render PostgreSQL External Database URL to .env"
        )


    # Render PostgreSQL requires SSL connection.
    #
    # If sslmode is not already present in the URL,
    # add:
    #
    #     sslmode=require
    #
    if "sslmode=" not in database_url:

        # If URL already contains '?', use '&'.
        #
        # Otherwise use '?'.
        separator = (
            "&"
            if "?" in database_url
            else "?"
        )

        database_url = (
            f"{database_url}"
            f"{separator}sslmode=require"
        )


    # Return the final database URL.
    return database_url

#url=get_database_url()
#print(url)
# ============================================================
# GROQ API KEY
# ============================================================

# Get Groq API key from .env.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# Make sure the API key exists.
#
# Without the key, the LLM cannot be called.
if not GROQ_API_KEY:

    raise ValueError(
        "GROQ_API_KEY is missing. "
        "Please add it to your .env file."
    )


# ============================================================
# LLM CONFIGURATION
# ============================================================

# Create the Groq LLM object.
#
# This object will be used whenever we need the LLM
# to generate text.
#
# Model:
#     llama-3.3-70b-versatile
#
llm = ChatGroq(
   model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY
)


# ============================================================
# TRAVEL AGENT STATE
# ============================================================

class TravelState(TypedDict):
    """
    TravelState represents the shared state of our
    LangGraph workflow.

    Every agent can read information from this state
    and return updates to it.
    """


    # --------------------------------------------------------
    # messages
    # --------------------------------------------------------
    #
    # Stores the conversation messages.
    #
    # Examples:
    #
    # HumanMessage -> user message
    # AIMessage    -> AI response
    # SystemMessage -> system instructions
    #
    # Annotated[..., operator.add] tells LangGraph:
    #
    # "When a node returns new messages, append them
    #  to the existing message list instead of replacing
    #  the complete list."
    #
    messages: Annotated[
        list[AnyMessage],
        operator.add
    ]


    # --------------------------------------------------------
    # user_query
    # --------------------------------------------------------
    #
    # Original query entered by the user.
    #
    # Example:
    #
    # "Plan a 7 day trip to Japan from Delhi"
    #
    user_query: str


    # --------------------------------------------------------
    # flight_results
    # --------------------------------------------------------
    #
    # Stores the result returned by the flight tool.
    #
    flight_results: str


    # --------------------------------------------------------
    # hotel_results
    # --------------------------------------------------------
    #
    # Stores hotel information returned by Tavily.
    #
    hotel_results: str


    # --------------------------------------------------------
    # itinerary
    # --------------------------------------------------------
    #
    # Stores the travel itinerary generated by the LLM.
    #
    itinerary: str


    # --------------------------------------------------------
    # llm_calls
    # --------------------------------------------------------
    #
    # Keeps track of how many agent/LLM calls have happened.
    #
    llm_calls: int


# ============================================================
# FLIGHT AGENT
# ============================================================

def flight_agent(state: TravelState):
    """
    Flight Agent

    Takes the user's travel query and sends it to the
    flight search tool.

    Example:

        User:
        "Plan a trip from Delhi to Japan"

        search_flights(...)
                ↓
        Flight information
    """


    # Get the original user query from the state.
    query = state["user_query"]


    # Call our custom flight tool.
    #
    # This tool internally communicates with AviationStack.
    flight_data = search_flights(query)


    # Return updates to the LangGraph state.
    return {

        # Save flight information.
        "flight_results": flight_data,


        # Add an AI message to indicate that
        # flight information has been fetched.
        "messages": [
            AIMessage(
                content="Flight results fetched."
            )
        ],


        # Increase the call counter by 1.
        #
        # state.get(..., 0) means:
        #
        # if llm_calls exists -> use its value
        # otherwise -> use 0
        #
        "llm_calls": (
            state.get("llm_calls", 0) + 1
        )
    }


# ============================================================
# HOTEL AGENT
# ============================================================

def hotel_agent(state: TravelState):
    """
    Hotel Agent

    Uses Tavily web search to find hotel information
    based on the user's travel query.
    """


    # Create a search query specifically for hotels.
    #
    # Example:
    #
    # User query:
    # "Plan a 7 day Japan trip"
    #
    # Generated search query:
    #
    # "Best hotels for Plan a 7 day Japan trip"
    #
    query = (
        f"Best hotels for "
        f"{state['user_query']}"
    )


    # Search the web using Tavily.
    hotel_results = tavily_search(query)


    # Return the hotel information to the shared state.
    return {

        # Save hotel results.
        "hotel_results": hotel_results,


        # Add a message indicating that
        # hotel information has been fetched.
        "messages": [
            AIMessage(
                content="Hotel information fetched."
            )
        ],


        # Increment the call counter.
        "llm_calls": (
            state.get("llm_calls", 0) + 1
        )
    }


# ============================================================
# ITINERARY AGENT
# ============================================================

def itinerary_agent(state: TravelState):
    """
    Itinerary Agent

    Uses the LLM to create a complete travel itinerary.

    It receives:
        - User query
        - Flight results
        - Hotel results

    and asks the LLM to combine all this information
    into a practical itinerary.
    """


    # Build the prompt that will be sent to the LLM.
    prompt = f"""
Create a complete travel itinerary.

User Query:
{state['user_query']}

Flight Results:
{state['flight_results']}

Hotel Results:
{state['hotel_results']}

Make the itinerary practical, budget-aware, and easy to follow.
"""


    # Call the Groq LLM.
    #
    # We send two messages:
    #
    # 1. SystemMessage
    #       Defines the role of the AI.
    #
    # 2. HumanMessage
    #       Contains the actual task and travel information.
    #
    response = llm.invoke([

        SystemMessage(
            content="You are an expert travel planner."
        ),

        HumanMessage(
            content=prompt
        )
    ])


    # Save the generated itinerary in state.
    return {

        # response.content contains the actual text
        # generated by the LLM.
        "itinerary": response.content,


        # Also store the LLM response as a message.
        "messages": [
            response
        ],


        # Increment the call counter.
        "llm_calls": (
            state.get("llm_calls", 0) + 1
        )
    }


# ============================================================
# FINAL RESPONSE AGENT
# ============================================================

# ============================================================
# FINAL RESPONSE AGENT
# ============================================================

# ============================================================
# FINAL RESPONSE AGENT
# ============================================================

def final_agent(state: TravelState):
    """
    Final Agent

    Returns the itinerary generated by the itinerary agent
    as the final user-facing response.
    """

    return {
        "messages": [
            AIMessage(
                content=state["itinerary"]
            )
        ]
    }

# ============================================================
# BUILD LANGGRAPH
# ============================================================

# Create a LangGraph StateGraph using our TravelState.
#
# This graph will control the flow between different agents.
graph = StateGraph(TravelState)


# ============================================================
# ADD NODES
# ============================================================
#
# Each node represents one step/agent in our workflow.
#
# ============================================================

# Flight search node.
graph.add_node(
    "flight_agent",
    flight_agent
)


# Hotel search node.
graph.add_node(
    "hotel_agent",
    hotel_agent
)


# Itinerary generation node.
graph.add_node(
    "itinerary_agent",
    itinerary_agent
)


# Final response generation node.
graph.add_node(
    "final_agent",
    final_agent
)


# ============================================================
# CONNECT THE NODES
# ============================================================
#
# Our workflow is:
#
# START
#   ↓
# Flight Agent
#   ↓
# Hotel Agent
#   ↓
# Itinerary Agent
#   ↓
# Final Agent
#   ↓
# END
#
# ============================================================

# Start the workflow with Flight Agent.
graph.add_edge(
    START,
    "flight_agent"
)


# After flights are fetched,
# move to Hotel Agent.
graph.add_edge(
    "flight_agent",
    "hotel_agent"
)


# After hotel information is fetched,
# move to Itinerary Agent.
graph.add_edge(
    "hotel_agent",
    "itinerary_agent"
)


# After itinerary is generated,
# move to Final Agent.
graph.add_edge(
    "itinerary_agent",
    "final_agent"
)


# After final response is generated,
# terminate the workflow.
graph.add_edge(
    "final_agent",
    END
)


# ============================================================
# POSTGRESQL CHECKPOINTER
# ============================================================

# Get PostgreSQL connection URL.
DATABASE_URL = get_database_url()


# Create a PostgreSQL connection.
_conn = psycopg.connect(

    # Database URL.
    DATABASE_URL,

    # Automatically commit database transactions.
    autocommit=True,

    # Return database rows as dictionaries.
    row_factory=dict_row
)


# ============================================================
# CREATE POSTGRES CHECKPOINTER
# ============================================================

# PostgresSaver stores LangGraph checkpoints in PostgreSQL.
#
# This allows the graph to maintain state for different
# conversation threads.
checkpointer = PostgresSaver(_conn)


# Create the required checkpoint tables/schema
# in PostgreSQL if they don't already exist.
checkpointer.setup()


# ============================================================
# COMPILE THE GRAPH
# ============================================================

# Compile the graph and attach PostgreSQL checkpointing.
#
# travel_graph is now the executable version of our
# LangGraph workflow.
travel_graph = graph.compile(
    checkpointer=checkpointer
)


# ============================================================
# FUNCTION USED BY FASTAPI
# ============================================================

def run_travel_agent(
    user_input: str,
    thread_id: str | None = None
):
    """
    Main function that can be called from FastAPI.

    Parameters:
        user_input:
            User's travel request.

        thread_id:
            Unique conversation ID.

            If provided, the same conversation/thread
            can continue.

            If not provided, a new ID is generated.

    Returns:
        Dictionary containing:
            - thread_id
            - final answer
            - flight results
            - hotel results
            - itinerary
            - number of calls
    """


    # ========================================================
    # Create thread ID if one wasn't provided.
    # ========================================================

    if not thread_id:

        # uuid.uuid4() creates a random UUID.
        #
        # .hex converts it into a compact string without
        # hyphens.
        #
        # Example:
        #
        # user_7a8c9d....
        #
        thread_id = (
            f"user_{uuid.uuid4().hex}"
        )


    # ========================================================
    # LangGraph configuration
    # ========================================================
    #
    # thread_id is very important for checkpointing.
    #
    # PostgreSQL uses this ID to identify which conversation
    # the state belongs to.
    #
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }


    # ========================================================
    # Run the LangGraph workflow
    # ========================================================

    result = travel_graph.invoke(

        # Initial state of the graph.
        {
            # Store user's message.
            "messages": [
                HumanMessage(
                    content=user_input
                )
            ],


            # Save original user query.
            "user_query": user_input,


            # Initially no flight results.
            "flight_results": "",


            # Initially no hotel results.
            "hotel_results": "",


            # Initially no itinerary.
            "itinerary": "",


            # No agent/LLM calls have happened yet.
            "llm_calls": 0
        },


        # Pass thread configuration so that
        # PostgreSQL checkpointing knows which conversation
        # this execution belongs to.
        config=config
    )


    # ========================================================
    # Get final answer
    # ========================================================
    #
    # Since Final Agent is the last node, its response
    # is the last message in the messages list.
    #
    final_answer = (
        result["messages"][-1].content
    )


    # ========================================================
    # Return API-friendly response
    # ========================================================

    return {

        # Conversation/thread ID.
        #
        # FastAPI can return this to the frontend so that
        # future requests can continue the same conversation.
        "thread_id": thread_id,


        # Final AI-generated travel response.
        "answer": final_answer,


        # Raw flight information.
        "flight_results": result.get(
            "flight_results",
            ""
        ),


        # Raw hotel search results.
        "hotel_results": result.get(
            "hotel_results",
            ""
        ),


        # Generated itinerary.
        "itinerary": result.get(
            "itinerary",
            ""
        ),


        # Number of calls performed by agents.
        "llm_calls": result.get(
            "llm_calls",
            0
        ),
    }