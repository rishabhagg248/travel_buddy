import os
import getpass
import subprocess
import sys
import requests
import json
from datetime import datetime, timedelta
from typing_extensions import Literal
from typing import Dict, List, Any, Optional, cast
import time
import re

# ============ DEPENDENCY INSTALLATION ============

def install_dependencies():
    """Install required packages for the Travel Buddy™"""
    print("Setting up Travel Buddy™ dependencies...")
    
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
        if var in ["BOOKING_API_KEY", "TRIPADVISOR_API_KEY", "GETYOURGUIDE_API_KEY"]:
            print(f"\n{var} requires partnership access.")
            print("Enter '0' if you don't have this API key (dummy data will be used)")
            key = getpass.getpass(f"Enter {var} (or '0' for dummy data): ")
        else:
            key = getpass.getpass(f"Enter {var}: ")
        os.environ[var] = key

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
    from langchain_core.messages import AIMessage, HumanMessage
    # from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from typing import TypedDict, Annotated
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
        self.use_dummy_data = (not self.api_key or self.api_key == "0")
        
        if not self.use_dummy_data:
            self.base_url = "https://booking-com.p.rapidapi.com/v1"
            self.headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
            }
    
    def search_locations(self, query: str):
        """Search for location IDs"""
        if self.use_dummy_data:
            return self._get_dummy_locations(query)
        
        url = f"{self.base_url}/hotels/locations"
        params = {"name": query, "locale": "en-gb"}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching locations: {e}")
            return self._get_dummy_locations(query)
    
    def search_hotels(self, dest_id: str, checkin_date: str, checkout_date: str, adults: int = 1, rooms: int = 1):
        """Search hotels using Booking.com API"""
        if self.use_dummy_data:
            return self._get_dummy_hotels(checkin_date, checkout_date)
        
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
            return self._get_dummy_hotels(checkin_date, checkout_date)
    
    def _get_dummy_locations(self, query: str):
        """Return dummy location data"""
        return [{"dest_id": "12345", "label": f"{query}, Country"}]
    
    def _get_dummy_hotels(self, checkin_date: str, checkout_date: str):
        """Return dummy hotel data"""
        checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
        nights = (checkout - checkin).days
        
        return {
            "result": [
                {
                    "hotel_name": "Grand Central Hotel",
                    "review_score": 8.5,
                    "min_total_price": 120 * nights,
                    "district": "City Center",
                    "hotel_facilities": ["WiFi", "Restaurant", "Gym", "Pool"],
                    "url": "https://booking.com/hotel1",
                    "hotel_id": "dummy_hotel_1"
                },
                {
                    "hotel_name": "Luxury Palace Hotel",
                    "review_score": 9.2,
                    "min_total_price": 280 * nights,
                    "district": "Downtown",
                    "hotel_facilities": ["WiFi", "Spa", "Restaurant", "Gym", "Pool", "Concierge"],
                    "url": "https://booking.com/hotel2",
                    "hotel_id": "dummy_hotel_2"
                },
                {
                    "hotel_name": "Budget Comfort Inn",
                    "review_score": 7.8,
                    "min_total_price": 65 * nights,
                    "district": "Suburb",
                    "hotel_facilities": ["WiFi", "Parking"],
                    "url": "https://booking.com/hotel3",
                    "hotel_id": "dummy_hotel_3"
                },
                {
                    "hotel_name": "Boutique Design Hotel",
                    "review_score": 8.9,
                    "min_total_price": 180 * nights,
                    "district": "Arts District",
                    "hotel_facilities": ["WiFi", "Restaurant", "Bar", "Rooftop Terrace"],
                    "url": "https://booking.com/hotel4",
                    "hotel_id": "dummy_hotel_4"
                }
            ]
        }

class TripAdvisorAPI:
    def __init__(self):
        self.api_key = os.getenv("TRIPADVISOR_API_KEY")
        self.use_dummy_data = (not self.api_key or self.api_key == "0")
        
        if not self.use_dummy_data:
            self.base_url = "https://api.content.tripadvisor.com/api/v1"
            self.headers = {"accept": "application/json"}
    
    def search_location(self, query: str):
        """Search for location ID"""
        if self.use_dummy_data:
            return self._get_dummy_location(query)
        
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
            return self._get_dummy_location(query)
    
    def get_attractions(self, location_id: str):
        """Get attractions for a location"""
        if self.use_dummy_data:
            return self._get_dummy_attractions()
        
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
            return self._get_dummy_attractions()
    
    def _get_dummy_location(self, query: str):
        """Return dummy location data"""
        return {
            "data": [{"location_id": "12345"}]
        }
    
    def _get_dummy_attractions(self):
        """Return dummy attractions data"""
        return {
            "data": [
                {
                    "name": "Historic City Museum",
                    "description": "Explore the rich history and culture of the city through fascinating exhibits and artifacts spanning centuries of local heritage.",
                    "category": {"name": "museum"},
                    "rating": 4.3,
                    "address_obj": {"address_string": "123 Main Street, Downtown"},
                    "website": "https://citymuseum.com",
                    "location_id": "attraction_1"
                },
                {
                    "name": "Central Food Market",
                    "description": "Vibrant local market featuring fresh produce, artisanal foods, and traditional culinary specialties from the region.",
                    "category": {"name": "food"},
                    "rating": 4.6,
                    "address_obj": {"address_string": "456 Market Square"},
                    "website": "https://centralmarket.com",
                    "location_id": "attraction_2"
                },
                {
                    "name": "Adventure Park & Trails",
                    "description": "Outdoor adventure destination with hiking trails, zip lines, and climbing walls suitable for all skill levels.",
                    "category": {"name": "outdoor"},
                    "rating": 4.4,
                    "address_obj": {"address_string": "789 Nature Valley"},
                    "website": "https://adventurepark.com",
                    "location_id": "attraction_3"
                },
                {
                    "name": "Spa & Wellness Center",
                    "description": "Luxurious relaxation facility offering massages, thermal baths, and wellness treatments in a serene environment.",
                    "category": {"name": "spa"},
                    "rating": 4.7,
                    "address_obj": {"address_string": "321 Wellness Way"},
                    "website": "https://spaluxury.com",
                    "location_id": "attraction_4"
                },
                {
                    "name": "Historic Cathedral",
                    "description": "Magnificent medieval cathedral featuring stunning architecture, religious art, and guided tours of the bell tower.",
                    "category": {"name": "historic"},
                    "rating": 4.5,
                    "address_obj": {"address_string": "100 Cathedral Square"},
                    "website": "https://cathedral.com",
                    "location_id": "attraction_5"
                }
            ]
        }

