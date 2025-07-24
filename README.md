# Travel Buddy 🌍✈️

An intelligent AI-powered travel planning assistant that creates comprehensive trip itineraries using real-time data from multiple travel APIs. Available in multiple architectural implementations to suit different needs and preferences.

## 🌟 Features

- **Real-time Flight Search** - Powered by Amadeus API for live flight data
- **Hotel Recommendations** - Integrated with Booking.com and Amadeus hotel APIs
- **Activity Suggestions** - TripAdvisor and GetYourGuide integration for authentic experiences
- **Smart Budget Optimization** - AI-powered budget allocation and cost optimization
- **Detailed Itineraries** - Day-by-day planning with booking information and practical tips
- **Multiple Architecture Options** - Choose between agent-based or state machine implementations
- **Interactive Visualization** - Visual state machine flow diagram for understanding the architecture

## 🏗️ Architecture Variants

Travel Buddy™ comes in three different implementations plus an interactive visualization:

### 1. **travel_buddy_manager.py** ⭐ (Recommended)
**Custom LangGraph State Machine Implementation**

- **Architecture**: Deterministic state machine with intelligent routing
- **Performance**: Faster execution with minimal LLM overhead
- **Reliability**: Predictable workflow with robust error handling
- **Type Safety**: Full TypeScript-style type checking
- **Best For**: Production environments, cost-sensitive applications, predictable workflows

```bash
python travel_buddy_manager.py
```

**Key Benefits:**
- ✅ Deterministic routing logic
- ✅ Lower API costs (fewer LLM calls)
- ✅ Better performance and reliability
- ✅ Complete type safety
- ✅ Easier debugging and maintenance

### 2. **travel_buddy.py**
**Multi-Agent ReAct Implementation**

- **Architecture**: Specialized AI agents with LLM-driven coordination
- **Performance**: More LLM calls for agent reasoning
- **Flexibility**: Agents can adapt and make intelligent decisions
- **Best For**: Complex decision-making scenarios, research environments

```bash
python travel_buddy.py
```

**Key Features:**
- 🤖 Flight Search Agent
- 🏨 Hotel Search Agent  
- 🎯 Activity Recommender Agent
- 💰 Budget Optimizer Agent
- 📋 Itinerary Generator Agent

### 3. **travel_buddy_ph.py**
**Enhanced Multi-Agent with Improved Error Handling**

- **Architecture**: Similar to travel_buddy.py with enhanced error handling
- **Features**: Better API fallbacks and dummy data integration
- **Best For**: Development and testing with unreliable API access

```bash
python travel_buddy_ph.py
```

### 4. **travel_buddy_visualizer.html** 📊
**Interactive State Machine Visualization**

- **Purpose**: Visual representation of the state machine architecture
- **Features**: Interactive flow diagram with hover tooltips
- **Technology**: Pure HTML/CSS/JavaScript with responsive design
- **Best For**: Understanding the system architecture and flow

```bash
# Open in any web browser
open travel_buddy_visualizer.html
```

**Visualization Features:**
- 🎯 **11-Step Flow Diagram** - Clear numbered sequence
- 🔄 **Interactive Tooltips** - Hover over any step for detailed explanations
- 📱 **Fully Responsive** - Works on desktop, tablet, and mobile
- 🎨 **Color-Coded Steps** - Start (green), Process (blue), Decision (orange), End (red)
- 📊 **Router Logic Display** - Shows the actual decision-making code
- 💡 **Architecture Benefits** - Highlights advantages of the state machine approach

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

2. Run any of the implementations (dependencies will be auto-installed):
```bash
# Recommended: State machine version
python travel_buddy_manager.py

# Or: Multi-agent version
python travel_buddy.py

# Or: Enhanced multi-agent version
python travel_buddy_ph.py
```

The scripts will automatically install required packages:
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

The scripts will prompt you for API keys on first run. For partner-only APIs, enter '0' to use dummy data.

## 🎯 Usage

### Interactive Mode

Run any implementation and follow the prompts:

```bash
python travel_buddy_manager.py  # Recommended
```

