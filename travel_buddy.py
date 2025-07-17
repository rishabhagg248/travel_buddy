import os
import getpass
import subprocess
import sys
import requests
import json
from datetime import datetime, timedelta
from typing_extensions import Literal
from typing import Dict, List, Any, Optional
import time

# ============ DEPENDENCY INSTALLATION ============

def install_dependencies():
    """Install required packages for the Travel Buddy\u2122"""
    print("Setting up Travel BuddyTM dependencies...")
    
    required_packages = {
        "langchain-openai": "langchain_openai",
        # "langchain-anthropic": "langchain_anthropic",
        "langgraph": "langgraph",
        "requests": "requests",
        "typing-extensions": "typing_extensions"
    }
    
    for package_name, import_name in required_packages.items():
        try:
            # Try to import the package
            __import__(import_name)
            print(f"{package_name} already installed")
        except ImportError:
            # Package not found, install it
            print(f"Installing {package_name}...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package_name
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"{package_name} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {package_name}: {e}")
                print(f"   Please manually run: pip install {package_name}")
    
    print("Dependency setup complete!")

# Install dependencies before importing other modules
install_dependencies()

# ============ API KEY MANAGEMENT ============

def _set_env(var: str):
    if not os.getenv(var):
        os.environ[var] = getpass.getpass(f"Enter {var}: ")

# Set up all required API keys
# _set_env("ANTHROPIC_API_KEY")
_set_env("OPENAI_API_KEY")
_set_env("AMADEUS_API_KEY")
_set_env("AMADEUS_API_SECRET") 
_set_env("BOOKING_API_KEY")
_set_env("TRIPADVISOR_API_KEY")
_set_env("GETYOURGUIDE_API_KEY")

# Import LangChain modules after installation
try:
    from langchain_core.tools import tool
    from langchain_core.messages import AIMessage
    # from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent
    from langgraph.graph import add_messages
    from langgraph.func import entrypoint, task
    from langchain_core.messages import convert_to_messages
    print("LangChain modules imported successfully")
except ImportError as e:
    print(f"Error importing LangChain modules: {e}")
    print("Please ensure all packages are installed correctly.")
    sys.exit(1)

# Initialize the model
model = ChatOpenAI(
    model="gpt-4o-mini",
    timeout=60,
    temperature=0.7
)

# ============ API CLIENT CLASSES ============

class AmadeusAPI:
    def __init__(self):
        self.api_key = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET")
        self.base_url = "https://test.api.amadeus.com/v1"  # Use production URL for live
        self.access_token = None
        self.token_expires = None
    
    def get_access_token(self):
        """Get OAuth2 access token for Amadeus API"""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            self.token_expires = datetime.now() + timedelta(seconds=token_data["expires_in"] - 60)
            
            return self.access_token
        except Exception as e:
            print(f"Error getting Amadeus token: {e}")
            return None
    
    def search_flights(self, origin: str, destination: str, departure_date: str, return_date: Optional[str] = None, adults: int = 1, max_price: Optional[int] = None):
        """Search flights using Amadeus Flight Offers API"""
        token = self.get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {token}"}
        
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination, 
            "departureDate": departure_date,
            "adults": adults,
            "max": 10
        }
        
        if return_date:
            params["returnDate"] = return_date
        if max_price:
            params["maxPrice"] = max_price
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching flights: {e}")
            return None
    
    def search_hotels(self, city_code: str, checkin_date: str, checkout_date: str, adults: int = 1, rooms: int = 1):
        """Search hotels using Amadeus Hotel Search API"""
        token = self.get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}/reference-data/locations/hotels/by-city"
        headers = {"Authorization": f"Bearer {token}"}
        
        params = {
            "cityCode": city_code,
            "radius": 20,
            "radiusUnit": "KM",
            "hotelSource": "ALL"
        }
        
        try:
            # First get hotel list
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            hotels_data = response.json()
            
            # Then get hotel offers for first few hotels
            if "data" in hotels_data:
                hotel_ids = [hotel["hotelId"] for hotel in hotels_data["data"][:20]]
                
                offers_url = f"{self.base_url}/shopping/hotel-offers"
                offers_params = {
                    "hotelIds": ",".join(hotel_ids),
                    "checkInDate": checkin_date,
                    "checkOutDate": checkout_date,
                    "adults": adults,
                    "rooms": rooms
                }
                
                offers_response = requests.get(offers_url, headers=headers, params=offers_params)
                offers_response.raise_for_status()
                return offers_response.json()
            
            return hotels_data
        except Exception as e:
            print(f"Error searching hotels: {e}")
            return None