class GetYourGuideAPI:
    def __init__(self):
        self.api_key = os.getenv("GETYOURGUIDE_API_KEY")
        self.use_dummy_data = (not self.api_key or self.api_key == "0")
        
        if not self.use_dummy_data:
            self.base_url = "https://api.getyourguide.com/v1"
            self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def search_activities(self, location: str, category: Optional[str] = None):
        """Search activities and tours"""
        if self.use_dummy_data:
            return self._get_dummy_activities(category)
        
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
            return self._get_dummy_activities(category)
    
    def _get_dummy_activities(self, category: Optional[str] = None):
        """Return dummy activity data"""
        activities = {
            "culture": [
                {
                    "title": "Guided Historical Walking Tour",
                    "description": "Discover the city's fascinating history with a knowledgeable local guide. Visit iconic landmarks and hear captivating stories from the past.",
                    "price": {"amount": 25.0},
                    "duration": "2.5 hours",
                    "rating": 4.4,
                    "location": "Historic District",
                    "booking_url": "https://tours.com/historical-tour",
                    "id": "culture_activity_1"
                },
                {
                    "title": "Art Gallery & Museum Combo Tour",
                    "description": "Explore renowned art collections and cultural exhibits with skip-the-line access and expert commentary.",
                    "price": {"amount": 35.0},
                    "duration": "3 hours",
                    "rating": 4.6,
                    "location": "Arts Quarter",
                    "booking_url": "https://tours.com/art-tour",
                    "id": "culture_activity_2"
                }
            ],
            "food": [
                {
                    "title": "Local Food & Wine Tasting Tour",
                    "description": "Savor authentic local cuisine and regional wines at hidden gems known only to locals. Includes 5 tastings.",
                    "price": {"amount": 55.0},
                    "duration": "3.5 hours",
                    "rating": 4.8,
                    "location": "Food District",
                    "booking_url": "https://tours.com/food-tour",
                    "id": "food_activity_1"
                },
                {
                    "title": "Cooking Class with Local Chef",
                    "description": "Learn to prepare traditional dishes with a professional chef. Take home recipes and new culinary skills.",
                    "price": {"amount": 75.0},
                    "duration": "4 hours",
                    "rating": 4.7,
                    "location": "Culinary School",
                    "booking_url": "https://tours.com/cooking-class",
                    "id": "food_activity_2"
                }
            ],
            "adventure": [
                {
                    "title": "City Bike Adventure Tour",
                    "description": "Explore the city's best sights on two wheels with scenic routes and photo stops at major attractions.",
                    "price": {"amount": 45.0},
                    "duration": "4 hours",
                    "rating": 4.3,
                    "location": "Various Locations",
                    "booking_url": "https://tours.com/bike-tour",
                    "id": "adventure_activity_1"
                },
                {
                    "title": "Rock Climbing & Rappelling Experience",
                    "description": "Challenge yourself with guided rock climbing suitable for beginners and experienced climbers alike.",
                    "price": {"amount": 85.0},
                    "duration": "5 hours",
                    "rating": 4.5,
                    "location": "Natural Rock Formations",
                    "booking_url": "https://tours.com/climbing",
                    "id": "adventure_activity_2"
                }
            ],
            "relaxation": [
                {
                    "title": "Spa Day with Thermal Baths",
                    "description": "Unwind in natural thermal waters with access to saunas, steam rooms, and relaxation areas.",
                    "price": {"amount": 65.0},
                    "duration": "6 hours",
                    "rating": 4.6,
                    "location": "Thermal Springs Resort",
                    "booking_url": "https://tours.com/spa-day",
                    "id": "relaxation_activity_1"
                },
                {
                    "title": "Sunset Cruise with Dinner",
                    "description": "Enjoy a peaceful evening cruise with gourmet dinner and stunning views as the sun sets over the water.",
                    "price": {"amount": 95.0},
                    "duration": "3 hours",
                    "rating": 4.9,
                    "location": "Marina",
                    "booking_url": "https://tours.com/sunset-cruise",
                    "id": "relaxation_activity_2"
                }
            ]
        }
        
        if category and category in activities:
            return {"data": activities[category]}
        else:
            all_activities = []
            for cat_activities in activities.values():
                all_activities.extend(cat_activities)
            return {"data": all_activities}