You'll be asked for:
- Destination city
- Departure city
- Travel dates
- Budget per person
- Number of travelers

### Visualizing the Architecture

Open the interactive visualization to understand how the state machine works:

```bash
# Open in any web browser
open travel_buddy_visualizer.html
# Or double-click the file in your file explorer
```

**Interactive Features:**
- **Hover over numbered steps** to see detailed explanations
- **Responsive design** that works on any screen size
- **Visual flow representation** of the state machine logic
- **Router decision logic** displayed with actual code

### Example Session

```
Welcome to Travel Buddy™ with Custom LangGraph State Machine!
==================================================

Let's plan your trip!
Where would you like to travel? Paris
Where are you departing from? New York
Departure date (YYYY-MM-DD): 2024-03-15
Return date (YYYY-MM-DD, or press Enter for one-way): 2024-03-22
Total budget per person ($): 2000
Number of travelers: 2
```

## 🔄 Architecture Comparison

| Feature | State Machine (`manager.py`) | Multi-Agent (`travel_buddy.py`) | Enhanced Multi-Agent (`ph.py`) | Visualizer (`visualizer.html`) |
|---------|------------------------------|----------------------------------|--------------------------------|---------------------------------|
| **Performance** | ⭐⭐⭐⭐⭐ Fastest | ⭐⭐⭐ Moderate | ⭐⭐⭐ Moderate | N/A - Visualization Only |
| **Cost Efficiency** | ⭐⭐⭐⭐⭐ Lowest | ⭐⭐ Higher LLM usage | ⭐⭐ Higher LLM usage | N/A - Static Content |
| **Reliability** | ⭐⭐⭐⭐⭐ Deterministic | ⭐⭐⭐ Variable | ⭐⭐⭐⭐ Enhanced | N/A - Educational Tool |
| **Flexibility** | ⭐⭐⭐ Structured | ⭐⭐⭐⭐⭐ Highly adaptive | ⭐⭐⭐⭐ Adaptive | N/A - Documentation |
| **Type Safety** | ⭐⭐⭐⭐⭐ Full typing | ⭐⭐ Basic | ⭐⭐⭐ Improved | N/A - HTML/CSS/JS |
| **Error Handling** | ⭐⭐⭐⭐⭐ Robust | ⭐⭐⭐ Standard | ⭐⭐⭐⭐⭐ Enhanced | N/A - No Processing |
| **Best For** | Production | Research/Complex | Development | Understanding Architecture |
| **User Experience** | Command Line | Command Line | Command Line | Interactive Web Interface |

## 🏗️ Technical Architecture

### State Machine Flow (`travel_buddy_manager.py`)
```
User Input → Extract Requirements → Get Destination Info → 
Search Flights → Search Hotels → Search Activities → 
Optimize Budget → Generate Itinerary → Format Response
```

### Multi-Agent Flow (`travel_buddy.py`, `travel_buddy_ph.py`)
```
User Input → Flight Search Agent → Hotel Search Agent → 
Activity Recommender Agent → Budget Optimizer Agent → 
Itinerary Generator Agent
```

### State Machine Components:

1. **Requirements Extraction** - Parse user input using regex patterns
2. **Destination Info Lookup** - Get country, currency, and travel details
3. **Flight Search** - Find optimal flights within budget
4. **Hotel Search** - Recommend accommodations based on preferences
5. **Activity Recommendations** - Suggest activities based on interests
6. **Budget Optimization** - Optimize selections for best value
7. **Itinerary Generation** - Create detailed day-by-day plans
8. **Response Formatting** - Generate comprehensive travel report

### Multi-Agent Components:

1. **Flight Search Agent** - Specialized in flight search and booking
2. **Hotel Search Agent** - Expert in accommodation recommendations  
3. **Activity Recommender Agent** - Focuses on local experiences
4. **Budget Optimizer Agent** - Analyzes costs and optimizes selections
5. **Itinerary Generator Agent** - Creates detailed travel plans

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

All implementations generate:

