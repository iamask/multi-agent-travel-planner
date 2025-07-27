#!/usr/bin/env python3
"""
Simple Travel Planner System - Multi-Agent System using Semantic Kernel

Features:
- Destination Analyzer Agent: Extracts location, duration, preferences
- Itinerary Builder Agent: Creates day-wise itineraries
- Simple feedback loop for clarifications
- Basic plugins for analysis and itinerary building
"""

import os
import asyncio
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, GroupChatOrchestration, RoundRobinGroupChatManager
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function

class DestinationAnalyzerPlugin:
    """
    Plugin for analyzing travel requests and extracting structured information.
    
    This plugin provides two main functions:
    1. analyze_travel_request: Extracts destination, duration, and purpose from natural language
    2. handle_clarification: Processes clarification requests and updates analysis
    """
    
    def __init__(self):
        # Initialize kernel for this plugin (though not used directly in this implementation)
        self.kernel = Kernel()
    
    @kernel_function(
        description="Analyze travel request and extract key information",
        name="analyze_travel_request"
    )
    def analyze_travel_request(self, user_request: str) -> str:
        """
        Extract destination, duration, and purpose from travel request.
        
        This function uses keyword-based extraction to identify:
        - Destination: Looks for travel keywords like "to", "visit", "go to"
        - Duration: Detects time-related keywords like "week", "day", "month"
        - Purpose: Identifies travel purposes like "cherry blossom", "beach", "business"
        
        Args:
            user_request (str): Natural language travel request from user
            
        Returns:
            str: JSON string containing structured analysis with missing_info field
        """
        print(f"[DEBUG] 🔍 Agent 1: Destination Analyzer (GPT-4o-mini): Starting analysis of: {user_request}")
        
        # Convert to lowercase for consistent keyword matching
        request_lower = user_request.lower()
        
        # Extract destination - look for common travel keywords
        destination = "Unknown"
        
        # Common travel keywords that indicate destinations
        # These keywords help identify where the user wants to travel
        travel_keywords = [
            "to ", "visit ", "go to ", "travel to ", "trip to ", "vacation to ",
            "in ", "at ", "for ", "destination", "place"
        ]
        
        # Look for destination after travel keywords
        # This approach can extract destinations like "Japan" from "Plan a trip to Japan"
        for keyword in travel_keywords:
            if keyword in request_lower:
                # Find the word after the keyword
                parts = request_lower.split(keyword)
                if len(parts) > 1:
                    potential_destination = parts[1].split()[0]  # First word after keyword
                    if potential_destination and len(potential_destination) > 2:
                        destination = potential_destination.title()
                        print(f"[DEBUG] 🎯 Found destination: {destination}")
                        break
        
        # If no destination found with keywords, try to extract any capitalized word
        # This fallback helps catch destinations mentioned without travel keywords
        if destination == "Unknown":
            words = user_request.split()
            for word in words:
                # Look for capitalized words that might be destinations
                # Excludes common words like "the", "and", "for", etc.
                if word[0].isupper() and len(word) > 2 and word.lower() not in ['the', 'and', 'for', 'with', 'from', 'this', 'that']:
                    destination = word
                    print(f"[DEBUG] 🎯 Found destination from capitalized word: {destination}")
                    break
        
        if destination == "Unknown":
            print(f"[DEBUG] ❓ No destination found in request")
        
        # Extract duration using keyword detection
        # Looks for time-related keywords to determine trip length
        duration = None
        if "week" in request_lower:
            duration = "7 days"
            print(f"[DEBUG] ⏰ Found duration: {duration}")
        elif "day" in request_lower:
            duration = "3 days"
            print(f"[DEBUG] ⏰ Found duration: {duration}")
        elif "month" in request_lower:
            duration = "30 days"
            print(f"[DEBUG] ⏰ Found duration: {duration}")
        else:
            print(f"[DEBUG] ❓ No duration found in request")
        
        # Extract purpose/type of travel
        # Identifies the reason for travel to create more relevant itineraries
        purpose = "General Travel"
        if "cherry blossom" in request_lower:
            purpose = "Cherry Blossom Viewing"
        elif "beach" in request_lower:
            purpose = "Beach Vacation"
        elif "business" in request_lower:
            purpose = "Business Trip"
        
        print(f"[DEBUG] 🎯 Found purpose: {purpose}")
        
        # Check for missing information that needs clarification
        # This helps Agent 2 know what information is incomplete
        missing_info = []
        if not duration:
            missing_info.append("duration")
        if destination == "Unknown":
            missing_info.append("destination")
        
        # Create structured analysis result
        # This JSON format allows easy communication between agents
        analysis = {
            "destination": destination,
            "duration": duration,
            "purpose": purpose,
            "missing_info": missing_info
        }
        
        print(f"[DEBUG] 📊 Agent 1: Destination Analyzer (GPT-4o-mini): Final analysis: {analysis}")
        return json.dumps(analysis)
    
    @kernel_function(
        description="Handle user clarifications and update analysis",
        name="handle_clarification"
    )
    def handle_clarification(self, original_analysis: str, user_clarification: str) -> str:
        """
        Update analysis based on user clarification.
        
        This function processes clarification requests from Agent 2 and updates
        the analysis with the provided information. It uses enhanced regex-based
        extraction for more accurate processing.
        
        Args:
            original_analysis (str): JSON string of the original analysis
            user_clarification (str): User's clarification input
            
        Returns:
            str: Updated JSON analysis with resolved missing information
        """
        print(f"[DEBUG] 🔄 Agent 1: Destination Analyzer (GPT-4o-mini) Plugin: handle_clarification called")
        print(f"[DEBUG] 📥 Original analysis: {original_analysis}")
        print(f"[DEBUG] 📥 User clarification: {user_clarification}")
        
        try:
            # Parse the original analysis JSON
            analysis = json.loads(original_analysis)
            clarification_lower = user_clarification.lower()
            
            print(f"[DEBUG] 🔍 Processing clarification: {clarification_lower}")
            
            # Update duration if it was missing and provided in clarification
            if "duration" in analysis.get("missing_info", []):
                print(f"[DEBUG] ⏰ Updating duration from clarification")
                
                # Enhanced duration extraction with specific patterns
                # This handles various ways users might specify duration
                if "7" in clarification_lower and ("day" in clarification_lower or "week" in clarification_lower):
                    analysis["duration"] = "7 days"
                    print(f"[DEBUG] ✅ Set duration to 7 days")
                elif "3" in clarification_lower and "day" in clarification_lower:
                    analysis["duration"] = "3 days"
                    print(f"[DEBUG] ✅ Set duration to 3 days")
                elif "5" in clarification_lower and "day" in clarification_lower:
                    analysis["duration"] = "5 days"
                    print(f"[DEBUG] ✅ Set duration to 5 days")
                elif "10" in clarification_lower and "day" in clarification_lower:
                    analysis["duration"] = "10 days"
                    print(f"[DEBUG] ✅ Set duration to 10 days")
                elif "14" in clarification_lower and ("day" in clarification_lower or "week" in clarification_lower):
                    analysis["duration"] = "14 days"
                    print(f"[DEBUG] ✅ Set duration to 14 days")
                elif "week" in clarification_lower:
                    analysis["duration"] = "7 days"
                    print(f"[DEBUG] ✅ Set duration to 7 days")
                elif "month" in clarification_lower:
                    analysis["duration"] = "30 days"
                    print(f"[DEBUG] ✅ Set duration to 30 days")
                elif "day" in clarification_lower:
                    # Extract number of days from the text using regex
                    # This handles cases like "7 days", "5 days", etc.
                    import re
                    numbers = re.findall(r'\d+', clarification_lower)
                    if numbers:
                        days = numbers[0]
                        analysis["duration"] = f"{days} days"
                        print(f"[DEBUG] ✅ Set duration to {days} days")
                    else:
                        analysis["duration"] = "7 days"  # Default fallback
                        print(f"[DEBUG] ✅ Set duration to 7 days (default)")
                else:
                    analysis["duration"] = "7 days"  # Default fallback
                    print(f"[DEBUG] ✅ Set duration to 7 days (default)")
            
            # Update destination if it was missing and provided in clarification
            if "destination" in analysis.get("missing_info", []):
                print(f"[DEBUG] 🎯 Updating destination from clarification")
                
                # Extract destination from clarification using similar logic to analyze_travel_request
                destination = "Unknown"
                
                # Common travel keywords that indicate destinations
                travel_keywords = [
                    "to ", "visit ", "go to ", "travel to ", "trip to ", "vacation to ",
                    "in ", "at ", "for ", "destination", "place"
                ]
                
                # Look for destination after travel keywords
                for keyword in travel_keywords:
                    if keyword in clarification_lower:
                        # Find the word after the keyword
                        parts = clarification_lower.split(keyword)
                        if len(parts) > 1:
                            potential_destination = parts[1].split()[0]  # First word after keyword
                            if potential_destination and len(potential_destination) > 2:
                                destination = potential_destination.title()
                                print(f"[DEBUG] ✅ Set destination to {destination}")
                                break
                
                # If no destination found with keywords, try to extract any capitalized word
                if destination == "Unknown":
                    words = user_clarification.split()
                    for word in words:
                        # Look for capitalized words that might be destinations
                        if word[0].isupper() and len(word) > 2 and word.lower() not in ['the', 'and', 'for', 'with', 'from', 'this', 'that']:
                            destination = word
                            print(f"[DEBUG] ✅ Set destination to {destination}")
                            break
                
                if destination != "Unknown":
                    analysis["destination"] = destination
            
            # Remove resolved missing info from the missing_info list
            # This helps Agent 2 know that the information is now complete
            resolved_items = []
            for item in analysis.get("missing_info", []):
                if item == "duration" and analysis.get("duration"):
                    resolved_items.append(item)
                    print(f"[DEBUG] ✅ Resolved duration")
                elif item == "destination" and analysis.get("destination") != "Unknown":
                    resolved_items.append(item)
                    print(f"[DEBUG] ✅ Resolved destination")
            
            # Remove resolved items from missing_info list
            for item in resolved_items:
                analysis["missing_info"].remove(item)
            
            print(f"[DEBUG] 📊 Agent 1: Destination Analyzer (GPT-4o-mini): Final updated analysis: {analysis}")
            return json.dumps(analysis)
            
        except json.JSONDecodeError as e:
            print(f"[DEBUG] ❌ Error parsing analysis: {e}")
            return original_analysis

