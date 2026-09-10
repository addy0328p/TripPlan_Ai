# Import TavilyClient to interact with the Tavily search API
from tavily import TavilyClient

# Import os to access environment variables
import os

# Import load_dotenv to load variables from the .env file
from dotenv import load_dotenv


# Load environment variables from the .env file
# Example:
# TAVILY_API_KEY=your_api_key
load_dotenv()


# Create a Tavily client using the API key
# The API key is read from the TAVILY_API_KEY environment variable
client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


# Function to perform a Tavily web search
def tavily_search(query):

    # Send the search query to Tavily
    # max_results=6 means we want a maximum of 6 search results
    response = client.search(
        query=query,
        max_results=6
    )

    # Create an empty list to store the formatted search results
    results = []

    # Loop through each search result
    # enumerate(..., 1) makes the numbering start from 1
    for i, r in enumerate(response["results"], 1):

        # Get the title of the search result
        # If no title is available, use "Unknown"
        title = r.get("title", "Unknown")

        # Get the URL of the search result
        # If no URL is available, use an empty string
        url = r.get("url", "")

        # Get the content/snippet of the search result
        # strip() removes unnecessary spaces from the beginning and end
        snippet = r.get("content", "").strip()

        # Keep the snippet short to avoid too much text in the output
        # If it is longer than 300 characters, truncate it
        if len(snippet) > 300:

            # Take the first 300 characters and cut at the last
            # complete word instead of cutting a word in the middle
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        # Format the result with:
        # 1. Title
        # 2. URL
        # 3. Short content/snippet
        results.append(
            f"{i}. **{title}**\n   {url}\n   {snippet}"
        )

    # Join all search results into one string
    # "\n\n" adds a blank line between each result
    return "\n\n".join(results)