# Initialize API clients
amadeus_api = AmadeusAPI()
booking_api = BookingAPI()
tripadvisor_api = TripAdvisorAPI()
getyourguide_api = GetYourGuideAPI()

# ============ STATE DEFINITION ============

class TravelPlanState(TypedDict):
    messages: Annotated[list, add_messages]
    # User requirements
    destination: Optional[str]
    departure_city: Optional[str]
    departure_date: Optional[str]
    return_date: Optional[str]
    checkin_date: Optional[str]
    checkout_date: Optional[str]
    travelers: Optional[int]
    total_budget: Optional[float]
    budget_per_person: Optional[float]
    activity_preferences: Optional[List[str]]
    trip_duration_days: Optional[int]
    
    # Search results
    flights_data: Optional[List[Dict]]
    hotels_data: Optional[List[Dict]]
    activities_data: Optional[List[Dict]]
    destination_info: Optional[Dict]
    
    # Optimization results
    selected_flight: Optional[Dict]
    selected_hotel: Optional[Dict]
    selected_activities: Optional[List[Dict]]
    optimization_complete: bool
    
    # Final output
    itinerary: Optional[Dict]
    final_response: Optional[str]
    
    # Control flags
    error_occurred: bool
    processing_complete: bool

# ============ UTILITY FUNCTIONS ============

def extract_user_requirements(messages) -> Dict:
    """Extract travel requirements from user messages using simple parsing"""
    user_content = ""
    for msg in messages:
        if hasattr(msg, 'content') and 'want to plan a trip' in msg.content.lower():
            user_content = msg.content
            break
    
    if not user_content:
        return {}
    
    requirements = {}
    
    # Extract destination
    destination_patterns = [
        r'trip to ([^,\n]+)',
        r'travel to ([^,\n]+)',
        r'visit ([^,\n]+)'
    ]
    for pattern in destination_patterns:
        match = re.search(pattern, user_content, re.IGNORECASE)
        if match:
            requirements['destination'] = match.group(1).strip()
            break
    
    # Extract departure city
    departure_patterns = [
        r'from ([^,\n]+)',
        r'departing from ([^,\n]+)'
    ]
    for pattern in departure_patterns:
        match = re.search(pattern, user_content, re.IGNORECASE)
        if match:
            requirements['departure_city'] = match.group(1).strip()
            break
    
    # Extract dates
    date_pattern = r'(\d{4}-\d{2}-\d{2})'
    dates = re.findall(date_pattern, user_content)
    if len(dates) >= 1:
        requirements['departure_date'] = dates[0]
        requirements['checkin_date'] = dates[0]
    if len(dates) >= 2:
        requirements['return_date'] = dates[1]
        requirements['checkout_date'] = dates[1]
    
    # Extract budget
    budget_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
    budget_match = re.search(budget_pattern, user_content)
    if budget_match:
        budget_str = budget_match.group(1).replace(',', '')
        requirements['budget_per_person'] = float(budget_str)
        
    # Extract number of travelers
    travelers_pattern = r'travelers?:\s*(\d+)|(\d+)\s+travelers?'
    travelers_match = re.search(travelers_pattern, user_content, re.IGNORECASE)
    if travelers_match:
        requirements['travelers'] = int(travelers_match.group(1) or travelers_match.group(2))
    
    # Extract activity preferences
    activity_keywords = {
        'culture': ['culture', 'cultural', 'museum', 'history', 'historic', 'art'],
        'food': ['food', 'cuisine', 'restaurant', 'dining', 'culinary'],
        'adventure': ['adventure', 'outdoor', 'hiking', 'climbing', 'sports'],
        'relaxation': ['relaxation', 'spa', 'beach', 'wellness', 'peaceful']
    }
    
    preferences = []
    content_lower = user_content.lower()
    for category, keywords in activity_keywords.items():
        if any(keyword in content_lower for keyword in keywords):
            preferences.append(category)
    
    if preferences:
        requirements['activity_preferences'] = preferences
    
    # Calculate trip duration if we have dates
    if requirements.get('departure_date') and requirements.get('return_date'):
        start = datetime.strptime(requirements['departure_date'], '%Y-%m-%d')
        end = datetime.strptime(requirements['return_date'], '%Y-%m-%d')
        requirements['trip_duration_days'] = (end - start).days
    
    return requirements

# ============ INDIVIDUAL TOOL FUNCTIONS ============

def search_flights_tool(departure_city: str, destination: str, departure_date: str, return_date: Optional[str] = None, 
                       travelers: int = 1, budget_per_person: float = 1000.0):
    """Search for flights using real flight APIs (Amadeus)."""
    departure_city = departure_city or "New York"
    destination = destination or "Paris"
    departure_date = departure_date or "2025-10-08"
    return_date = return_date if return_date and return_date.lower() != "none" else None
    travelers = int(travelers) if travelers else 1
    budget_per_person = float(budget_per_person) if budget_per_person else 1000.0
    
    print(f"Searching real flights from {departure_city} to {destination} on {departure_date}")
    
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
        for offer in flight_data["data"][:5]:  
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
                    "rating": 4.0 + (5 - stops) * 0.2,  
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
    
    affordable_flights = [f for f in formatted_flights if f["price"] <= budget_per_person]
    
    return affordable_flights[:3]