class ItineraryBuilderPlugin:
    """
    Plugin for building travel itineraries based on analyzed travel information.
    
    This plugin provides the main build_itinerary function and several helper
    methods for generating specialized and general itineraries.
    """
    
    def __init__(self):
        # Initialize kernel for this plugin (though not used directly in this implementation)
        self.kernel = Kernel()
    
    @kernel_function(
        description="Build travel itinerary based on analysis",
        name="build_itinerary"
    )
    def build_itinerary(self, analysis: str) -> str:
        """
        Build a simple travel itinerary based on the provided analysis.
        
        This function checks if all required information is available and either:
        1. Creates a complete itinerary if all info is present
        2. Requests clarification if information is missing
        
        Args:
            analysis (str): JSON string containing travel analysis from Agent 1
            
        Returns:
            str: Either a complete itinerary or a clarification request
        """
        print(f"[DEBUG] 📝 Agent 2: Itinerary Builder (GPT-4o-mini): Starting itinerary creation")
        print(f"[DEBUG] 📊 Input analysis: {analysis}")
        
        try:
            # Parse the analysis JSON from Agent 1
            data = json.loads(analysis)
            destination = data.get("destination", "Unknown")
            duration = data.get("duration", "7 days")
            purpose = data.get("purpose", "General Travel")
            missing_info = data.get("missing_info", [])
            
            print(f"[DEBUG] 🎯 Agent 2: Itinerary Builder (GPT-4o-mini): Destination={destination}, Duration={duration}, Purpose={purpose}")
            
            # If missing info, request clarification from Agent 1
            # This ensures we have complete information before creating an itinerary
            if missing_info:
                print(f"[DEBUG] ❓ Agent 2: Itinerary Builder (GPT-4o-mini): Missing info detected: {missing_info}")
                print(f"[DEBUG] ❓ Agent 2: Itinerary Builder (GPT-4o-mini): Asking Agent 1 for clarification")
                return self._request_clarification(missing_info)
            
            # Generate simple itinerary based on available information
            print(f"[DEBUG] 📝 Agent 2: Itinerary Builder (GPT-4o-mini): All info complete, creating itinerary")
            if "Japan" in destination and "Cherry Blossom" in purpose:
                # Specialized itinerary for Japan cherry blossom viewing
                print(f"[DEBUG] 🎯 Agent 2: Itinerary Builder (GPT-4o-mini): Creating Japan cherry blossom itinerary")
                return self._generate_japan_cherry_blossom_itinerary(duration)
            else:
                # General itinerary template for any destination
                print(f"[DEBUG] 🎯 Agent 2: Itinerary Builder (GPT-4o-mini): Creating general itinerary for {destination}")
                return self._generate_general_itinerary(destination, duration, purpose)
                
        except json.JSONDecodeError as e:
            print(f"[DEBUG] ❌ Error parsing analysis: {e}")
            return "Error processing travel request. Please try again."
    
    def _request_clarification(self, missing_info: List[str]) -> str:
        """
        Request clarification for missing information.
        
        This function creates a structured clarification request that Agent 1
        can process to get the missing information.
        
        Args:
            missing_info (List[str]): List of missing information items
            
        Returns:
            str: JSON string containing clarification request
        """
        print(f"[DEBUG] ❓ Agent 2: Itinerary Builder (GPT-4o-mini) Plugin: _request_clarification called")
        print(f"[DEBUG] 📋 Missing info: {missing_info}")
        
        # Create specific questions for each missing piece of information
        questions = []
        
        if "duration" in missing_info:
            questions.append("How many days would you like to spend on this trip?")
            print(f"[DEBUG] ❓ Added duration question")
        if "destination" in missing_info:
            questions.append("Where would you like to travel?")
            print(f"[DEBUG] ❓ Added destination question")
        
        # Create structured clarification request
        # This format allows Agent 1 to understand what information is needed
        result = {
            "needs_clarification": True,
            "questions": questions,
            "missing_info": missing_info
        }
        
        print(f"[DEBUG] 📤 Agent 2: Itinerary Builder (GPT-4o-mini): Clarification request: {result}")
        return json.dumps(result)
    
    def _generate_japan_cherry_blossom_itinerary(self, duration: str) -> str:
        """
        Generate Japan cherry blossom itinerary.
        
        This specialized itinerary is designed for cherry blossom viewing in Japan,
        with specific locations and activities optimized for the cherry blossom season.
        
        Args:
            duration (str): Trip duration (e.g., "7 days")
            
        Returns:
            str: Detailed Japan cherry blossom itinerary
        """
        return f"""
# Japan Cherry Blossom Itinerary ({duration})

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

### Day 3: Day Trip to Kamakura
- Train to Kamakura
- Visit Tsurugaoka Hachimangu Shrine
- See the Great Buddha
- Return to Tokyo

### Day 4: Tokyo to Kyoto
- Shinkansen to Kyoto
- Visit Maruyama Park for cherry blossoms
- Explore Yasaka Shrine
- Traditional kaiseki dinner

### Day 5: Kyoto Highlights
- Visit Kiyomizu-dera Temple
- Walk the Philosopher's Path (famous cherry blossom spot)
- Explore Gion district
- Evening stroll through illuminated blossoms

### Day 6: Day Trip to Nara
- Train to Nara
- Visit Nara Park with deer
- Cherry blossoms at Todai-ji Temple
- Return to Kyoto

### Day 7: Final Day
- Visit Fushimi Inari Shrine
- Final cherry blossom viewing
- Return to Tokyo
- Departure

## Tips
- Book accommodations 6-12 months in advance
- Be flexible with dates as bloom timing varies
- Pack light layers for spring weather
- Respect local customs during hanami parties

*This itinerary is optimized for cherry blossom viewing!*
        """.strip()
    
    def _generate_general_itinerary(self, destination: str, duration: str, purpose: str) -> str:
        """
        Generate a general travel itinerary.
        
        This template provides a flexible framework for any destination,
        with practical advice and structure that can be customized.
        
        Args:
            destination (str): Travel destination
            duration (str): Trip duration (e.g., "7 days")
            purpose (str): Purpose of travel (e.g., "General Travel")
            
        Returns:
            str: General travel itinerary template
        """
        return f"""
# Travel Itinerary: {destination} ({duration})

## Trip Overview
Experience {destination} with this {duration} itinerary for {purpose.lower()} travel.

## Day-by-Day Itinerary

### Day 1: Arrival
- Arrive at destination
- Check into hotel
- Light exploration of the area
- Welcome dinner

### Day 2-{duration.split()[0] if duration else '7'}: Main Activities
- Sightseeing and activities
- Local cuisine experiences
- Cultural activities
- Shopping and exploration

### Final Day: Departure
- Final activities
- Souvenir shopping
- Departure

## Accommodation
- Research hotels in the city center
- Book in advance for better rates
- Consider your budget and preferences

## Transportation
- Research local transportation options
- Consider city passes for attractions
- Plan airport transfers

## Budget Tips
- Research accommodation rates
- Plan for local cuisine experiences
- Include must-see attractions
- Factor in transportation costs

*This is a general framework - customize based on your specific destination and preferences.*
        """.strip()