class BookingAPI:
    def __init__(self):
        self.api_key = os.getenv("BOOKING_API_KEY")
        self.base_url = "https://booking-com.p.rapidapi.com/v1"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
        }
    
    def search_locations(self, query: str):
        """Search for location IDs"""
        url = f"{self.base_url}/hotels/locations"
        params = {"name": query, "locale": "en-gb"}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching locations: {e}")
            return None
    
    def search_hotels(self, dest_id: str, checkin_date: str, checkout_date: str, adults: int = 1, rooms: int = 1):
        """Search hotels using Booking.com API"""
        url = f"{self.base_url}/hotels/search"
        params = {
            "dest_id": dest_id,
            "order_by": "popularity",
            "filter_by_currency": "USD",
            "checkin_date": checkin_date,
            "checkout_date": checkout_date,
            "adults_number": adults,
            "room_number": rooms,
            "page_number": 0,
            "include_adjacency": "true"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching hotels: {e}")
            return None

class TripAdvisorAPI:
    def __init__(self):
        self.api_key = os.getenv("TRIPADVISOR_API_KEY")
        self.base_url = "https://api.content.tripadvisor.com/api/v1"
        self.headers = {"accept": "application/json"}
    
    def search_location(self, query: str):
        """Search for location ID"""
        url = f"{self.base_url}/location/search"
        params = {
            "key": self.api_key,
            "searchQuery": query,
            "language": "en"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching location: {e}")
            return None
    
    def get_attractions(self, location_id: str):
        """Get attractions for a location"""
        url = f"{self.base_url}/location/{location_id}/attractions"
        params = {
            "key": self.api_key,
            "language": "en"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting attractions: {e}")
            return None

class GetYourGuideAPI:
    def __init__(self):
        self.api_key = os.getenv("GETYOURGUIDE_API_KEY")
        self.base_url = "https://api.getyourguide.com/v1"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def search_activities(self, location: str, category: Optional[str] = None):
        """Search activities and tours"""
        url = f"{self.base_url}/activities"
        params = {
            "q": location,
            "limit": 20
        }
        
        if category:
            params["category"] = category
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching activities: {e}")
            return None

# Initialize API clients
amadeus_api = AmadeusAPI()
booking_api = BookingAPI()
tripadvisor_api = TripAdvisorAPI()
getyourguide_api = GetYourGuideAPI()

# ============ ENHANCED TRAVEL SEARCH TOOLS ============

@tool
def search_flights(departure_city: str, destination: str, departure_date: str, return_date: Optional[str] = None, 
                  travelers: int = 1, budget_per_person: float = 1000.0):
    """Search for flights using real flight APIs (Amadeus)."""
    print(f"Searching real flights from {departure_city} to {destination} on {departure_date}")
    
    # Convert city names to airport codes (simplified mapping)
    airport_codes = {
        "new york": "NYC", "paris": "PAR", "london": "LON", "tokyo": "TYO",
        "los angeles": "LAX", "rome": "ROM", "barcelona": "BCN", "madrid": "MAD",
        "amsterdam": "AMS", "berlin": "BER", "sydney": "SYD", "dubai": "DXB"
    }
    
    origin_code = airport_codes.get(departure_city.lower(), "NYC")
    dest_code = airport_codes.get(destination.lower(), "PAR")
    
    # Search flights using Amadeus API
    flight_data = amadeus_api.search_flights(
        origin=origin_code,
        destination=dest_code,
        departure_date=departure_date,
        return_date=return_date,
        adults=travelers,
        max_price=int(budget_per_person)
    )
    
    formatted_flights = []
    
    if flight_data and "data" in flight_data:
        for offer in flight_data["data"][:5]:  # Limit to top 5 results
            try:
                price = float(offer["price"]["total"])
                
                # Get flight details from first itinerary
                itinerary = offer["itineraries"][0]
                segments = itinerary["segments"]
                
                departure_time = segments[0]["departure"]["at"]
                arrival_time = segments[-1]["arrival"]["at"]
                duration = itinerary["duration"]
                stops = len(segments) - 1
                
                # Get airline code
                airline_code = segments[0]["carrierCode"]
                
                formatted_flights.append({
                    "airline": f"{airline_code} Airlines",
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "price": price,
                    "duration": duration,
                    "stops": stops,
                    "rating": 4.0 + (5 - stops) * 0.2,  # Simple rating based on stops
                    "booking_token": offer.get("id", "")
                })
            except (KeyError, ValueError) as e:
                print(f"Error parsing flight offer: {e}")
                continue
    
    # Fallback to mock data if API fails
    if not formatted_flights:
        print("Using mock flight data (API unavailable)")
        formatted_flights = [
            {
                "airline": "Delta Airlines",
                "departure_time": f"{departure_date}T08:00:00",
                "arrival_time": f"{departure_date}T16:30:00",
                "price": 450.0,
                "duration": "PT8H30M",
                "stops": 1,
                "rating": 4.2,
                "booking_token": "mock_token_1"
            },
            {
                "airline": "American Airlines", 
                "departure_time": f"{departure_date}T10:00:00",
                "arrival_time": f"{departure_date}T17:45:00",
                "price": 520.0,
                "duration": "PT7H45M",
                "stops": 0,
                "rating": 4.5,
                "booking_token": "mock_token_2"
            }
        ]
    
    # Filter by budget
    affordable_flights = [f for f in formatted_flights if f["price"] <= budget_per_person]
    
    return {
        "flights": affordable_flights[:3],
        "search_params": {
            "departure_city": departure_city,
            "destination": destination,
            "departure_date": departure_date,
            "travelers": travelers
        }
    }

@tool
def search_hotels(destination: str, checkin_date: str, checkout_date: str, 
                 budget_per_night: float, travelers: int = 1, accommodation_type: str = "hotel"):
    """Search for hotels using real hotel APIs (Amadeus + Booking.com)."""
    print(f"Searching real hotels in {destination} from {checkin_date} to {checkout_date}")
    
    # Calculate nights
    checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
    checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
    nights = (checkout - checkin).days
    
    formatted_hotels = []
    
    # Try Booking.com API first
    location_data = booking_api.search_locations(destination)
    if location_data and len(location_data) > 0:
        dest_id = location_data[0].get("dest_id")
        if dest_id:
            hotel_data = booking_api.search_hotels(
                dest_id=str(dest_id),
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                adults=travelers
            )
            
            if hotel_data and "result" in hotel_data:
                for hotel in hotel_data["result"][:10]:  # Limit to top 10
                    try:
                        price_per_night = float(hotel.get("min_total_price", 0)) / nights
                        
                        if price_per_night <= budget_per_night:
                            formatted_hotels.append({
                                "name": hotel.get("hotel_name", "Unknown Hotel"),
                                "rating": float(hotel.get("review_score", 3.0)),
                                "price_per_night": price_per_night,
                                "total_cost": price_per_night * nights,
                                "location": hotel.get("district", "City Center"),
                                "amenities": hotel.get("hotel_facilities", ["WiFi"]),
                                "category": "luxury" if price_per_night > 200 else ("mid-range" if price_per_night > 100 else "budget"),
                                "booking_url": hotel.get("url", ""),
                                "hotel_id": hotel.get("hotel_id", "")
                            })
                    except (KeyError, ValueError, TypeError) as e:
                        print(f"Error parsing hotel data: {e}")
                        continue
    
    # Try Amadeus API as backup
    if not formatted_hotels:
        city_codes = {"paris": "PAR", "london": "LON", "new york": "NYC", "tokyo": "TYO"}
        city_code = city_codes.get(destination.lower(), "PAR")
        
        hotel_data = amadeus_api.search_hotels(
            city_code=city_code,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            adults=travelers
        )
        
        if hotel_data and "data" in hotel_data:
            for hotel_offer in hotel_data["data"][:5]:
                try:
                    hotel_info = hotel_offer.get("hotel", {})
                    offers = hotel_offer.get("offers", [])
                    
                    if offers:
                        price_info = offers[0].get("price", {})
                        total_price = float(price_info.get("total", 0))
                        price_per_night = total_price / nights
                        
                        if price_per_night <= budget_per_night:
                            formatted_hotels.append({
                                "name": hotel_info.get("name", "Unknown Hotel"),
                                "rating": float(hotel_info.get("rating", 3.5)),
                                "price_per_night": price_per_night,
                                "total_cost": total_price,
                                "location": hotel_info.get("address", {}).get("cityName", "City Center"),
                                "amenities": hotel_info.get("amenities", ["WiFi"]),
                                "category": "luxury" if price_per_night > 200 else ("mid-range" if price_per_night > 100 else "budget"),
                                "booking_url": "",
                                "hotel_id": hotel_info.get("hotelId", "")
                            })
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Error parsing Amadeus hotel data: {e}")
                    continue
    
    # Fallback to mock data if APIs fail
    if not formatted_hotels:
        print("Using mock hotel data (APIs unavailable)")
        formatted_hotels = [
            {
                "name": "Grand Plaza Hotel",
                "rating": 4.5,
                "price_per_night": 150.0,
                "total_cost": 150.0 * nights,
                "location": "City Center",
                "amenities": ["WiFi", "Pool", "Gym", "Restaurant"],
                "category": "mid-range",
                "booking_url": "",
                "hotel_id": "mock_hotel_1"
            },
            {
                "name": "Budget Inn",
                "rating": 3.2,
                "price_per_night": 80.0,
                "total_cost": 80.0 * nights,
                "location": "Downtown",
                "amenities": ["WiFi", "Parking"],
                "category": "budget",
                "booking_url": "",
                "hotel_id": "mock_hotel_2"
            }
        ]
    
    return {
        "hotels": formatted_hotels[:5],
        "nights": nights,
        "search_params": {
            "destination": destination,
            "checkin_date": checkin_date,
            "checkout_date": checkout_date,
            "budget_per_night": budget_per_night
        }
    }

@tool
def recommend_activities(destination: str, activity_preferences: List[str], 
                        daily_activity_budget: float, trip_duration_days: int):
    """Recommend activities using real activity APIs (TripAdvisor + GetYourGuide)."""
    print(f"Searching real activities for {destination} with preferences: {activity_preferences}")
    
    formatted_activities = []
    
    # Try TripAdvisor API
    location_data = tripadvisor_api.search_location(destination)
    if location_data and "data" in location_data:
        location_id = location_data["data"][0].get("location_id")
        if location_id:
            attractions_data = tripadvisor_api.get_attractions(location_id)
            
            if attractions_data and "data" in attractions_data:
                for attraction in attractions_data["data"][:15]:
                    try:
                        # Map TripAdvisor categories to our preferences
                        ta_category = attraction.get("category", {}).get("name", "").lower()
                        our_category = "culture"  # default
                        
                        if any(pref in ta_category for pref in ["museum", "historic", "cultural"]):
                            our_category = "culture"
                        elif any(pref in ta_category for pref in ["food", "restaurant", "culinary"]):
                            our_category = "food"
                        elif any(pref in ta_category for pref in ["adventure", "outdoor", "sports"]):
                            our_category = "adventure"
                        elif any(pref in ta_category for pref in ["spa", "beach", "relaxation"]):
                            our_category = "relaxation"
                        
                        if our_category in activity_preferences:
                            # Estimate price based on category
                            price_estimates = {
                                "culture": 25.0,
                                "food": 45.0, 
                                "adventure": 65.0,
                                "relaxation": 35.0
                            }
                            
                            estimated_price = price_estimates.get(our_category, 30.0)
                            
                            if estimated_price <= daily_activity_budget:
                                formatted_activities.append({
                                    "name": attraction.get("name", "Unknown Activity"),
                                    "description": attraction.get("description", "No description available")[:200],
                                    "category": our_category,
                                    "duration": "2-3 hours",
                                    "price": estimated_price,
                                    "rating": float(attraction.get("rating", 4.0)),
                                    "location": attraction.get("address_obj", {}).get("address_string", "Unknown"),
                                    "website": attraction.get("website", ""),
                                    "activity_id": attraction.get("location_id", "")
                                })
                    except (KeyError, ValueError, TypeError) as e:
                        print(f"Error parsing TripAdvisor activity: {e}")
                        continue
    
    # Try GetYourGuide API as backup
    for preference in activity_preferences[:2]:  # Limit API calls
        activity_data = getyourguide_api.search_activities(destination, preference)
        
        if activity_data and "data" in activity_data:
            for activity in activity_data["data"][:5]:
                try:
                    price = float(activity.get("price", {}).get("amount", 50.0))
                    
                    if price <= daily_activity_budget:
                        formatted_activities.append({
                            "name": activity.get("title", "Unknown Activity"),
                            "description": activity.get("description", "No description available")[:200],
                            "category": preference,
                            "duration": activity.get("duration", "3 hours"),
                            "price": price,
                            "rating": float(activity.get("rating", 4.0)),
                            "location": activity.get("location", "Unknown"),
                            "website": activity.get("booking_url", ""),
                            "activity_id": activity.get("id", "")
                        })
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Error parsing GetYourGuide activity: {e}")
                    continue
    
    # Fallback to mock data if APIs fail
    if not formatted_activities:
        print("Using mock activity data (APIs unavailable)")
        mock_activities = [
            {
                "name": "City Walking Tour",
                "description": "Explore the historic downtown area with a local guide",
                "category": "culture",
                "duration": "3 hours",
                "price": 25.0,
                "rating": 4.3,
                "location": "Downtown",
                "website": "",
                "activity_id": "mock_activity_1"
            },
            {
                "name": "Food Market Tour",
                "description": "Taste local specialties at the famous central market",
                "category": "food",
                "duration": "2.5 hours",
                "price": 35.0,
                "rating": 4.8,
                "location": "Central Market",
                "website": "",
                "activity_id": "mock_activity_2"
            }
        ]
        
        # Filter mock activities by preferences
        formatted_activities = [a for a in mock_activities if a["category"] in activity_preferences]
    
    # Remove duplicates and sort by rating
    unique_activities = []
    seen_names = set()
    
    for activity in sorted(formatted_activities, key=lambda x: x["rating"], reverse=True):
        if activity["name"] not in seen_names:
            unique_activities.append(activity)
            seen_names.add(activity["name"])
    
    return {"activities": unique_activities[:trip_duration_days]}

@tool
def get_destination_info(destination: str):
    """Get general information about a destination including weather, currency, etc."""
    print(f"Getting destination info for {destination}")
    
    # This would integrate with APIs like Amadeus, TripAdvisor, GetYourGuide, etc.
    # For now, providing structured mock data
    
    destination_data = {
        "paris": {
            "country": "France",
            "currency": "EUR",
            "language": "French",
            "timezone": "CET",
            "best_time_to_visit": "April-June, September-October",
            "average_temperature": "15°C (59°F)",
            "popular_districts": ["Marais", "Saint-Germain", "Montmartre", "Champs-Élysées"],
            "transportation": ["Metro", "Bus", "Taxi", "Walking"],
            "emergency_number": "112"
        },
        "london": {
            "country": "United Kingdom",
            "currency": "GBP",
            "language": "English", 
            "timezone": "GMT",
            "best_time_to_visit": "May-September",
            "average_temperature": "12°C (54°F)",
            "popular_districts": ["Westminster", "Camden", "Shoreditch", "Covent Garden"],
            "transportation": ["Underground", "Bus", "Taxi", "Walking"],
            "emergency_number": "999"
        }
    }
    
    info = destination_data.get(destination.lower(), {
        "country": "Unknown",
        "currency": "USD",
        "language": "Local Language",
        "timezone": "Local Time",
        "best_time_to_visit": "Year-round",
        "average_temperature": "Variable",
        "popular_districts": ["City Center"],
        "transportation": ["Public Transport", "Taxi"],
        "emergency_number": "Emergency Services"
    })
    
    return {"destination_info": info}

# ============ BUDGET OPTIMIZATION TOOLS ============

@tool
def optimize_travel_budget(total_budget: float, travelers: int, trip_duration_days: int, 
                          flights: List[Dict], hotels: List[Dict], activities: List[Dict],
                          budget_priority: Literal["economy", "balanced", "luxury"] = "balanced"):
    """Optimize travel selections based on budget constraints and priorities using real pricing data."""
    print(f"Optimizing budget of ${total_budget} for {travelers} travelers, {trip_duration_days} days")
    
    # Budget allocation strategy
    flight_budget_ratio = 0.35
    hotel_budget_ratio = 0.45  
    activity_budget_ratio = 0.20
    
    per_person_budget = total_budget / travelers
    flight_budget = per_person_budget * flight_budget_ratio
    hotel_budget = per_person_budget * hotel_budget_ratio
    activity_budget = per_person_budget * activity_budget_ratio
    
    # Select optimal flight
    affordable_flights = [f for f in flights if f["price"] <= flight_budget]
    if not affordable_flights:
        affordable_flights = flights  # Fallback to all options
    
    if budget_priority == "economy":
        selected_flight = min(affordable_flights, key=lambda f: f["price"])
    elif budget_priority == "luxury":
        selected_flight = max(affordable_flights, key=lambda f: f.get("rating", 3.0))
    else:  # balanced
        # Score based on price/rating ratio
        for flight in affordable_flights:
            rating = flight.get("rating", 3.0)
            price_score = (flight_budget - flight["price"]) / flight_budget  # Higher is better
            flight["value_score"] = (rating / 5.0) * 0.6 + price_score * 0.4
        selected_flight = max(affordable_flights, key=lambda f: f.get("value_score", 0))
    
    # Select optimal hotel
    remaining_budget = per_person_budget - selected_flight["price"]
    hotel_budget_adjusted = min(hotel_budget, remaining_budget * 0.6)
    
    affordable_hotels = [h for h in hotels if h["price_per_night"] <= hotel_budget_adjusted]
    if not affordable_hotels:
        affordable_hotels = hotels
    
    if budget_priority == "economy":
        selected_hotel = min(affordable_hotels, key=lambda h: h["price_per_night"])
    elif budget_priority == "luxury":
        selected_hotel = max(affordable_hotels, key=lambda h: h.get("rating", 3.0))
    else:  # balanced
        for hotel in affordable_hotels:
            rating = hotel.get("rating", 3.0)
            price_score = (hotel_budget_adjusted - hotel["price_per_night"]) / hotel_budget_adjusted
            hotel["value_score"] = (rating / 5.0) * 0.6 + price_score * 0.4
        selected_hotel = max(affordable_hotels, key=lambda h: h.get("value_score", 0))
    
    # Select activities within remaining budget
    total_cost = selected_flight["price"] + selected_hotel["total_cost"]
    remaining_for_activities = per_person_budget - total_cost
    daily_activity_budget = remaining_for_activities / trip_duration_days
    
    selected_activities = []
    current_activity_cost = 0
    for activity in sorted(activities, key=lambda a: a.get("rating", 3.0), reverse=True):
        if current_activity_cost + activity["price"] <= remaining_for_activities:
            selected_activities.append(activity)
            current_activity_cost += activity["price"]
    
    total_trip_cost = total_cost + current_activity_cost
    budget_remaining = per_person_budget - total_trip_cost
    
    # Generate detailed recommendations
    recommendations = []
    if budget_remaining < 0:
        recommendations.append("Budget exceeded - consider these options:")
        recommendations.append(f"• Switch to economy flight (save ${selected_flight['price'] - min(flights, key=lambda f: f['price'])['price']:.2f})")
        recommendations.append(f"• Choose budget hotel (save ${selected_hotel['price_per_night'] - min(hotels, key=lambda h: h['price_per_night'])['price_per_night']:.2f}/night)")
        recommendations.append("• Reduce number of paid activities")
    else:
        recommendations.append(f"Great! You have ${budget_remaining:.2f} remaining")
        recommendations.append("• Consider upgrading accommodation")
        recommendations.append("• Add more premium activities")
        recommendations.append("• Set aside for meals and shopping")
    
    optimization_result = {
        "selected_flight": selected_flight,
        "selected_hotel": selected_hotel, 
        "selected_activities": selected_activities,
        "total_cost": total_trip_cost,
        "budget_remaining": budget_remaining,
        "cost_breakdown": {
            "flight": selected_flight["price"],
            "hotel": selected_hotel["total_cost"],
            "activities": current_activity_cost,
            "meals_misc": budget_remaining * 0.5 if budget_remaining > 0 else 0
        },
        "budget_status": "within_budget" if budget_remaining >= 0 else "over_budget",
        "recommendations": recommendations,
        "savings_opportunities": {
            "flight_savings": selected_flight["price"] - min(flights, key=lambda f: f["price"])["price"],
            "hotel_savings": selected_hotel["price_per_night"] - min(hotels, key=lambda h: h["price_per_night"])["price_per_night"]
        }
    }
    
    return optimization_result

# ============ ITINERARY GENERATION TOOLS ============

@tool
def generate_detailed_itinerary(destination: str, checkin_date: str, checkout_date: str,
                               selected_flight: Dict, selected_hotel: Dict, selected_activities: List[Dict],
                               destination_info: Optional[Dict] = None):
    """Generate a detailed day-by-day itinerary with real booking information."""
    print(f"Generating detailed itinerary for {destination}")
    
    start_date = datetime.strptime(checkin_date, "%Y-%m-%d")
    end_date = datetime.strptime(checkout_date, "%Y-%m-%d")
    trip_duration = (end_date - start_date).days
    
    itinerary = []
    
    # Add destination info to itinerary header
    if destination_info:
        itinerary.append({
            "type": "destination_info",
            "destination": destination,
            "info": destination_info
        })
    
    # Day 1: Arrival
    day_1 = {
        "date": start_date.strftime("%Y-%m-%d"),
        "day_number": 1,
        "title": "Arrival Day",
        "activities": [
            {
                "time": "Morning/Afternoon",
                "activity": f"Flight Arrival - {selected_flight['airline']}",
                "description": f"Arrive at {destination}",
                "cost": selected_flight["price"],
                "duration": selected_flight.get("duration", "8 hours"),
                "booking_info": {
                    "type": "flight",
                    "booking_token": selected_flight.get("booking_token", ""),
                    "confirmation": "Book through airline website"
                }
            },
            {
                "time": "Late Afternoon",
                "activity": f"Hotel Check-in - {selected_hotel['name']}",
                "description": f"Check into {selected_hotel['name']} in {selected_hotel['location']}",
                "cost": 0,
                "duration": "30 minutes",
                "booking_info": {
                    "type": "hotel",
                    "hotel_id": selected_hotel.get("hotel_id", ""),
                    "booking_url": selected_hotel.get("booking_url", ""),
                    "amenities": selected_hotel.get("amenities", [])
                }
            },
            {
                "time": "Evening",
                "activity": "Welcome Dinner",
                "description": "Explore local dining near hotel",
                "cost": 50,
                "duration": "2 hours",
                "booking_info": {
                    "type": "meal",
                    "suggestion": "Ask hotel concierge for recommendations"
                }
            }
        ],
        "daily_total": selected_flight["price"] + 50
    }
    itinerary.append(day_1)
    
    # Middle days: Activities
    activity_index = 0
    for day_num in range(2, trip_duration + 1):
        current_date = start_date + timedelta(days=day_num - 1)
        
        day_activities = [
            {
                "time": "Morning",
                "activity": "Breakfast",
                "description": "Breakfast at hotel or local cafe",
                "cost": 15,
                "duration": "1 hour",
                "booking_info": {
                    "type": "meal",
                    "suggestion": "Hotel breakfast or nearby cafe"
                }
            }
        ]
        
        daily_total = 15
        
        # Add main activity if available
        if activity_index < len(selected_activities):
            activity = selected_activities[activity_index]
            day_activities.append({
                "time": "Mid-Morning to Afternoon",
                "activity": activity["name"],
                "description": activity["description"],
                "cost": activity["price"],
                "duration": activity.get("duration", "3 hours"),
                "booking_info": {
                    "type": "activity",
                    "activity_id": activity.get("activity_id", ""),
                    "website": activity.get("website", ""),
                    "location": activity.get("location", ""),
                    "rating": activity.get("rating", 4.0)
                }
            })
            daily_total += activity["price"]
            activity_index += 1
        else:
            day_activities.append({
                "time": "Morning to Afternoon", 
                "activity": "Free Exploration",
                "description": f"Explore {destination} at your own pace",
                "cost": 30,
                "duration": "4 hours",
                "booking_info": {
                    "type": "free_time",
                    "suggestion": "Visit local markets, parks, or neighborhoods"
                }
            })
            daily_total += 30
        
        day_activities.append({
            "time": "Evening",
            "activity": "Dinner & Leisure",
            "description": "Local dining and evening activities",
            "cost": 60,
            "duration": "2-3 hours",
            "booking_info": {
                "type": "meal",
                "suggestion": "Try local specialties and nightlife"
            }
        })
        daily_total += 60
        
        day_plan = {
            "date": current_date.strftime("%Y-%m-%d"),
            "day_number": day_num,
            "title": f"Day {day_num} - Exploration",
            "activities": day_activities,
            "daily_total": daily_total
        }
        itinerary.append(day_plan)
    
    # Last day: Departure
    departure_day = {
        "date": end_date.strftime("%Y-%m-%d"),
        "day_number": trip_duration + 1,
        "title": "Departure Day",
        "activities": [
            {
                "time": "Morning",
                "activity": "Hotel Check-out",
                "description": "Pack and check out of hotel",
                "cost": 0,
                "duration": "1 hour",
                "booking_info": {
                    "type": "hotel",
                    "note": "Confirm check-out time with hotel"
                }
            },
            {
                "time": "Late Morning/Afternoon",
                "activity": "Departure",
                "description": "Travel to airport and departure",
                "cost": 0,
                "duration": "Variable",
                "booking_info": {
                    "type": "transportation",
                    "suggestion": "Book airport transfer or use public transport"
                }
            }
        ],
        "daily_total": 0
    }
    itinerary.append(departure_day)
    
    # Calculate total itinerary cost
    total_itinerary_cost = sum(day.get("daily_total", 0) for day in itinerary if day.get("type") != "destination_info")
    
    return {
        "itinerary": itinerary, 
        "total_days": len([d for d in itinerary if d.get("type") != "destination_info"]),
        "total_cost": total_itinerary_cost,
        "booking_summary": {
            "flight": {
                "airline": selected_flight["airline"],
                "price": selected_flight["price"],
                "booking_token": selected_flight.get("booking_token", "")
            },
            "hotel": {
                "name": selected_hotel["name"],
                "total_cost": selected_hotel["total_cost"],
                "booking_url": selected_hotel.get("booking_url", "")
            },
            "activities_count": len(selected_activities),
            "activities_cost": sum(a["price"] for a in selected_activities)
        }
    }

# ============ AGENT TRANSFER TOOLS ============

@tool(return_direct=True)
def transfer_to_hotel_search():
    """Transfer to hotel search agent for accommodation recommendations."""
    return "Transferring to Hotel Search Agent for accommodation options..."

@tool(return_direct=True) 
def transfer_to_activity_recommender():
    """Transfer to activity recommender agent for activity suggestions."""
    return "Transferring to Activity Recommender Agent for activity suggestions..."

@tool(return_direct=True)
def transfer_to_budget_optimizer():
    """Transfer to budget optimizer agent for budget optimization."""
    return "Transferring to Budget Optimizer Agent for budget analysis..."

@tool(return_direct=True)
def transfer_to_itinerary_generator():
    """Transfer to itinerary generator agent for detailed itinerary creation."""
    return "Transferring to Itinerary Generator Agent for detailed planning..."

@tool(return_direct=True)
def transfer_to_flight_search():
    """Transfer to flight search agent for flight options."""
    return "Transferring to Flight Search Agent for flight options..."

# ============ AGENT DEFINITIONS ============

# Flight Search Agent
flight_search_tools = [search_flights, get_destination_info, transfer_to_hotel_search]
flight_search_agent = create_react_agent(
    model,
    flight_search_tools,
    prompt=(
        "You are a flight search specialist with access to real flight APIs (Amadeus). "
        "You help find the best flight options within budget constraints. "
        "Always search for flights first, then get destination information. "
        "After providing flight recommendations and destination info, transfer to hotel search. "
        "Provide detailed flight options with prices, airlines, and booking information."
    ),
)

# Hotel Search Agent  
hotel_search_tools = [search_hotels, transfer_to_activity_recommender]
hotel_search_agent = create_react_agent(
    model,
    hotel_search_tools,
    prompt=(
        "You are a hotel search specialist with access to real hotel APIs (Booking.com, Amadeus). "
        "You find the best accommodation options within budget and preference constraints. "
        "After providing hotel recommendations with real pricing and booking links, transfer to activity recommender. "
        "Include amenities, ratings, and location details for each hotel option."
    ),
)

# Activity Recommender Agent
activity_recommender_tools = [recommend_activities, transfer_to_budget_optimizer]
activity_recommender_agent = create_react_agent(
    model,
    activity_recommender_tools,
    prompt=(
        "You are an activity recommendation specialist with access to real activity APIs (TripAdvisor, GetYourGuide). "
        "You suggest activities based on user preferences using real data from attraction databases. "
        "After providing activity recommendations with real pricing and booking information, transfer to budget optimizer. "
        "Include ratings, descriptions, and website links for each activity."
    ),
)

# Budget Optimizer Agent
budget_optimizer_tools = [optimize_travel_budget, transfer_to_itinerary_generator]
budget_optimizer_agent = create_react_agent(
    model,
    budget_optimizer_tools,
    prompt=(
        "You are a budget optimization specialist that analyzes real pricing data to create optimal travel combinations. "
        "You consider flight prices, hotel costs, and activity fees to maximize value within budget constraints. "
        "After optimizing the budget and providing cost breakdown with savings opportunities, transfer to itinerary generator. "
        "Provide clear budget analysis with recommendations for upgrades or cost savings."
    ),
)

# Itinerary Generator Agent
itinerary_generator_tools = [generate_detailed_itinerary]
itinerary_generator_agent = create_react_agent(
    model,
    itinerary_generator_tools,
    prompt=(
        "You are an itinerary planning specialist that creates detailed day-by-day travel plans with real booking information. "
        "You generate comprehensive itineraries with timing, costs, booking details, and practical travel tips. "
        "Include booking URLs, confirmation numbers, and practical advice for each component. "
        "This is the final step - provide a complete, actionable itinerary with all booking information."
    ),
)

# ============ TASK DEFINITIONS ============

@task
def call_flight_search_agent(messages):
   if not isinstance(messages, list):
       messages = [messages]
   
   response = flight_search_agent.invoke({"messages": messages})
   return response["messages"]

@task  
def call_hotel_search_agent(messages):
   if not isinstance(messages, list):
       messages = [messages]
   
   response = hotel_search_agent.invoke({"messages": messages})
   return response["messages"]

@task
def call_activity_recommender_agent(messages):
   if not isinstance(messages, list):
       messages = [messages]
   
   response = activity_recommender_agent.invoke({"messages": messages})
   return response["messages"]

@task
def call_budget_optimizer_agent(messages):
   if not isinstance(messages, list):
       messages = [messages]
   
   response = budget_optimizer_agent.invoke({"messages": messages})
   return response["messages"]

@task
def call_itinerary_generator_agent(messages):
   if not isinstance(messages, list):
       messages = [messages]
   
   response = itinerary_generator_agent.invoke({"messages": messages})
   return response["messages"]

# ============ MAIN WORKFLOW ============

@entrypoint()
def travel_planner_workflow(messages):
   current_messages = list(messages)
   
   agent_sequence = [
       call_flight_search_agent,
       call_hotel_search_agent,
       call_activity_recommender_agent,
       call_budget_optimizer_agent,
       call_itinerary_generator_agent
   ]
   
   for agent_func in agent_sequence:
       try:
           print(f"Running {agent_func.__name__}...")
           
           agent_result = agent_func(current_messages).result()
           
           if isinstance(agent_result, list):
               current_messages.extend(agent_result)
           else:
               current_messages.append(agent_result)
               
       except Exception as e:
           print(f"Error in {agent_func.__name__}: {e}")
           continue
   
   return current_messages

# ============ UTILITY FUNCTIONS ============

def pretty_print_messages(update):
   if isinstance(update, tuple):
       ns, update = update
       if len(ns) == 0:
           return
       
       graph_id = ns[-1].split(":")[0]
       print(f"Update from subgraph {graph_id}:")
       print()
   
   for node_name, node_update in update.items():
       print(f"Update from node {node_name}:")
       print()
       
       for m in convert_to_messages(node_update["messages"]):
           m.pretty_print()
       print()

# ============ MAIN EXECUTION ============

if __name__ == "__main__":
   print("\nWelcome to Travel Buddy\u2122!")
   print("=" * 50)
   
   print("Let's plan your trip!")
   destination = input("Where would you like to travel? ").strip()
   departure_city = input("Where are you departing from? ").strip()
   departure_date = input("Departure date (YYYY-MM-DD): ").strip()
   return_date = input("Return date (YYYY-MM-DD, or press Enter for one-way): ").strip()
   budget = float(input("Total budget per person ($): ").strip())
   travelers = int(input("Number of travelers: ").strip())
   
   if not return_date:
       return_date = "One-way"
   
   user_message_content = f"""
I want to plan a trip to {destination} from {departure_city}.
Departure: {departure_date}
Return: {return_date}
Budget: ${budget} per person
Travelers: {travelers}

Please help me find flights, hotels, activities, optimize my budget, and create a detailed itinerary.
I'm interested in culture, food, and some adventure activities.
   """.strip()
   
   print(f"\nPlanning your trip to {destination}...")
   print("This may take a few moments as we search multiple APIs...\n")
   
   try:
       from langchain_core.messages import HumanMessage
       
       human_message = HumanMessage(content=user_message_content)
       
       print("Starting travel planning...")
       
       result_messages = travel_planner_workflow([human_message])
       
       print("\nTrip planning complete!")
       print("=" * 70)
       
       for i, msg in enumerate(result_messages):
           if hasattr(msg, 'content') and msg.content and msg.content.strip():
               print(f"\nStep {i+1}:")
               print(msg.content)
               print("-" * 70)
               
   except Exception as e:
       print(f"\nError planning trip: {e}")
       import traceback
       traceback.print_exc()
       print("\nMake sure your API keys are correct and you have internet connection.")