def search_hotels_tool(destination: str, checkin_date: str, checkout_date: str, 
                      budget_per_night: float, travelers: int = 1, accommodation_type: str = "hotel"):
    """Search for hotels using real hotel APIs (Amadeus + Booking.com)."""
    destination = destination or "Paris"
    checkin_date = checkin_date or "2025-10-08"
    checkout_date = checkout_date or "2025-10-15"
    budget_per_night = float(budget_per_night) if budget_per_night else 200.0
    travelers = int(travelers) if travelers else 1
    accommodation_type = accommodation_type or "hotel"
    
    print(f"Searching hotels in {destination} from {checkin_date} to {checkout_date}")
    
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
                for hotel in hotel_data["result"][:10]:  
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
    
    # Try Amadeus API as backup if Booking.com didn't work or returned no results
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
    
    if not formatted_hotels:
        print("No hotels found within budget constraints")
    
    return formatted_hotels[:5]

def recommend_activities_tool(destination: str, activity_preferences: List[str], 
                            daily_activity_budget: float, trip_duration_days: int):
    """Recommend activities using real activity APIs (TripAdvisor + GetYourGuide)."""
    destination = destination or "Paris"
    activity_preferences = activity_preferences if activity_preferences else ["culture", "food"]
    daily_activity_budget = float(daily_activity_budget) if daily_activity_budget else 100.0
    trip_duration_days = int(trip_duration_days) if trip_duration_days else 7
    
    print(f"Searching activities for {destination} with preferences: {activity_preferences}")
    
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
                        ta_category = attraction.get("category", {}).get("name", "").lower()
                        our_category = "culture"  
                        
                        if any(pref in ta_category for pref in ["museum", "historic", "cultural"]):
                            our_category = "culture"
                        elif any(pref in ta_category for pref in ["food", "restaurant", "culinary"]):
                            our_category = "food"
                        elif any(pref in ta_category for pref in ["adventure", "outdoor", "sports"]):
                            our_category = "adventure"
                        elif any(pref in ta_category for pref in ["spa", "beach", "relaxation"]):
                            our_category = "relaxation"
                        
                        if our_category in activity_preferences:
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
    for preference in activity_preferences[:2]:  
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
    
    unique_activities = []
    seen_names = set()
    
    for activity in sorted(formatted_activities, key=lambda x: x["rating"], reverse=True):
        if activity["name"] not in seen_names:
            unique_activities.append(activity)
            seen_names.add(activity["name"])
    
    return unique_activities[:trip_duration_days]

def get_destination_info_tool(destination: str):
    """Get general information about a destination including weather, currency, etc."""
    print(f"Getting destination info for {destination}")
    
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
    
    return info

# ============ STATE NODE FUNCTIONS ============

def extract_requirements_node(state: TravelPlanState) -> TravelPlanState:
    """Extract user requirements from messages"""
    print("Extracting user requirements...")
    
    requirements = extract_user_requirements(state["messages"])
    
    # Calculate total budget if we have budget per person and travelers
    total_budget = None
    if requirements.get('budget_per_person') and requirements.get('travelers'):
        total_budget = requirements['budget_per_person'] * requirements['travelers']
    
    # Return properly typed state update
    return {
        "messages": state["messages"],
        "destination": requirements.get("destination"),
        "departure_city": requirements.get("departure_city"),
        "departure_date": requirements.get("departure_date"),
        "return_date": requirements.get("return_date"),
        "checkin_date": requirements.get("checkin_date"),
        "checkout_date": requirements.get("checkout_date"),
        "travelers": requirements.get("travelers"),
        "total_budget": total_budget,
        "budget_per_person": requirements.get("budget_per_person"),
        "activity_preferences": requirements.get("activity_preferences"),
        "trip_duration_days": requirements.get("trip_duration_days"),
        "flights_data": state.get("flights_data"),
        "hotels_data": state.get("hotels_data"),
        "activities_data": state.get("activities_data"),
        "destination_info": state.get("destination_info"),
        "selected_flight": state.get("selected_flight"),
        "selected_hotel": state.get("selected_hotel"),
        "selected_activities": state.get("selected_activities"),
        "optimization_complete": False,
        "itinerary": state.get("itinerary"),
        "final_response": state.get("final_response"),
        "error_occurred": False,
        "processing_complete": False
    }

def search_flights_node(state: TravelPlanState) -> TravelPlanState:
    """Search for flights"""
    print("Searching for flights...")
    
    try:
        flights = search_flights_tool(
            departure_city=state.get("departure_city") or "New York",
            destination=state.get("destination") or "Paris",
            departure_date=state.get("departure_date") or "2025-10-08",
            return_date=state.get("return_date"),  # This can be None
            travelers=state.get("travelers") or 1,
            budget_per_person=state.get("budget_per_person") or 1000.0
        )
        
        # Return complete state with flights data updated
        return {**state, "flights_data": flights}
        
    except Exception as e:
        print(f"Error searching flights: {e}")
        return {**state, "error_occurred": True}