def get_travel_agents():
    """
    Create simple travel planning agents with kernel and plugins.
    
    This function sets up the multi-agent system by:
    1. Creating a kernel and adding plugins
    2. Creating two specialized agents with specific roles
    3. Configuring agents with proper instructions and kernel integration
    
    Returns:
        List[ChatCompletionAgent]: List of configured agents for the travel planner
    """
    # Create kernel and add plugins
    # The kernel manages the plugins and provides them to agents
    kernel = Kernel()
    
    # Add plugins to kernel
    # These plugins provide the core functionality for travel analysis and itinerary building
    destination_analyzer_plugin = DestinationAnalyzerPlugin()
    itinerary_builder_plugin = ItineraryBuilderPlugin()
    
    # Register plugins with the kernel using descriptive names
    # This allows agents to access plugin functions
    kernel.add_plugin(destination_analyzer_plugin, "DestinationAnalyzer")
    kernel.add_plugin(itinerary_builder_plugin, "ItineraryBuilder")
    
    return [
        # Agent 1: Destination Analyzer - Extracts travel information from user requests
        ChatCompletionAgent(
            name="Agent1_DestinationAnalyzer",
            description="Agent 1: Destination Analyzer (GPT-4o-mini)",
            instructions="""You are Agent 1: Destination Analyzer (GPT-4o-mini). Your role is to:

1. **Use the analyze_travel_request function** to extract destination, duration, and purpose from travel requests
2. **Use the handle_clarification function** when Agent 2 asks for missing information
3. **DO NOT hallucinate** - if information is missing, indicate it in the missing_info field
4. **Provide structured JSON output** for Agent 2 to process

**IMPORTANT: You MUST use the available functions:**
- Use `analyze_travel_request` to analyze the initial request
- Use `handle_clarification` when Agent 2 asks for missing info

**Debug Messages**:
- Start with: "🔍 Agent 1: Destination Analyzer (GPT-4o-mini): Extracted [destination, duration, purpose]"
- If asked for clarification: "🔄 Agent 1: Destination Analyzer (GPT-4o-mini): Processing clarification request from Agent 2"
- After user clarification: "✅ Agent 1: Destination Analyzer (GPT-4o-mini): Updated analysis with user clarification"

**Focus on**:
- Destination (where they want to go)
- Duration (how long the trip should be)
- Purpose (why they're traveling - vacation, business, etc.)
- Missing information that needs clarification

Keep your analysis simple and focused on the essential travel planning elements.""",
            service=OpenAIChatCompletion(ai_model_id="gpt-4o-mini"),
            kernel=kernel,  # Connect agent to kernel for plugin access
        ),
        # Agent 2: Itinerary Builder - Creates travel itineraries based on Agent 1's analysis
        ChatCompletionAgent(
            name="Agent2_ItineraryBuilder", 
            description="Agent 2: Itinerary Builder (GPT-4o-mini)",
            instructions="""You are Agent 2: Itinerary Builder (GPT-4o-mini). Your role is to:

1. **Use the build_itinerary function** to create itineraries based on Agent 1's analysis
2. **Check for missing information** and ask Agent 1 for clarification if needed
3. **Only create itineraries** when all required information is available
4. **Provide practical, day-by-day plans**

**IMPORTANT: You MUST use the available functions:**
- Use `build_itinerary` to process Agent 1's analysis and create itineraries

**Debug Messages**:
- If missing info: "❓ Agent 2: Itinerary Builder (GPT-4o-mini): Missing [missing_info], requesting clarification from Agent 1"
- When creating itinerary: "📝 Agent 2: Itinerary Builder (GPT-4o-mini): Creating itinerary with complete information"

**Focus on**:
- Day-by-day structure with clear activities
- Practical details like accommodation and transportation
- Budget-friendly and luxury options
- Local experiences and cultural activities

Keep your itineraries simple, practical, and ready to use.""",
            service=OpenAIChatCompletion(ai_model_id="gpt-4o-mini"),
            kernel=kernel,  # Connect agent to kernel for plugin access
        ),
    ]