1. **Flight Options** with real pricing and booking tokens
2. **Hotel Recommendations** with amenities and booking URLs
3. **Activity Suggestions** with descriptions and pricing
4. **Budget Analysis** with cost breakdown and optimization tips
5. **Detailed Itinerary** with day-by-day planning and booking information

## 🛠️ Technical Details

### Dependencies
- **LangChain**: AI agent framework
- **LangGraph**: Multi-agent orchestration and state machines
- **OpenAI**: Language model for AI processing
- **Requests**: HTTP client for API calls
- **Typing Extensions**: Enhanced type annotations

### Error Handling
- Automatic fallback to mock data if APIs are unavailable
- Graceful degradation for missing API keys
- Comprehensive error logging
- Enhanced error recovery in `travel_buddy_ph.py`

### Rate Limiting
- Built-in token management for Amadeus API
- Efficient API call optimization
- Fallback mechanisms for API limits

## 🔐 Security

- API keys are requested securely via `getpass`
- No API keys are stored in code or logs
- Environment variables for production deployment

## 🚧 Development

### Choosing the Right Implementation

**Use `travel_buddy_manager.py` when:**
- Building production applications
- Cost efficiency is important
- You need predictable, reliable workflows
- Type safety is a priority
- Debugging and maintenance ease matters

**Use `travel_buddy.py` when:**
- You need maximum flexibility
- Complex decision-making is required
- Research or experimental use cases
- Agent reasoning is beneficial

**Use `travel_buddy_ph.py` when:**
- Developing with unreliable API access
- Testing with dummy data
- Need enhanced error handling
- Working in development environments

**Use `travel_buddy_visualizer.html` when:**
- Learning about the system architecture
- Explaining the state machine concept to others
- Debugging the flow logic
- Understanding the step-by-step process
- Training team members on the system

### Adding New Features

1. **State Machine**: Add new node functions and update routing logic
2. **Multi-Agent**: Create new specialized agents or enhance existing ones
3. **APIs**: Add new API client classes and integrate with existing tools

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
4. Test with all three implementations
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter issues:

1. Check that all API keys are valid
2. Verify internet connection
3. Try different implementations based on your needs
4. Use the visualizer to understand the expected flow
5. Review API documentation for any service changes
6. Open an issue with error details and implementation used

## 📚 Learning Resources

### Understanding the Architecture
1. **Start with the Visualizer** - Open `travel_buddy_visualizer.html` to see the flow
2. **Read the Code** - Compare the state machine vs agent implementations
3. **Test Different Approaches** - Try all three Python implementations
4. **Monitor Performance** - Compare execution times and API costs

### Educational Value
- **State Machine Concepts** - Learn deterministic vs probabilistic routing
- **Multi-Agent Systems** - Understand agent coordination and handoffs
- **API Integration** - See real-world API usage patterns
- **Error Handling** - Compare different approaches to failure recovery

## 🔮 Roadmap

- [ ] Web interface for all implementations
- [ ] Mobile app version
- [ ] Real-time price alerts
- [ ] Group travel planning
- [ ] Multi-destination trips
- [ ] Travel document management
- [ ] Weather integration
- [ ] Currency conversion
- [ ] Travel insurance recommendations
- [ ] Hybrid architecture combining state machine efficiency with agent flexibility

---

**Happy Travels!** 🎒✨

*Built with ❤️ using AI agents, state machines, and real travel APIs*

**Choose Your Adventure:**
- 🚀 **Fast & Reliable**: `travel_buddy_manager.py`
- 🤖 **Intelligent & Flexible**: `travel_buddy.py`  
- 🛠️ **Enhanced Development**: `travel_buddy_ph.py`
- 📊 **Interactive Learning**: `travel_buddy_visualizer.html`

**Quick Start Guide:**
1. **New to the project?** → Start with `travel_buddy_visualizer.html`
2. **Want to run it?** → Use `travel_buddy_manager.py`
3. **Need flexibility?** → Try `travel_buddy.py`
4. **Developing/Testing?** → Use `travel_buddy_ph.py`