def search_hotels_node(state: TravelPlanState) -> TravelPlanState:
    """Search for hotels"""
    print("Searching for hotels...")
    
    try:
        # Calculate budget per night (rough estimate: 40% of total budget for hotels)
        budget_per_person = state.get("budget_per_person") or 1000.0
        trip_duration = state.get("trip_duration_days") or 7
        budget_per_night = (budget_per_person * 0.4) / trip_duration if trip_duration > 0 else 150.0
        
        hotels = search_hotels_tool(
            destination=state.get("destination") or "Paris",
            checkin_date=state.get("checkin_date") or "2025-10-08",
            checkout_date=state.get("checkout_date") or "2025-10-15",
            budget_per_night=budget_per_night,
            travelers=state.get("travelers") or 1
        )
        
        return {**state, "hotels_data": hotels}
        
    except Exception as e:
        print(f"Error searching hotels: {e}")
        return {**state, "error_occurred": True}

def search_activities_node(state: TravelPlanState) -> TravelPlanState:
    """Search for activities"""
    print("Searching for activities...")
    
    try:
        # Calculate daily activity budget (rough estimate: 20% of total budget for activities)
        budget_per_person = state.get("budget_per_person") or 1000.0
        trip_duration = state.get("trip_duration_days") or 7
        daily_activity_budget = (budget_per_person * 0.2) / trip_duration if trip_duration > 0 else 50.0
        
        activities = recommend_activities_tool(
            destination=state.get("destination") or "Paris",
            activity_preferences=state.get("activity_preferences") or ["culture", "food"],
            daily_activity_budget=daily_activity_budget,
            trip_duration_days=trip_duration
        )
        
        return {**state, "activities_data": activities}
        
    except Exception as e:
        print(f"Error searching activities: {e}")
        return {**state, "error_occurred": True}

def get_destination_info_node(state: TravelPlanState) -> TravelPlanState:
    """Get destination information"""
    print("Getting destination information...")
    
    try:
        dest_info = get_destination_info_tool(state.get("destination") or "Paris")
        return {**state, "destination_info": dest_info}
        
    except Exception as e:
        print(f"Error getting destination info: {e}")
        return {**state, "error_occurred": True}

def optimize_budget_node(state: TravelPlanState) -> TravelPlanState:
    """Optimize budget and select best options"""
    print("Optimizing budget and selecting best options...")
    
    try:
        # Prepare data for optimization
        flights = state.get("flights_data") or []
        hotels = state.get("hotels_data") or []
        activities = state.get("activities_data") or []
        
        # Use fallback data if any are missing
        if not flights:
            flights = [
                {"airline": "Delta Airlines", "price": 450.0, "duration": "PT8H30M", "stops": 1, "rating": 4.2, "booking_token": "mock_token_1"},
                {"airline": "American Airlines", "price": 520.0, "duration": "PT7H45M", "stops": 0, "rating": 4.5, "booking_token": "mock_token_2"}
            ]
        
        if not hotels:
            hotels = [
                {"name": "Grand Central Hotel", "rating": 8.5, "price_per_night": 120.0, "total_cost": 840.0, "location": "City Center", "amenities": ["WiFi", "Restaurant", "Gym", "Pool"], "category": "mid-range", "booking_url": "", "hotel_id": "hotel_1"},
                {"name": "Budget Comfort Inn", "rating": 7.8, "price_per_night": 65.0, "total_cost": 455.0, "location": "Suburb", "amenities": ["WiFi", "Parking"], "category": "budget", "booking_url": "", "hotel_id": "hotel_2"}
            ]
        
        if not activities:
            activities = [
                {"name": "Local Food & Wine Tasting Tour", "price": 55.0, "category": "food", "duration": "3.5 hours", "rating": 4.8, "description": "Authentic local cuisine tasting"},
                {"name": "Art Gallery & Museum Tour", "price": 35.0, "category": "culture", "duration": "3 hours", "rating": 4.6, "description": "Explore renowned art collections"},
                {"name": "Adventure Park & Trails", "price": 65.0, "category": "adventure", "duration": "4 hours", "rating": 4.4, "description": "Outdoor adventure activities"}
            ]
        
        # Simple optimization logic (balanced approach)
        budget_per_person = state.get("budget_per_person") or 1000.0
        
        # Select best value flight
        selected_flight = max(flights, key=lambda f: f.get("rating", 0) / max(f.get("price", 999999), 1))
        
        # Select best value hotel
        selected_hotel = max(hotels, key=lambda h: h.get("rating", 0) / max(h.get("price_per_night", 999999), 1))
        
        # Select activities within remaining budget
        remaining_budget = budget_per_person - selected_flight.get("price", 0) - selected_hotel.get("total_cost", 0)
        selected_activities = []
        current_cost = 0
        
        for activity in sorted(activities, key=lambda a: a.get("rating", 0), reverse=True):
            activity_price = activity.get("price", 0)
            if current_cost + activity_price <= remaining_budget:
                selected_activities.append(activity)
                current_cost += activity_price
        
        return {
            **state,
            "selected_flight": selected_flight,
            "selected_hotel": selected_hotel,
            "selected_activities": selected_activities,
            "optimization_complete": True
        }
        
    except Exception as e:
        print(f"Error optimizing budget: {e}")
        return {**state, "error_occurred": True}