async def run_simple_travel_planner(user_request: str):
    """
    Run the simple travel planner with proper feedback loop.
    
    This function orchestrates the multi-agent travel planning process:
    1. Creates agents with kernel and plugins
    2. Sets up group chat for agent collaboration
    3. Sends the user request to the agent group
    4. Returns the final travel itinerary
    
    Args:
        user_request (str): Natural language travel request from user
        
    Returns:
        str: Final travel itinerary or None if failed
    """
    print(f"✈️ Travel Request: {user_request}")
    print("🤖 Initializing Simple Travel Planner...")
    
    # Create agents with kernel and plugins
    # These agents will collaborate to analyze the request and create an itinerary
    agents = get_travel_agents()
    print(f"[DEBUG] 🤖 Created {len(agents)} agents: {[agent.name for agent in agents]}")
    
    # Create group chat for agent collaboration
    # RoundRobinGroupChatManager ensures agents take turns in the conversation
    group_chat = GroupChatOrchestration(
        members=agents,
        manager=RoundRobinGroupChatManager(max_rounds=5),  # Increased for feedback loops
    )
    print(f"[DEBUG] 💬 Created Agent group chat with max_rounds=5")
    
    # Initialize runtime for agent execution
    # This manages the execution environment for the agents
    runtime = InProcessRuntime()
    runtime.start()
    print(f"[DEBUG] ⚡ Runtime started")
    
    print("🚀 Starting Travel Planner...")
    print("=" * 50)
    
    try:
        # Send the travel request to the agent group
        # The agents will collaborate to analyze and create an itinerary
        print(f"[DEBUG] 📤 Sending task to group chat: {user_request}")
        result = await group_chat.invoke(
            task=f"""Please help me plan a trip: "{user_request}"

**IMPORTANT: Use the available functions and follow the proper feedback loop**

**Step-by-Step Process**:
1. **Agent 1: Destination Analyzer (GPT-4o-mini)**: Use `analyze_travel_request` function to extract destination, duration, and purpose
2. **Agent 2: Itinerary Builder (GPT-4o-mini)**: Use `build_itinerary` function to check if information is missing
3. **If missing info**: Agent 2 will ask Agent 1 for clarification
4. **Agent 1**: If Agent 2 asks for missing info, use `handle_clarification` function to process the clarification
5. **Agent 2**: Create the final itinerary only when all info is complete

**CRITICAL: Use the available functions:**
- Agent 1: Use `analyze_travel_request` and `handle_clarification` functions
- Agent 2: Use `build_itinerary` function

**Proper Feedback Loop**:
- Agent 1 analyzes the request and returns analysis with missing_info if any
- Agent 2 checks the analysis and requests clarification from Agent 1 if info is missing
- Agent 1 processes the clarification request using `handle_clarification` function
- Agent 2 creates the final itinerary when all information is complete

**Debug Messages to Show**:
- "🔍 Agent 1: Destination Analyzer (GPT-4o-mini): Extracted [destination, duration, purpose]"
- "❓ Agent 2: Itinerary Builder (GPT-4o-mini): Missing [missing_info], requesting clarification from Agent 1"
- "🔄 Agent 1: Destination Analyzer (GPT-4o-mini): Processing clarification request from Agent 2"
- "✅ Agent 1: Destination Analyzer (GPT-4o-mini): Updated analysis with user clarification"
- "📝 Agent 2: Itinerary Builder (GPT-4o-mini): Creating itinerary with complete information"

**Key Rules**:
- Agent 1 should NOT hallucinate missing information
- Agent 1 should indicate missing info in the missing_info field
- Agent 2 should request clarification from Agent 1 when info is missing
- Agent 1 should use `handle_clarification` function to process clarification requests
- Only proceed with itinerary creation when all required information is available
- Show debug messages for each step

**Expected Output**:
- Clear day-by-day travel itinerary
- Practical activities and recommendations
- Accommodation and transportation tips
- Budget considerations

Keep it simple and practical!""",
            runtime=runtime,
        )
        
        # Get the final result from the agent collaboration
        print(f"[DEBUG] 📥 Received result from group chat")
        value = await result.get()
        print(f"[DEBUG] 📋 Final value: {value}")
        
        print("=" * 50)
        print("✅ Final Travel Itinerary:")
        print(f"📝 {value}")
        
        return value
        
    except Exception as e:
        # Handle any errors during the travel planning process
        print(f"❌ Error: {e}")
        print(f"[DEBUG] ❌ Exception details: {type(e).__name__}: {str(e)}")
        return None
    
    finally:
        # Clean up runtime resources
        print(f"[DEBUG] 🛑 Stopping runtime")
        await runtime.stop_when_idle()

