# ============================================================
# Flight Search Utility
# ============================================================
# This script:
# 1. Takes a natural-language flight query.
# 2. Detects origin and destination.
# 3. Converts city/country names into IATA airport codes.
# 4. Calls the AviationStack API.
# 5. Returns formatted live flight information.
#
# Example queries:
#   "flights from Delhi to Tokyo"
#   "flights from Mumbai to Dubai"
#   "Japan trip"
#   "flights from India"
#   "all country flight info"
# ============================================================


# -----------------------------
# Import required libraries
# -----------------------------

import os
import re

# certifi provides a trusted collection of SSL certificates.
# It helps HTTPS requests work correctly.
import certifi

# airportsdata contains information about airports,
# including IATA codes, cities and countries.
import airportsdata

# pycountry helps convert country names into country codes.
# Example:
# India -> IN
# Japan -> JP
# United States -> US
import pycountry

# requests is used to make HTTP requests to AviationStack API.
import requests

# dotenv loads environment variables from the .env file.
from dotenv import load_dotenv


# ============================================================
# Load environment variables
# ============================================================

# Reads variables from the .env file.
#
# Example .env:
#
# AVIATIONSTACK_API_KEY=your_api_key
# DEFAULT_ORIGIN_IATA=DEL
#
load_dotenv()


# ============================================================
# SSL Certificate Configuration
# ============================================================

# Tell Python where the trusted SSL certificate bundle is located.
#
# This can prevent SSL certificate errors while making HTTPS
# requests to APIs.
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


# ============================================================
# API Configuration
# ============================================================

# Get AviationStack API key from environment variables.
#
# The API key should NOT be hardcoded in the Python file.
# It should be stored inside the .env file.
API_KEY = os.getenv("AVIATIONSTACK_API_KEY")


# Default origin airport.
#
# If the user only mentions a destination:
#
#     "Plan a Japan trip"
#
# the program assumes that the flight starts from Delhi.
#
# DEL = Indira Gandhi International Airport, Delhi
#
# We can override this using:
#
# DEFAULT_ORIGIN_IATA=BOM
#
# inside the .env file.
DEFAULT_ORIGIN_IATA = os.getenv(
    "DEFAULT_ORIGIN_IATA",
    "DEL"
)


# AviationStack endpoint for flight information.
BASE_URL = "https://api.aviationstack.com/v1/flights"


# ============================================================
# Load Airport Database
# ============================================================

# Load airport information using IATA codes.
#
# AIRPORTS will contain data like:
#
# {
#     "DEL": {
#         "name": "...",
#         "city": "Delhi",
#         "country": "India"
#     }
# }
#
AIRPORTS = airportsdata.load("IATA")


# ============================================================
# Country Aliases
# ============================================================
#
# Users can write the same country in different ways.
#
# Examples:
#   USA
#   U.S.A
#   America
#
# All of them should resolve to:
#   US
#
# The dictionary converts these different names into
# standard ISO 2-letter country codes.
# ============================================================

COUNTRY_ALIASES = {

    # United States
    "usa": "US",
    "u.s.a": "US",
    "u.s.": "US",
    "america": "US",
    "united states": "US",

    # United Kingdom
    "uk": "GB",
    "u.k.": "GB",
    "britain": "GB",
    "england": "GB",

    # United Arab Emirates
    "uae": "AE",
    "dubai": "AE",

    # Asian countries
    "south korea": "KR",
    "korea": "KR",
    "russia": "RU",
    "vietnam": "VN",

    # India
    "india": "IN",

    # Other popular travel destinations
    "japan": "JP",
    "china": "CN",
    "singapore": "SG",
    "malaysia": "MY",
    "thailand": "TH",
    "indonesia": "ID",
    "nepal": "NP",
    "qatar": "QA",
    "saudi arabia": "SA",
    "turkey": "TR",
    "canada": "CA",
    "australia": "AU",
    "germany": "DE",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
}