def generate_itinerary_node(state: TravelPlanState) -> TravelPlanState:
    """Generate detailed itinerary"""
    print("Generating detailed itinerary...")
    
    try:
        destination = state.get("destination") or "Paris"
        checkin_date = state.get("checkin_date") or "2025-10-08"
        checkout_date = state.get("checkout_date") or "2025-10-15"
        selected_flight = state.get("selected_flight") or {}
        selected_hotel = state.get("selected_hotel") or {}
        selected_activities = state.get("selected_activities") or []
        destination_info = state.get("destination_info") or {}
        
        # Calculate trip details
        start_date = datetime.strptime(checkin_date, "%Y-%m-%d")
        end_date = datetime.strptime(checkout_date, "%Y-%m-%d")
        trip_duration = (end_date - start_date).days
        
        itinerary = []
        
        # Add destination info
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
                    "activity": f"Flight Arrival - {selected_flight.get('airline', 'Unknown Airline')}",
                    "description": f"Arrive at {destination}",
                    "cost": selected_flight.get("price", 0),
                    "duration": selected_flight.get("duration", "8 hours")
                },
                {
                    "time": "Late Afternoon",
                    "activity": f"Hotel Check-in - {selected_hotel.get('name', 'Unknown Hotel')}",
                    "description": f"Check into {selected_hotel.get('name', 'hotel')} in {selected_hotel.get('location', 'city center')}",
                    "cost": 0,
                    "duration": "30 minutes"
                },
                {
                    "time": "Evening",
                    "activity": "Welcome Dinner",
                    "description": "Explore local dining near hotel",
                    "cost": 50,
                    "duration": "2 hours"
                }
            ],
            "daily_total": selected_flight.get("price", 0) + 50
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
                    "duration": "1 hour"
                }
            ]
            
            daily_total = 15
            
            # Add main activity if available
            if activity_index < len(selected_activities):
                activity = selected_activities[activity_index]
                day_activities.append({
                    "time": "Mid-Morning to Afternoon",
                    "activity": activity.get("name", "Activity"),
                    "description": activity.get("description", "Enjoy local activities"),
                    "cost": activity.get("price", 0),
                    "duration": activity.get("duration", "3 hours")
                })
                daily_total += activity.get("price", 0)
                activity_index += 1
            else:
                day_activities.append({
                    "time": "Morning to Afternoon", 
                    "activity": "Free Exploration",
                    "description": f"Explore {destination} at your own pace",
                    "cost": 30,
                    "duration": "4 hours"
                })
                daily_total += 30
            
            day_activities.append({
                "time": "Evening",
                "activity": "Dinner & Leisure",
                "description": "Local dining and evening activities",
                "cost": 60,
                "duration": "2-3 hours"
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
                    "duration": "1 hour"
                },
                {
                    "time": "Late Morning/Afternoon",
                    "activity": "Departure",
                    "description": "Travel to airport and departure",
                    "cost": 0,
                    "duration": "Variable"
                }
            ],
            "daily_total": 0
        }
        itinerary.append(departure_day)
        
        # Calculate total itinerary cost
        total_itinerary_cost = sum(day.get("daily_total", 0) for day in itinerary if day.get("type") != "destination_info")
        
        itinerary_result = {
            "itinerary": itinerary, 
            "total_days": len([d for d in itinerary if d.get("type") != "destination_info"]),
            "total_cost": total_itinerary_cost,
            "booking_summary": {
                "flight": {
                    "airline": selected_flight.get("airline", "Unknown"),
                    "price": selected_flight.get("price", 0),
                    "booking_token": selected_flight.get("booking_token", "")
                },
                "hotel": {
                    "name": selected_hotel.get("name", "Unknown"),
                    "total_cost": selected_hotel.get("total_cost", 0),
                    "booking_url": selected_hotel.get("booking_url", "")
                },
                "activities_count": len(selected_activities),
                "activities_cost": sum(a.get("price", 0) for a in selected_activities)
            }
        }
        
        return {**state, "itinerary": itinerary_result, "processing_complete": True}
        
    except Exception as e:
        print(f"Error generating itinerary: {e}")
        return {**state, "error_occurred": True}

