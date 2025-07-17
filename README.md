# Travel Buddy 🌍✈️

An intelligent AI-powered travel planning assistant that creates comprehensive trip itineraries using real-time data from multiple travel APIs.

## 🌟 Features

- **Real-time Flight Search** - Powered by Amadeus API for live flight data
- **Hotel Recommendations** - Integrated with Booking.com and Amadeus hotel APIs
- **Activity Suggestions** - TripAdvisor and GetYourGuide integration for authentic experiences
- **Smart Budget Optimization** - AI-powered budget allocation and cost optimization
- **Detailed Itineraries** - Day-by-day planning with booking information and practical tips
- **Multi-Agent Architecture** - Specialized AI agents for each travel component

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- API keys for travel services (see [API Setup](#api-setup))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/rishabhagg248/travel_buddy.git
cd travel_buddy
```

2. Run the script (dependencies will be auto-installed):
```bash
python travel_buddy.py
```

The script will automatically install required packages:
- `langchain-openai`
- `langgraph`
- `requests`
- `typing-extensions`

### API Setup

You'll need API keys from the following services:

#### Required APIs:
- **OpenAI API** - For AI agents and language processing
- **Amadeus API** - For flights and hotels
- **Booking.com API** - For hotel data
- **TripAdvisor API** - For attractions and reviews
- **GetYourGuide API** - For activities and tours

#### Getting API Keys:

1. **OpenAI**: Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Amadeus**: Register at [Amadeus for Developers](https://developers.amadeus.com/)
3. **Booking.com**: Apply through [RapidAPI Booking.com](https://rapidapi.com/apidojo/api/booking/)
4. **TripAdvisor**: Get access at [TripAdvisor Content API](https://developer-tripadvisor.com/)
5. **GetYourGuide**: Apply at [GetYourGuide Partner API](https://partner-help.getyourguide.com/hc/en-us/articles/4411371325597)

The script will prompt you for API keys on first run.

## 🎯 Usage

### Interactive Mode

Run the script and follow the prompts:

```bash
python travel_buddy.py
```

You'll be asked for:
- Destination city
- Departure city
- Travel dates
- Budget per person
- Number of travelers

### Example Session

```
Welcome to Travel Buddy™!
==================================================

Let's plan your trip!
Where would you like to travel? Paris
Where are you departing from? New York
Departure date (YYYY-MM-DD): 2024-03-15
Return date (YYYY-MM-DD, or press Enter for one-way): 2024-03-22
Total budget per person ($): 2000
Number of travelers: 2
```

## 🏗️ Architecture

Travel Buddy™ uses a multi-agent architecture with specialized AI agents:

### Agent Flow
```
User Input → Flight Search → Hotel Search → Activity Recommender → Budget Optimizer → Itinerary Generator
```

### Agents:

1. **Flight Search Agent** - Finds optimal flights within budget
2. **Hotel Search Agent** - Recommends accommodations based on preferences
3. **Activity Recommender Agent** - Suggests activities based on interests
4. **Budget Optimizer Agent** - Optimizes selections for best value
5. **Itinerary Generator Agent** - Creates detailed day-by-day plans

## 📊 API Integrations

### Amadeus API
- Flight search and pricing
- Hotel availability and rates
- Location data

### Booking.com API
- Hotel search and booking
- Property details and amenities
- Real-time availability

### TripAdvisor API
- Attraction information
- Reviews and ratings
- Location-based recommendations

### GetYourGuide API
- Tours and activities
- Booking information
- Experience details

## 🔧 Configuration

### Budget Allocation Strategy
- **Flights**: 35% of budget
- **Hotels**: 45% of budget  
- **Activities**: 20% of budget

### Budget Priorities
- **Economy**: Focus on lowest prices
- **Balanced**: Optimize price-to-value ratio
- **Luxury**: Prioritize quality and ratings

## 📝 Output Format

The system generates:

1. **Flight Options** with real pricing and booking tokens
2. **Hotel Recommendations** with amenities and booking URLs
3. **Activity Suggestions** with descriptions and pricing
4. **Budget Analysis** with cost breakdown and optimization tips
5. **Detailed Itinerary** with day-by-day planning and booking information

## 🛠️ Technical Details

### Dependencies
- **LangChain**: AI agent framework
- **LangGraph**: Multi-agent orchestration
- **OpenAI**: Language model for AI agents
- **Requests**: HTTP client for API calls

### Error Handling
- Automatic fallback to mock data if APIs are unavailable
- Graceful degradation for missing API keys
- Comprehensive error logging

### Rate Limiting
- Built-in token management for Amadeus API
- Efficient API call optimization
- Fallback mechanisms for API limits

## 🔐 Security

- API keys are requested securely via `getpass`
- No API keys are stored in code or logs
- Environment variables for production deployment

## 🚧 Development

### Adding New APIs

1. Create a new API client class in the API section
2. Add corresponding tools using the `@tool` decorator
3. Integrate with existing agents or create new specialized agents

### Extending Functionality

The modular architecture makes it easy to add:
- New travel services
- Additional optimization strategies
- Custom travel preferences
- Enhanced itinerary features

## 📋 Limitations

- Some APIs require approval processes
- Mock data fallbacks for unavailable APIs
- Test API endpoints used (switch to production for live data)
- Rate limits apply to free API tiers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter issues:

1. Check that all API keys are valid
2. Verify internet connection
3. Review API documentation for any service changes
4. Open an issue with error details

## 🔮 Roadmap

- [ ] Web interface
- [ ] Mobile app
- [ ] Real-time price alerts
- [ ] Group travel planning
- [ ] Multi-destination trips
- [ ] Travel document management
- [ ] Weather integration
- [ ] Currency conversion
- [ ] Travel insurance recommendations

---

**Happy Travels!** 🎒✨

*Built with ❤️ using AI agents and real travel APIs*