# ============================================================
# Preferred Main Airport for Each Country
# ============================================================
#
# When the user says:
#
#     "India"
#
# there are many airports in India.
#
# Instead of searching randomly, we choose a major airport.
#
# India -> DEL
# Japan -> NRT
# UAE -> DXB
#
# ============================================================

COUNTRY_MAIN_AIRPORT = {

    # India
    "IN": "DEL",

    # Asia
    "JP": "NRT",
    "CN": "PEK",
    "KR": "ICN",
    "NP": "KTM",
    "SG": "SIN",
    "MY": "KUL",
    "TH": "BKK",
    "ID": "CGK",

    # Middle East
    "AE": "DXB",
    "QA": "DOH",
    "SA": "JED",
    "TR": "IST",

    # Europe
    "GB": "LHR",
    "DE": "FRA",
    "FR": "CDG",
    "IT": "FCO",
    "ES": "MAD",

    # North America
    "US": "JFK",
    "CA": "YYZ",

    # Australia
    "AU": "SYD",
}


# ============================================================
# Major Indian Cities
# ============================================================
#
# This mapping allows users to write city names instead of
# airport codes.
#
# Example:
#
#     Mumbai -> BOM
#     Delhi -> DEL
#     Bangalore -> BLR
#
# ============================================================

INDIA_CITY_MAIN_AIRPORT = {

    "delhi": "DEL",
    "new delhi": "DEL",

    "mumbai": "BOM",

    "bangalore": "BLR",
    "bengaluru": "BLR",

    "hyderabad": "HYD",

    "chennai": "MAA",

    "kolkata": "CCU",

    "pune": "PNQ",

    "ahmedabad": "AMD",

    "jaipur": "JAI",

    "lucknow": "LKO",

    "goa": "GOI",

    "kochi": "COK",

    "coimbatore": "CJB",

    "chandigarh": "IXC",

    "bhubaneswar": "BBI",

    "patna": "PAT",

    "varanasi": "VNS",

    "srinagar": "SXR",

    "amritsar": "ATQ",

    "indore": "IDR",

    "nagpur": "NAG",

    "surat": "STV",

    "ranchi": "IXR",

    "dehradun": "DED",
}


# ============================================================
# Major International Cities
# ============================================================
#
# These are useful when the user searches for international
# destinations.
#
# Example:
#
#     Tokyo -> NRT
#     London -> LHR
#     Dubai -> DXB
#
# ============================================================

CITY_MAIN_AIRPORT = {

    # -------------------------
    # India
    # -------------------------

    **INDIA_CITY_MAIN_AIRPORT,


    # -------------------------
    # Japan
    # -------------------------

    "tokyo": "NRT",
    "osaka": "KIX",
    "kyoto": "KIX",


    # -------------------------
    # USA
    # -------------------------

    "new york": "JFK",
    "los angeles": "LAX",
    "san francisco": "SFO",
    "chicago": "ORD",
    "boston": "BOS",
    "washington": "IAD",


    # -------------------------
    # United Kingdom
    # -------------------------

    "london": "LHR",
    "manchester": "MAN",


    # -------------------------
    # Middle East
    # -------------------------

    "dubai": "DXB",
    "abu dhabi": "AUH",
    "doha": "DOH",
    "riyadh": "RUH",
    "jeddah": "JED",
    "istanbul": "IST",


    # -------------------------
    # Southeast Asia
    # -------------------------

    "singapore": "SIN",
    "kuala lumpur": "KUL",
    "bangkok": "BKK",
    "jakarta": "CGK",


    # -------------------------
    # Australia
    # -------------------------

    "sydney": "SYD",
    "melbourne": "MEL",


    # -------------------------
    # Europe
    # -------------------------

    "paris": "CDG",
    "rome": "FCO",
    "madrid": "MAD",
    "frankfurt": "FRA",
    "berlin": "BER",
}