async def interactive_travel_session():
    """
    Run an interactive travel planning session.
    
    This function provides a command-line interface for users to:
    1. Enter travel requests
    2. Get travel itineraries
    3. Exit the application
    
    The session continues until the user types 'quit' or interrupts with Ctrl+C.
    """
    print("✈️ Simple Travel Planner")
    print("=" * 50)
    print("Ask me to plan any trip!")
    print("Type 'quit' to exit.")
    print("=" * 50)
    
    while True:
        try:
            # Get travel request from user
            user_request = input("\n✈️ Your travel request: ").strip()
            print(f"[DEBUG] 👤 User input received: '{user_request}'")
            
            # Check for exit commands
            if user_request.lower() in ['quit', 'exit', 'q']:
                print("[DEBUG] 👋 User requested to quit")
                print("👋 Thank you for using the Travel Planner!")
                break
            
            # Validate user input
            if not user_request:
                print("[DEBUG] ❌ Empty user input")
                print("❌ Please enter a valid travel request.")
                continue
            
            # Process the travel request using the multi-agent system
            print(f"[DEBUG] 🚀 Starting travel planning for: '{user_request}'")
            print("\n🔄 Planning your trip...")
            result = await run_simple_travel_planner(user_request)
            
            # Handle the result
            if result:
                print(f"[DEBUG] ✅ Travel planning successful")
                print("\n✅ Travel planning completed!")
            else:
                print(f"[DEBUG] ❌ Travel planning failed")
                print("\n❌ Travel planning failed. Please try again.")
                
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print(f"[DEBUG] ⌨️ Keyboard interrupt received")
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            # Handle any unexpected errors
            print(f"[DEBUG] ❌ Exception in interactive session: {type(e).__name__}: {str(e)}")
            print(f"\n❌ Error: {e}")
            print("Please try again.")