def format_final_response_node(state: TravelPlanState) -> TravelPlanState:
    """Format the final response for the user"""
    print("Formatting final response...")
    
    try:
        # Extract all the gathered information with proper None handling
        destination = state.get("destination") or "Unknown"
        budget_per_person = state.get("budget_per_person") or 0
        travelers = state.get("travelers") or 1
        trip_duration = state.get("trip_duration_days") or 0
        
        flights_data = state.get("flights_data") or []
        hotels_data = state.get("hotels_data") or []
        activities_data = state.get("activities_data") or []
        destination_info = state.get("destination_info") or {}
        
        selected_flight = state.get("selected_flight") or {}
        selected_hotel = state.get("selected_hotel") or {}
        selected_activities = state.get("selected_activities") or []
        itinerary = state.get("itinerary") or {}
        
        # Build comprehensive response
        response = f"""
TRAVEL PLAN FOR {destination.upper()}

TRIP OVERVIEW
Destination: {destination}
Duration: {trip_duration} days
Travelers: {travelers}
Budget per person: ${budget_per_person:.2f}

DESTINATION INFORMATION
Country: {destination_info.get('country', 'N/A')}
Currency: {destination_info.get('currency', 'N/A')}
Language: {destination_info.get('language', 'N/A')}
Best time to visit: {destination_info.get('best_time_to_visit', 'N/A')}
Transportation: {', '.join(destination_info.get('transportation', []))}

FLIGHT OPTIONS FOUND
"""
        
        for i, flight in enumerate(flights_data[:3], 1):
            response += f"{i}. {flight.get('airline', 'Unknown')} - ${flight.get('price', 0):.2f}\n"
            response += f"   Duration: {flight.get('duration', 'N/A')}, Stops: {flight.get('stops', 0)}, Rating: {flight.get('rating', 0):.1f}/5\n"
        
        response += f"\nHOTEL OPTIONS FOUND\n"
        for i, hotel in enumerate(hotels_data[:3], 1):
            response += f"{i}. {hotel.get('name', 'Unknown')} - ${hotel.get('price_per_night', 0):.2f}/night\n"
            response += f"   Rating: {hotel.get('rating', 0):.1f}/5, Location: {hotel.get('location', 'N/A')}\n"
            response += f"   Amenities: {', '.join(hotel.get('amenities', [])[:3])}\n"
        
        response += f"\nACTIVITY OPTIONS FOUND\n"
        for i, activity in enumerate(activities_data[:5], 1):
            response += f"{i}. {activity.get('name', 'Unknown')} - ${activity.get('price', 0):.2f}\n"
            response += f"   Category: {activity.get('category', 'N/A')}, Duration: {activity.get('duration', 'N/A')}\n"
            response += f"   Rating: {activity.get('rating', 0):.1f}/5\n"
        
        response += f"\nOPTIMIZED SELECTIONS\n"
        response += f"Selected Flight: {selected_flight.get('airline', 'Unknown')} - ${selected_flight.get('price', 0):.2f}\n"
        response += f"Selected Hotel: {selected_hotel.get('name', 'Unknown')} - ${selected_hotel.get('price_per_night', 0):.2f}/night\n"
        response += f"Selected Activities: {len(selected_activities)} activities totaling ${sum(a.get('price', 0) for a in selected_activities):.2f}\n"
        
        if itinerary and isinstance(itinerary, dict):
            response += f"\nDETAILED ITINERARY\n"
            total_cost = itinerary.get('total_cost', 0)
            response += f"Total Trip Cost: ${total_cost:.2f} per person\n"
            response += f"Total Days: {itinerary.get('total_days', 0)} days\n\n"
            
            for day in itinerary.get('itinerary', []):
                if day.get('type') == 'destination_info':
                    continue
                    
                response += f"DAY {day.get('day_number', 0)} - {day.get('title', 'Unknown')} ({day.get('date', 'N/A')})\n"
                for activity in day.get('activities', []):
                    response += f"  {activity.get('time', 'N/A')}: {activity.get('activity', 'Unknown')}\n"
                    response += f"    {activity.get('description', 'N/A')}\n"
                    if activity.get('cost', 0) > 0:
                        response += f"    Cost: ${activity.get('cost', 0):.2f}\n"
                response += f"  Daily Total: ${day.get('daily_total', 0):.2f}\n\n"
        
        response += f"\nBOOKING INFORMATION\n"
        response += f"Flight Booking: Use token {selected_flight.get('booking_token', 'N/A')}\n"
        response += f"Hotel Booking: {selected_hotel.get('booking_url', 'Contact hotel directly')}\n"
        response += f"Activities: Contact venues or use their websites for booking\n"
        
        response += f"\nYour complete travel plan is ready! All searches used real API data where available."
        
        return {**state, "final_response": response}
        
    except Exception as e:
        print(f"Error formatting response: {e}")
        return {**state, "final_response": "Sorry, there was an error formatting your travel plan. Please try again."}

# ============ ROUTING FUNCTION ============

def route_to_next_node(state: TravelPlanState) -> str:
    """Determine which node to execute next based on current state"""
    
    # Check for errors first
    if state.get("error_occurred"):
        return "format_final_response"
    
    # Check if processing is complete
    if state.get("processing_complete"):
        return "format_final_response"
    
    # Check if we have user requirements extracted
    if not state.get("destination"):
        return "extract_requirements"
    
    # Check if we have destination info
    if not state.get("destination_info"):
        return "get_destination_info"
    
    # Check if we need to search for flights
    if not state.get("flights_data"):
        return "search_flights"
    
    # Check if we need to search for hotels
    if not state.get("hotels_data"):
        return "search_hotels"
    
    # Check if we need to search for activities
    if not state.get("activities_data"):
        return "search_activities"
    
    # Check if we need to optimize
    if not state.get("optimization_complete"):
        return "optimize_budget"
    
    # Check if we need to generate itinerary
    if not state.get("itinerary"):
        return "generate_itinerary"
    
    # If everything is done, format final response
    return "format_final_response"

# ============ BUILD STATE GRAPH ============