# ============================================================
# clean_text()
# ============================================================
#
# Cleans user input before processing it.
#
# Example:
#
#     "Plan a 7 Days Japan Trip!"
#
# becomes approximately:
#
#     "japan"
#
# This makes location detection easier.
# ============================================================

def clean_text(text: str) -> str:

    # Convert everything to lowercase.
    text = text.lower().strip()

    # Remove special characters.
    #
    # Example:
    # "Japan!" -> "japan"
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Replace multiple spaces with a single space.
    text = re.sub(r"\s+", " ", text)

    # Words that are not useful for detecting a location.
    stop_words = [
        "flight",
        "flights",
        "ticket",
        "tickets",
        "trip",
        "travel",
        "plan",
        "complete",
        "days",
        "day",
        "including",
        "hotel",
        "hotels",
        "sightseeing",
        "under",
        "budget",
        "info",
        "information"
    ]

    # Remove unnecessary words.
    words = [
        word
        for word in text.split()
        if word not in stop_words
    ]

    return " ".join(words).strip()


# ============================================================
# country_name_to_code()
# ============================================================
#
# Converts a country name into an ISO country code.
#
# Examples:
#
#     India -> IN
#     Japan -> JP
#     Germany -> DE
#
# ============================================================

def country_name_to_code(text: str):

    # Clean the input first.
    text = clean_text(text)

    # Check our custom aliases first.
    if text in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[text]

    # Try pycountry's built-in country lookup.
    try:

        country = pycountry.countries.lookup(text)

        return country.alpha_2

    except LookupError:
        pass


    # Search for a country name inside a longer sentence.
    #
    # Example:
    #
    #     "trip to japan"
    #
    # should still detect:
    #
    #     Japan -> JP
    #
    for country in pycountry.countries:

        country_name = country.name.lower()

        if country_name in text:

            return country.alpha_2


    # Finally check aliases inside longer text.
    for alias, code in COUNTRY_ALIASES.items():

        if alias in text:

            return code


    # Country could not be identified.
    return None


# ============================================================
# airport_country_matches()
# ============================================================
#
# Checks whether an airport belongs to a particular country.
#
# Example:
#
#     DEL belongs to India.
#
# country_code = "IN"
#
# ============================================================

def airport_country_matches(
    airport: dict,
    country_code: str
) -> bool:

    # Get airport's country.
    airport_country = str(
        airport.get("country", "")
    ).upper().strip()


    # Direct country-code comparison.
    if airport_country == country_code:

        return True


    # Sometimes airport data contains country names instead
    # of country codes.
    try:

        country = pycountry.countries.get(
            alpha_2=country_code
        )

        if (
            country
            and airport_country.lower()
            == country.name.lower()
        ):

            return True

    except Exception:

        pass


    return False


# ============================================================
# get_best_airport_for_country()
# ============================================================
#
# Finds the most suitable airport for a country.
#
# Example:
#
#     India -> DEL
#     Japan -> NRT
#
# First we check our preferred airport mapping.
#
# If it doesn't exist, we search the complete airport database.
# ============================================================

def get_best_airport_for_country(country_code: str):

    # Check whether we already have a preferred airport.
    preferred = COUNTRY_MAIN_AIRPORT.get(
        country_code
    )


    # If the preferred airport exists in our airport database,
    # return it immediately.
    if preferred and preferred in AIRPORTS:

        return preferred


    # Store possible airports here.
    candidates = []


    # Search through all airports.
    for iata, airport in AIRPORTS.items():

        # Skip airports without IATA codes.
        if not iata:

            continue


        # Check whether airport belongs to the country.
        if airport_country_matches(
            airport,
            country_code
        ):

            name = str(
                airport.get("name", "")
            ).lower()

            city = str(
                airport.get("city", "")
            ).lower()


            # Score helps us select a good airport.
            score = 0


            # International airports are preferred.
            if "international" in name:

                score += 50


            if "intl" in name:

                score += 40


            # Capital-city airports get extra points.
            if "capital" in name:

                score += 20


            if city:

                score += 5


            candidates.append(
                (score, iata)
            )


    # No airport found.
    if not candidates:

        return None


    # Highest score comes first.
    candidates.sort(reverse=True)

    return candidates[0][1]


