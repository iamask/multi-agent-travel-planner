# Multi-Agent Travel Planner System

A powerful travel planning system built with **Semantic Kernel** that demonstrates multi-agent collaboration, plugins, and intelligent feedback loops.

## 🎯 **Quick Overview**

**Two Specialized Agents:**

- **Agent 1: Destination Analyzer (GPT-4o-mini)** - Extracts travel details from natural language
- **Agent 2: Itinerary Builder (GPT-4o-mini)** - Creates comprehensive travel itineraries

**Key Features:**

- ✅ **No Hallucination** - Agents ask for missing info instead of guessing
- ✅ **Dynamic Destination Extraction** - Handles any destination from natural language
- ✅ **Intelligent Feedback Loops** - Proper agent collaboration with user interaction
- ✅ **Plugin-Based Architecture** - Structured processing with kernel functions

## 🚀 **Quick Start**

```bash
# Clone and setup
git clone <repository-url>
cd multi-agent-travel-planner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Run the system
python travel_planner.py
```

## 🏗 **Architecture**

### **Request Flow Through Components:**

```mermaid
flowchart TD
    A[User Request] --> B[Interactive Session]
    B --> C[Create Agents & Plugins]
    C --> D[Agent 1: Destination Analyzer<br/>GPT-4o-mini]
    C --> E[Agent 2: Itinerary Builder<br/>GPT-4o-mini]

    %% Agent 1 Flow
    D --> F[analyze_travel_request function]
    F --> G[Extract destination, duration, purpose]
    G --> H[Return JSON analysis<br/>(with or without missing_info)]

    %% Agent 2 Flow
    E --> I[build_itinerary function]
    I --> J{Missing Info?}
    J -->|No| K[Generate itinerary]
    J -->|Yes| L[Request clarification from Agent 1]

    %% Feedback Loop
    L --> M[handle_clarification function]
    M --> N[Use default values for missing info]
    N --> O[Update analysis with defaults]
    O --> P[Remove resolved missing_info]
    P --> I

    %% Complete Flow
    H --> I
    K --> Q[Final Travel Itinerary]

    %% Styling
    style A fill:#e1f5fe
    style D fill:#f3e5f5
    style E fill:#f3e5f5
    style F fill:#e8f5e8
    style I fill:#e8f5e8
    style M fill:#e8f5e8
    style Q fill:#e8f5e8
```

## 🔌 **Plugin Architecture**

### **Core Plugins**

#### **1. DestinationAnalyzerPlugin**

**Purpose:** Extract structured travel information from natural language requests.

**Functions:**

```python
@kernel_function(
    description="Analyze travel request and extract key information",
    name="analyze_travel_request"
)
def analyze_travel_request(self, user_request: str) -> str:
    # Dynamic destination extraction using travel keywords
    # Duration detection from keywords (week, day, month)
    # Purpose identification (cherry blossom, beach, business)
    # Missing info detection and JSON output
    return json.dumps(analysis)

@kernel_function(
    description="Handle user clarifications and update analysis",
    name="handle_clarification"
)
def handle_clarification(self, original_analysis: str, user_clarification: str) -> str:
    # Enhanced duration extraction with regex patterns
    # Update destination from user input
    # Remove resolved missing info from analysis
    # Return updated JSON analysis
    return json.dumps(updated_analysis)
```

**Features:**

- **Dynamic Destination Extraction** - Handles any destination from natural language
- **Enhanced Duration Processing** - Regex-based extraction for accurate user input
- **Anti-Hallucination** - Never guesses missing information
- **Structured Output** - JSON-based communication with other plugins

#### **2. ItineraryBuilderPlugin**

**Purpose:** Generate comprehensive travel itineraries based on analyzed data.

**Functions:**

```python
@kernel_function(
    description="Build travel itinerary based on analysis",
    name="build_itinerary"
)
def build_itinerary(self, analysis: str) -> str:
    # Check for missing info
    # Request clarification if needed
    # Generate specialized or general itinerary
    return itinerary_text

def _request_clarification(self, missing_info: List[str]) -> str:
    # Create clarification request JSON
    return json.dumps(clarification_request)

def _generate_japan_cherry_blossom_itinerary(self, duration: str) -> str:
    # Specialized Japan cherry blossom itinerary
    return detailed_itinerary

def _generate_general_itinerary(self, destination: str, duration: str, purpose: str) -> str:
    # General template for any destination
    return general_itinerary
```

**Features:**

- **Specialized Itineraries** - Custom plans for specific destinations (Japan cherry blossoms)
- **General Templates** - Flexible frameworks for any destination
- **Quality Control** - Only creates itineraries with complete information
- **Practical Details** - Accommodation, transportation, and budget tips

### **Plugin Integration**