def create_travel_planning_graph():
    """Create and configure the travel planning state graph"""
    
    # Create the state graph
    workflow = StateGraph(TravelPlanState)
    
    # Add all nodes
    workflow.add_node("extract_requirements", extract_requirements_node)
    workflow.add_node("get_destination_info", get_destination_info_node)
    workflow.add_node("search_flights", search_flights_node)
    workflow.add_node("search_hotels", search_hotels_node)
    workflow.add_node("search_activities", search_activities_node)
    workflow.add_node("optimize_budget", optimize_budget_node)
    workflow.add_node("generate_itinerary", generate_itinerary_node)
    workflow.add_node("format_final_response", format_final_response_node)
    
    # Set up routing from START
    workflow.add_conditional_edges(START, route_to_next_node)
    
    # Set up routing from each node
    workflow.add_conditional_edges("extract_requirements", route_to_next_node)
    workflow.add_conditional_edges("get_destination_info", route_to_next_node)
    workflow.add_conditional_edges("search_flights", route_to_next_node)
    workflow.add_conditional_edges("search_hotels", route_to_next_node)
    workflow.add_conditional_edges("search_activities", route_to_next_node)
    workflow.add_conditional_edges("optimize_budget", route_to_next_node)
    workflow.add_conditional_edges("generate_itinerary", route_to_next_node)
    
    # End at format_final_response
    workflow.add_edge("format_final_response", END)
    
    # Compile the graph
    return workflow.compile()

# ============ MAIN WORKFLOW FUNCTION ============

def travel_planner_workflow(input_data):
    """Main workflow using the custom LangGraph state machine"""
    
    # Extract messages from the input dictionary
    if isinstance(input_data, dict):
        messages = input_data.get("messages", [])
    else:
        messages = input_data

    try:
        print("Starting Travel Planning State Machine...")
        
        # Create the graph
        app = create_travel_planning_graph()
        
        # Initialize state with proper typing using cast
        initial_state_dict = {
            "messages": messages,
            "destination": None,
            "departure_city": None,
            "departure_date": None,
            "return_date": None,
            "checkin_date": None,
            "checkout_date": None,
            "travelers": None,
            "total_budget": None,
            "budget_per_person": None,
            "activity_preferences": None,
            "trip_duration_days": None,
            "flights_data": None,
            "hotels_data": None,
            "activities_data": None,
            "destination_info": None,
            "selected_flight": None,
            "selected_hotel": None,
            "selected_activities": None,
            "optimization_complete": False,
            "itinerary": None,
            "final_response": None,
            "error_occurred": False,
            "processing_complete": False
        }
        
        # Cast to proper type
        initial_state = cast(TravelPlanState, initial_state_dict)
        
        # Run the state machine
        final_state = app.invoke(initial_state)
        
        # Create response message
        final_response = final_state.get("final_response", "Travel planning completed successfully!")
        response_message = AIMessage(content=final_response)
        
        return [response_message]
        
    except Exception as e:
        print(f"Error in Travel Planning State Machine: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error message
        error_message = AIMessage(
            content=f"Sorry, there was an error planning your trip: {str(e)}. Please try again with your travel requirements."
        )
        return [error_message]

# ============ UTILITY FUNCTIONS ============

def pretty_print_messages(messages):
    """Print messages in a readable format"""
    for message in messages:
        if hasattr(message, 'content') and message.content:
            content = message.content
            
            # Handle both string content and list content
            if isinstance(content, str):
                content_text = content.strip()
            elif isinstance(content, list):
                # Extract text from content blocks
                content_text = ""
                for block in content:
                    if isinstance(block, str):
                        content_text += block
                    elif isinstance(block, dict) and 'text' in block:
                        content_text += block['text']
                content_text = content_text.strip()
            else:
                content_text = str(content).strip()
                
            if content_text:
                print(f"\n{content_text}\n")
                print("-" * 50)

# ============ MAIN EXECUTION ============

if __name__ == "__main__":
    print("\nWelcome to Travel Buddy™ with Custom LangGraph State Machine!")
    print("=" * 70)
    print("Note: This system uses dummy data for partner-only APIs (Booking.com, TripAdvisor, GetYourGuide)")
    print("Enter '0' for API keys you don't have access to.")
    print()
    
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
    print("The State Machine will intelligently coordinate all aspects of your trip planning...\n")
    
    try:
        human_message = HumanMessage(content=user_message_content)
        
        print("Starting intelligent travel planning state machine...")
        
        result = travel_planner_workflow({"messages": [human_message]})
        
        print("\nTrip planning complete!")
        print("=" * 70)
        
        # Print the final response
        for message in result:
            if hasattr(message, 'content') and message.content:
                content = message.content
                
                # Handle both string content and list content
                if isinstance(content, str):
                    content_text = content.strip()
                elif isinstance(content, list):
                    # Extract text from content blocks
                    content_text = ""
                    for block in content:
                        if isinstance(block, str):
                            content_text += block
                        elif isinstance(block, dict) and 'text' in block:
                            content_text += block['text']
                    content_text = content_text.strip()
                else:
                    content_text = str(content).strip()
                
                if content_text:
                    print(f"\n{content_text}")
                    
    except Exception as e:
        print(f"\nError planning trip: {e}")
        import traceback
        traceback.print_exc()
        print("\nMake sure your API keys are correct and you have internet connection.")
        print("For partner-only APIs, enter '0' to use dummy data.")