# ============================================================
# resolve_location_to_iata()
# ============================================================
#
# Converts:
#
#     Country
#     City
#     Airport name
#     IATA code
#
# into an IATA airport code.
#
# Examples:
#
#     India       -> DEL
#     Japan       -> NRT
#     Delhi       -> DEL
#     Mumbai      -> BOM
#     Tokyo       -> NRT
#     DEL         -> DEL
#
# ============================================================

def resolve_location_to_iata(location: str):

    # If no location was provided, return None.
    if not location:

        return None


    raw_location = location.strip()


    # --------------------------------------------------------
    # Step 1: Check whether input is already an IATA code.
    # --------------------------------------------------------
    #
    # IATA codes contain exactly 3 letters.
    #
    # Example:
    # DEL
    # BOM
    # DXB
    #
    if re.fullmatch(
        r"[A-Za-z]{3}",
        raw_location
    ):

        code = raw_location.upper()


        # Make sure the code exists in our airport database.
        if code in AIRPORTS:

            return code


    # Clean the location.
    location_clean = clean_text(
        raw_location
    )


    if not location_clean:

        return None


    # --------------------------------------------------------
    # Step 2: Check city mapping.
    # --------------------------------------------------------

    if location_clean in CITY_MAIN_AIRPORT:

        return CITY_MAIN_AIRPORT[
            location_clean
        ]


    # --------------------------------------------------------
    # Step 3: Check country.
    # --------------------------------------------------------

    country_code = country_name_to_code(
        location_clean
    )


    if country_code:

        airport = get_best_airport_for_country(
            country_code
        )

        if airport:

            return airport


    # --------------------------------------------------------
    # Step 4: Search airport database for city.
    # --------------------------------------------------------

    city_matches = []


    for iata, airport in AIRPORTS.items():

        city = str(
            airport.get("city", "")
        ).lower().strip()

        name = str(
            airport.get("name", "")
        ).lower().strip()


        score = 0


        # Exact city match gets the highest score.
        if city == location_clean:

            score += 100


        # Partial city match.
        elif location_clean in city:

            score += 70


        # Airport name contains location.
        if location_clean in name:

            score += 50


        # International airports get extra points.
        if "international" in name:

            score += 10


        if score > 0:

            city_matches.append(
                (score, iata)
            )


    # If matching airports were found,
    # return the airport with the highest score.
    if city_matches:

        city_matches.sort(reverse=True)

        return city_matches[0][1]


    # Location couldn't be resolved.
    return None


# ============================================================
# find_location_mentions()
# ============================================================
#
# Finds city/country names mentioned inside a natural-language
# query.
#
# Example:
#
#     "I want to travel from India to Japan"
#
# Returns something like:
#
#     ["india", "japan"]
#
# ============================================================

def find_location_mentions(query: str):

    # Convert query to lowercase.
    q = query.lower()

    mentions = []


    # --------------------------------------------------------
    # Check country aliases.
    # --------------------------------------------------------

    for alias in COUNTRY_ALIASES:

        if re.search(
            rf"\b{re.escape(alias)}\b",
            q
        ):

            mentions.append(alias)


    # --------------------------------------------------------
    # Check all country names from pycountry.
    # --------------------------------------------------------

    for country in pycountry.countries:

        name = country.name.lower()

        # Ignore very short country names.
        if len(name) >= 4:

            if re.search(
                rf"\b{re.escape(name)}\b",
                q
            ):

                mentions.append(name)


    # --------------------------------------------------------
    # Check city names from our city mapping.
    # --------------------------------------------------------

    for city in CITY_MAIN_AIRPORT:

        if re.search(
            rf"\b{re.escape(city)}\b",
            q
        ):

            mentions.append(city)


    # --------------------------------------------------------
    # Remove duplicates.
    # --------------------------------------------------------

    unique_mentions = []

    for item in mentions:

        if item not in unique_mentions:

            unique_mentions.append(item)


    return unique_mentions