async def main():
    """
    Main function to demonstrate the Simple Travel Planner.
    
    This function:
    1. Loads environment variables
    2. Validates OpenAI API key
    3. Shows example requests
    4. Starts the interactive session
    """
    print("🚀 Starting Simple Travel Planner System")
    print("[DEBUG] 🚀 Main function started")
    
    # Load environment variables from .env file
    # This includes the OpenAI API key needed for the agents
    load_dotenv()
    print("[DEBUG] 📄 Environment variables loaded")
    
    # Check for OpenAI API key
    # The API key is required for the GPT-4o-mini model used by the agents
    if not os.getenv("OPENAI_API_KEY"):
        print("[DEBUG] ❌ OpenAI API key not found")
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    print("[DEBUG] ✅ OpenAI API key found")
    print("✅ OpenAI API key loaded from .env file.")
    
    # Example travel requests for user reference
    # These show the types of requests the system can handle
    example_requests = [
        "Plan a trip to Japan for cherry blossoms.",
        "I want to visit Paris for 5 days.",
        "Plan a beach vacation in Bali.",
        "Create an itinerary for a business trip to New York."
    ]
    
    print("\n📋 Example travel requests you can try:")
    for i, request in enumerate(example_requests, 1):
        print(f"{i}. {request}")
    
    # Start the interactive session
    # This is where users can interact with the travel planner
    print("\n🎯 Starting interactive mode...")
    print("[DEBUG] 🎯 Calling interactive_travel_session")
    await interactive_travel_session()
    print("[DEBUG] 🏁 Main function completed")

if __name__ == "__main__":
    # Run the main function using asyncio
    # This starts the travel planner system
    asyncio.run(main()) 