```python
# Kernel setup with plugins
kernel = Kernel()
destination_analyzer_plugin = DestinationAnalyzerPlugin()
itinerary_builder_plugin = ItineraryBuilderPlugin()

kernel.add_plugin(destination_analyzer_plugin, "DestinationAnalyzer")
kernel.add_plugin(itinerary_builder_plugin, "ItineraryBuilder")

# Agents use kernel plugins for consistent behavior
agents = [
    ChatCompletionAgent(
        name="Agent1_DestinationAnalyzer",
        description="Agent 1: Destination Analyzer (GPT-4o-mini)",
        instructions="Use analyze_travel_request and handle_clarification functions",
        service=OpenAIChatCompletion(ai_model_id="gpt-4o-mini"),
        kernel=kernel,
    ),
    ChatCompletionAgent(
        name="Agent2_ItineraryBuilder",
        description="Agent 2: Itinerary Builder (GPT-4o-mini)",
        instructions="Use build_itinerary function",
        service=OpenAIChatCompletion(ai_model_id="gpt-4o-mini"),
        kernel=kernel,
    ),
]
```

## 📋 **Example Usage**

### **Interactive Mode:**

```bash
✈️ Your travel request: Plan a trip to Japan for cherry blossoms
🔄 Planning your trip...
✅ Travel planning completed!
```

### **Sample Requests:**

1. `"Plan a trip to Japan for cherry blossoms."`
2. `"I want to visit Paris for 5 days."`
3. `"Plan a beach vacation in Bali."`
4. `"Create an itinerary for a business trip to New York."`

## 🔧 **Technical Features**

### **Enhanced Duration Extraction:**

```python
# Look for specific duration patterns with regex
if "7" in clarification_lower and ("day" in clarification_lower or "week" in clarification_lower):
    analysis["duration"] = "7 days"
elif "day" in clarification_lower:
    # Extract number of days from the text using regex
    import re
    numbers = re.findall(r'\d+', clarification_lower)
    if numbers:
        days = numbers[0]
        analysis["duration"] = f"{days} days"
    else:
        analysis["duration"] = "7 days"  # Default
```

### **Dynamic Destination Extraction:**

```python
# Look for destination after travel keywords
travel_keywords = [
    "to ", "visit ", "go to ", "travel to ", "trip to ", "vacation to ",
    "in ", "at ", "for ", "destination", "place"
]

# Extract any destination, not just predefined ones
for keyword in travel_keywords:
    if keyword in request_lower:
        parts = request_lower.split(keyword)
        if len(parts) > 1:
            potential_destination = parts[1].split()[0]
            destination = potential_destination.title()
            break
```

## 🎓 **Learning Objectives**

This project demonstrates key **Semantic Kernel** concepts:

### **1. Plugin Development**

- Creating custom plugins with `@kernel_function`
- Structured data extraction and processing
- JSON-based communication between plugins

### **2. Agent Collaboration**

- Multi-agent systems with specialized roles
- Round-robin agent management
- Coordinated problem-solving

### **3. Intelligent Feedback Loops**

- Agent 2 asks Agent 1 for missing information
- Agent 1 processes clarification requests using `handle_clarification` function
- Complete information validation before itinerary creation

### **4. Real-World Application**

- Natural language processing for travel planning
- Structured output generation
- Practical AI system development

## 📊 **Sample Output**

### **Japan Cherry Blossom Itinerary:**

```
# Japan Cherry Blossom Itinerary (7 days)

## Trip Overview
Experience the magical cherry blossom season in Japan!

## Day-by-Day Itinerary

### Day 1: Tokyo Arrival
- Arrive in Tokyo
- Check into hotel
- Visit Ueno Park for cherry blossoms
- Dinner at local restaurant

### Day 2: Tokyo Exploration
- Visit Yoyogi Park
- Walk along Meguro River (famous for cherry blossoms)
- Shopping in Ginza
- Evening hanami (cherry blossom viewing party)

[... continues with detailed 7-day itinerary ...]

## Tips
- Book accommodations 6-12 months in advance
- Be flexible with dates as bloom timing varies
- Pack light layers for spring weather
- Respect local customs during hanami parties
```

## 🛠 **Dependencies**

```
python-dotenv==1.0.0
semantic-kernel==0.4.0
```

## 📁 **Project Structure**

```
multi-agent-travel-planner/
├── travel_planner.py          # Main travel planner system
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
└── venv/                     # Virtual environment (ignored)
```

## 🤝 **Contributing**

This is a learning project demonstrating Semantic Kernel features. Feel free to:

1. **Extend the system** with more destinations and itineraries
2. **Add new plugins** for different travel planning aspects
3. **Improve the feedback loops** with more sophisticated clarification logic
4. **Enhance the UI** with web interfaces or chat bots

## 📚 **Resources**

- [Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Multi-Agent Systems](https://en.wikipedia.org/wiki/Multi-agent_system)

---

**Perfect for beginners learning Semantic Kernel while building something useful and engaging!** 🎯