# ============================================================
# parse_route()
# ============================================================
#
# Understands the user's query and extracts:
#
#     departure airport
#     arrival airport
#
# Examples:
#
# "DEL to NRT"
#       -> DEL, NRT
#
# "flights from Delhi to Tokyo"
#       -> DEL, NRT
#
# "flights from Mumbai"
#       -> BOM, None
#
# "flights to Dubai"
#       -> None, DXB
#
# "Japan trip"
#       -> DEL, NRT
#
# "all country flight info"
#       -> None, None
#
# ============================================================

def parse_route(query: str):

    q = query.strip()

    q_lower = q.lower()


    # ========================================================
    # Global / all-country query
    # ========================================================
    #
    # If the user asks for all flights globally,
    # don't apply any airport filters.
    #
    # None, None means:
    #
    # departure = any airport
    # arrival   = any airport
    #
    global_keywords = [

        "all country",
        "all countries",
        "global flight",
        "global flights",
        "all flight",
        "all flights",
        "worldwide flight",
        "worldwide flights",
    ]


    if any(
        keyword in q_lower
        for keyword in global_keywords
    ):

        return None, None


    # ========================================================
    # Direct IATA code route
    # ========================================================
    #
    # Example:
    #
    #     "DEL to NRT"
    #
    # finds:
    #
    #     DEL
    #     NRT
    #
    codes = re.findall(
        r"\b[A-Z]{3}\b",
        q
    )


    if len(codes) >= 2:

        dep = codes[0].upper()

        arr = codes[1].upper()

        return dep, arr


    # ========================================================
    # Pattern: "from X to Y"
    # ========================================================
    #
    # Example:
    #
    #     flights from Delhi to Tokyo
    #
    # X = Delhi
    # Y = Tokyo
    #
    match = re.search(
        r"\bfrom\s+(.+?)\s+\bto\s+(.+?)(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
        q_lower,
    )


    if match:

        origin_text = match.group(1)

        dest_text = match.group(2)


        dep_iata = resolve_location_to_iata(
            origin_text
        )

        arr_iata = resolve_location_to_iata(
            dest_text
        )


        return dep_iata, arr_iata


    # ========================================================
    # Pattern: "to Y from X"
    # ========================================================

    match = re.search(
        r"\bto\s+(.+?)\s+\bfrom\s+(.+?)(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
        q_lower,
    )


    if match:

        dest_text = match.group(1)

        origin_text = match.group(2)


        dep_iata = resolve_location_to_iata(
            origin_text
        )

        arr_iata = resolve_location_to_iata(
            dest_text
        )


        return dep_iata, arr_iata


    # ========================================================
    # Pattern: "flights from X"
    # ========================================================

    match = re.search(
        r"\bfrom\s+(.+?)(?:[.!?]|$)",
        q_lower
    )


    if match:

        origin_text = match.group(1)


        dep_iata = resolve_location_to_iata(
            origin_text
        )


        return dep_iata, None


    # ========================================================
    # Pattern: "flights to X"
    # ========================================================

    match = re.search(
        r"\bto\s+(.+?)(?:[.!?]|$)",
        q_lower
    )


    if match:

        dest_text = match.group(1)


        arr_iata = resolve_location_to_iata(
            dest_text
        )


        return None, arr_iata


    # ========================================================
    # Fallback: detect locations anywhere in query
    # ========================================================

    mentions = find_location_mentions(q)


    # If two locations are found,
    # assume first = origin and second = destination.
    if len(mentions) >= 2:

        dep_iata = resolve_location_to_iata(
            mentions[0]
        )

        arr_iata = resolve_location_to_iata(
            mentions[1]
        )


        return dep_iata, arr_iata


    # If only one location is found,
    # assume it is the destination.
    #
    # Origin will be DEFAULT_ORIGIN_IATA.
    #
    # Example:
    #
    #     "Japan trip"
    #
    # becomes:
    #
    #     DEL -> NRT
    #
    if len(mentions) == 1:

        arr_iata = resolve_location_to_iata(
            mentions[0]
        )


        return DEFAULT_ORIGIN_IATA, arr_iata


    # No location found.
    return None, None


