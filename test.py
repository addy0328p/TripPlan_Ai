# test.py

from backend import run_travel_agent


# ============================================================
# TEST 1: Basic travel query
# ============================================================

user_query = "Plan a 7 days Lucknow trip from Delhi"

result = run_travel_agent(user_query)


# ============================================================
# PRINT FINAL RESPONSE
# ============================================================

print("\n")
print("=" * 80)
print("FINAL TRAVEL RESPONSE")
print("=" * 80)

print(result["answer"])


# ============================================================
# PRINT THREAD ID
# ============================================================

print("\n")
print("=" * 80)
print("THREAD ID")
print("=" * 80)

print(result["thread_id"])


# ============================================================
# PRINT FLIGHT RESULTS
# ============================================================

print("\n")
print("=" * 80)
print("FLIGHT RESULTS")
print("=" * 80)

print(result["flight_results"])


# ============================================================
# PRINT HOTEL RESULTS
# ============================================================

print("\n")
print("=" * 80)
print("HOTEL RESULTS")
print("=" * 80)

print(result["hotel_results"])


# ============================================================
# PRINT ITINERARY
# ============================================================

print("\n")
print("=" * 80)
print("ITINERARY")
print("=" * 80)

print(result["itinerary"])


# ============================================================
# PRINT NUMBER OF CALLS
# ============================================================

print("\n")
print("=" * 80)
print("CALL COUNT")
print("=" * 80)

print(result["llm_calls"])