# ============================================================
# format_flight()
# ============================================================
#
# Takes one flight object returned by AviationStack
# and converts it into a readable text format.
#
# ============================================================

def format_flight(flight: dict):

    # Airline name.
    airline = (
        flight.get("airline", {}).get("name")
        or "Unknown airline"
    )


    # Flight number.
    flight_number = (
        flight.get("flight", {}).get("iata")
        or "Unknown flight number"
    )


    # Current flight status.
    status = (
        flight.get("flight_status")
        or "Unknown"
    )


    # Get departure information.
    dep = flight.get(
        "departure",
        {}
    ) or {}


    # Get arrival information.
    arr = flight.get(
        "arrival",
        {}
    ) or {}


    # ========================================================
    # Departure details
    # ========================================================

    dep_airport = (
        dep.get("airport")
        or "Unknown departure airport"
    )

    dep_iata = (
        dep.get("iata")
        or "Unknown"
    )

    dep_terminal = (
        dep.get("terminal")
        or "N/A"
    )

    dep_gate = (
        dep.get("gate")
        or "N/A"
    )

    dep_scheduled = (
        dep.get("scheduled")
        or "Unknown"
    )

    dep_delay = dep.get("delay")


    # Convert delay into readable text.
    if dep_delay is not None:

        dep_delay_text = (
            f"{dep_delay} minutes"
        )

    else:

        dep_delay_text = "N/A"


    # ========================================================
    # Arrival details
    # ========================================================

    arr_airport = (
        arr.get("airport")
        or "Unknown arrival airport"
    )

    arr_iata = (
        arr.get("iata")
        or "Unknown"
    )

    arr_terminal = (
        arr.get("terminal")
        or "N/A"
    )

    arr_gate = (
        arr.get("gate")
        or "N/A"
    )

    arr_scheduled = (
        arr.get("scheduled")
        or "Unknown"
    )

    arr_delay = arr.get("delay")


    # Convert arrival delay into readable text.
    if arr_delay is not None:

        arr_delay_text = (
            f"{arr_delay} minutes"
        )

    else:

        arr_delay_text = "N/A"


    # Return formatted flight information.
    return f"""
Airline: {airline}
Flight: {flight_number}
Status: {status}

Departure:
- Airport: {dep_airport}
- IATA: {dep_iata}
- Terminal: {dep_terminal}
- Gate: {dep_gate}
- Scheduled: {dep_scheduled}
- Delay: {dep_delay_text}

Arrival:
- Airport: {arr_airport}
- IATA: {arr_iata}
- Terminal: {arr_terminal}
- Gate: {arr_gate}
- Scheduled: {arr_scheduled}
- Delay: {arr_delay_text}
""".strip()


# ============================================================
# search_flights()
# ============================================================
#
# Main function.
#
# This function:
#
# 1. Checks API key.
# 2. Parses user's query.
# 3. Creates AviationStack request parameters.
# 4. Calls the API.
# 5. Handles errors.
# 6. Formats the returned flights.
#
# ============================================================

def search_flights(
    query: str,
    limit: int = 10
):

    # ========================================================
    # Step 1: Check API key
    # ========================================================

    if not API_KEY:

        return (
            "Flight API error: "
            "AVIATIONSTACK_API_KEY is missing.\n"

            "Please add this in your .env file:\n"

            "AVIATIONSTACK_API_KEY=your_api_key_here"
        )


    # ========================================================
    # Step 2: Extract origin and destination
    # ========================================================

    dep_iata, arr_iata = parse_route(
        query
    )


    # ========================================================
    # Step 3: Create API parameters
    # ========================================================

    params = {

        # Authentication key.
        "access_key": API_KEY,

        # Maximum number of results.
        #
        # AviationStack supports up to 100 here,
        # so we don't allow our function to request more.
        "limit": min(limit, 100),
    }


    # If departure airport was detected,
    # add it to API parameters.
    if dep_iata:

        params["dep_iata"] = dep_iata


    # If arrival airport was detected,
    # add it to API parameters.
    if arr_iata:

        params["arr_iata"] = arr_iata


    # ========================================================
    # Step 4: Call AviationStack API
    # ========================================================

    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )


        # Convert API response from JSON into Python dictionary.
        data = response.json()


    # Handle network/request errors.
    except requests.exceptions.RequestException as e:

        return (
            f"Flight API request failed: {e}"
        )


    # Handle invalid JSON response.
    except ValueError:

        return (
            "Flight API returned invalid JSON."
        )


    # ========================================================
    # Step 5: Check API-level errors
    # ========================================================

    if "error" in data:

        error = data["error"]


        return (
            "Flight API error:\n"

            f"Code: "
            f"{error.get('code', 'Unknown')}\n"

            f"Message: "
            f"{error.get('message', 'Unknown error')}"
        )


    # ========================================================
    # Step 6: Extract flight data
    # ========================================================

    flight_data = data.get(
        "data",
        []
    )


    # ========================================================
    # Step 7: Handle no flight results
    # ========================================================

    if not flight_data:

        route_text = ""


        # Both origin and destination exist.
        if dep_iata and arr_iata:

            route_text = (
                f" for route "
                f"{dep_iata} to {arr_iata}"
            )


        # Only origin exists.
        elif dep_iata:

            route_text = (
                f" from {dep_iata}"
            )


        # Only destination exists.
        elif arr_iata:

            route_text = (
                f" to {arr_iata}"
            )


        return (
            f"No live flight data found"
            f"{route_text}.\n\n"

            "Note: AviationStack provides "
            "live/status flight data, not ticket prices. "

            "For actual fare prices, use a "
            "flight-pricing API such as Amadeus."
        )


    # ========================================================
    # Step 8: Create route description
    # ========================================================

    route_info = "Global live flights"


    # Origin + destination.
    if dep_iata and arr_iata:

        route_info = (
            f"Live flights from "
            f"{dep_iata} to {arr_iata}"
        )


    # Only origin.
    elif dep_iata:

        route_info = (
            f"Live flights from {dep_iata}"
        )


    # Only destination.
    elif arr_iata:

        route_info = (
            f"Live flights to {arr_iata}"
        )


    # ========================================================
    # Step 9: Format each flight
    # ========================================================

    formatted_flights = [

        format_flight(flight)

        for flight in flight_data[:limit]

    ]


    # Combine all formatted flights.
    return (
        f"{route_info}\n\n"
        + "\n\n---\n\n".join(
            formatted_flights
        )
    )


# ============================================================
# Program Entry Point
# ============================================================
#
# This block only runs when this Python file is executed
# directly.
#
# It will NOT run if this file is imported into another file.
#
# ============================================================

if __name__ == "__main__":


    # --------------------------------------------------------
    # Test 1
    # --------------------------------------------------------
    #
    # Since the query contains only Japan,
    # the program assumes:
    #
    # Default origin = Delhi (DEL)
    # Destination    = Japan (NRT)
    #
    print(
        search_flights(
            "Plan a 7 days Japan trip from India"
        )
    )


    # Print a separator between tests.
    print(
        "\n"
        + "=" * 80
        + "\n"
    )


    # --------------------------------------------------------
    # Test 2
    # --------------------------------------------------------
    #
    # This searches globally because
    # "all country flight info" is detected as a
    # global-flight query.
    #
    print(
        search_flights(
            "all country flight info"
        )
    )