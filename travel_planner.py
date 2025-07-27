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
    """Simple plugin for analyzing travel requests."""
    
    def __init__(self):
        self.kernel = Kernel()
    
    @kernel_function(
        description="Analyze travel request and extract key information",
        name="analyze_travel_request"
    )
    def analyze_travel_request(self, user_request: str) -> str:
        """Extract destination, duration, and purpose from travel request."""
        print(f"[DEBUG] 🔍 Agent 1: Destination Analyzer (GPT-4o-mini): Starting analysis of: {user_request}")
        
        # Simple extraction logic
        request_lower = user_request.lower()
        
        # Extract destination - look for common travel keywords
        destination = "Unknown"
        
        # Common travel keywords that indicate destinations
        travel_keywords = [
            "to ", "visit ", "go to ", "travel to ", "trip to ", "vacation to ",
            "in ", "at ", "for ", "destination", "place"
        ]
        
        # Look for destination after travel keywords
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
        if destination == "Unknown":
            words = user_request.split()
            for word in words:
                # Look for capitalized words that might be destinations
                if word[0].isupper() and len(word) > 2 and word.lower() not in ['the', 'and', 'for', 'with', 'from', 'this', 'that']:
                    destination = word
                    print(f"[DEBUG] 🎯 Found destination from capitalized word: {destination}")
                    break
        
        if destination == "Unknown":
            print(f"[DEBUG] ❓ No destination found in request")
        
        # Extract duration
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
        
        # Extract purpose
        purpose = "General Travel"
        if "cherry blossom" in request_lower:
            purpose = "Cherry Blossom Viewing"
        elif "beach" in request_lower:
            purpose = "Beach Vacation"
        elif "business" in request_lower:
            purpose = "Business Trip"
        
        print(f"[DEBUG] 🎯 Found purpose: {purpose}")
        
        # Check for missing info
        missing_info = []
        if not duration:
            missing_info.append("duration")
        if destination == "Unknown":
            missing_info.append("destination")
        
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
        """Update analysis based on user clarification."""
        print(f"[DEBUG] 🔄 Agent 1: Destination Analyzer (GPT-4o-mini) Plugin: handle_clarification called")
        print(f"[DEBUG] 📥 Original analysis: {original_analysis}")
        print(f"[DEBUG] 📥 User clarification: {user_clarification}")
        
        try:
            analysis = json.loads(original_analysis)
            clarification_lower = user_clarification.lower()
            
            print(f"[DEBUG] 🔍 Processing clarification: {clarification_lower}")
            
            # Update duration if provided
            if "duration" in analysis.get("missing_info", []):
                print(f"[DEBUG] ⏰ Updating duration from clarification")
                
                # Look for specific duration patterns
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
                    # Extract number of days from the text
                    import re
                    numbers = re.findall(r'\d+', clarification_lower)
                    if numbers:
                        days = numbers[0]
                        analysis["duration"] = f"{days} days"
                        print(f"[DEBUG] ✅ Set duration to {days} days")
                    else:
                        analysis["duration"] = "7 days"  # Default
                        print(f"[DEBUG] ✅ Set duration to 7 days (default)")
                else:
                    analysis["duration"] = "7 days"  # Default
                    print(f"[DEBUG] ✅ Set duration to 7 days (default)")
            
            # Update destination if provided
            if "destination" in analysis.get("missing_info", []):
                print(f"[DEBUG] 🎯 Updating destination from clarification")
                
                # Extract destination from clarification using similar logic
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
            
            # Remove resolved missing info
            resolved_items = []
            for item in analysis.get("missing_info", []):
                if item == "duration" and analysis.get("duration"):
                    resolved_items.append(item)
                    print(f"[DEBUG] ✅ Resolved duration")
                elif item == "destination" and analysis.get("destination") != "Unknown":
                    resolved_items.append(item)
                    print(f"[DEBUG] ✅ Resolved destination")
            
            for item in resolved_items:
                analysis["missing_info"].remove(item)
            
            print(f"[DEBUG] 📊 Agent 1: Destination Analyzer (GPT-4o-mini): Final updated analysis: {analysis}")
            return json.dumps(analysis)
            
        except json.JSONDecodeError as e:
            print(f"[DEBUG] ❌ Error parsing analysis: {e}")
            return original_analysis

class ItineraryBuilderPlugin:
    """Simple plugin for building travel itineraries."""
    
    def __init__(self):
        self.kernel = Kernel()
    
    @kernel_function(
        description="Build travel itinerary based on analysis",
        name="build_itinerary"
    )
    def build_itinerary(self, analysis: str) -> str:
        """Build a simple travel itinerary."""
        print(f"[DEBUG] 📝 Agent 2: Itinerary Builder (GPT-4o-mini): Starting itinerary creation")
        print(f"[DEBUG] 📊 Input analysis: {analysis}")
        
        try:
            data = json.loads(analysis)
            destination = data.get("destination", "Unknown")
            duration = data.get("duration", "7 days")
            purpose = data.get("purpose", "General Travel")
            missing_info = data.get("missing_info", [])
            
            print(f"[DEBUG] 🎯 Agent 2: Itinerary Builder (GPT-4o-mini): Destination={destination}, Duration={duration}, Purpose={purpose}")
            
            # If missing info, request clarification
            if missing_info:
                print(f"[DEBUG] ❓ Agent 2: Itinerary Builder (GPT-4o-mini): Missing info detected: {missing_info}")
                print(f"[DEBUG] ❓ Agent 2: Itinerary Builder (GPT-4o-mini): Asking Agent 1 for clarification")
                return self._request_clarification(missing_info)
            
            # Generate simple itinerary
            print(f"[DEBUG] 📝 Agent 2: Itinerary Builder (GPT-4o-mini): All info complete, creating itinerary")
            if "Japan" in destination and "Cherry Blossom" in purpose:
                print(f"[DEBUG] 🎯 Agent 2: Itinerary Builder (GPT-4o-mini): Creating Japan cherry blossom itinerary")
                return self._generate_japan_cherry_blossom_itinerary(duration)
            else:
                print(f"[DEBUG] 🎯 Agent 2: Itinerary Builder (GPT-4o-mini): Creating general itinerary for {destination}")
                return self._generate_general_itinerary(destination, duration, purpose)
                
        except json.JSONDecodeError as e:
            print(f"[DEBUG] ❌ Error parsing analysis: {e}")
            return "Error processing travel request. Please try again."
    
    def _request_clarification(self, missing_info: List[str]) -> str:
        """Request clarification for missing information."""
        print(f"[DEBUG] ❓ Agent 2: Itinerary Builder (GPT-4o-mini) Plugin: _request_clarification called")
        print(f"[DEBUG] 📋 Missing info: {missing_info}")
        
        questions = []
        
        if "duration" in missing_info:
            questions.append("How many days would you like to spend on this trip?")
            print(f"[DEBUG] ❓ Added duration question")
        if "destination" in missing_info:
            questions.append("Where would you like to travel?")
            print(f"[DEBUG] ❓ Added destination question")
        
        result = {
            "needs_clarification": True,
            "questions": questions,
            "missing_info": missing_info
        }
        
        print(f"[DEBUG] 📤 Agent 2: Itinerary Builder (GPT-4o-mini): Clarification request: {result}")
        return json.dumps(result)
    
    def _generate_japan_cherry_blossom_itinerary(self, duration: str) -> str:
        """Generate Japan cherry blossom itinerary."""
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
        """Generate a general travel itinerary."""
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
    """Create simple travel planning agents."""
    # Create kernel and add plugins
    kernel = Kernel()
    
    # Add plugins to kernel
    destination_analyzer_plugin = DestinationAnalyzerPlugin()
    itinerary_builder_plugin = ItineraryBuilderPlugin()
    
    kernel.add_plugin(destination_analyzer_plugin, "DestinationAnalyzer")
    kernel.add_plugin(itinerary_builder_plugin, "ItineraryBuilder")
    
    return [
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
            kernel=kernel,
        ),
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
            kernel=kernel,
        ),
    ]

async def run_simple_travel_planner(user_request: str):
    """Run the simple travel planner with proper feedback loop."""
    print(f"✈️ Travel Request: {user_request}")
    print("🤖 Initializing Simple Travel Planner...")
    
    # Create agents
    agents = get_travel_agents()
    print(f"[DEBUG] 🤖 Created {len(agents)} agents: {[agent.name for agent in agents]}")
    
    # Create group chat
    group_chat = GroupChatOrchestration(
        members=agents,
        manager=RoundRobinGroupChatManager(max_rounds=5),  # Increased for feedback loops
    )
    print(f"[DEBUG] 💬 Created Agent group chat with max_rounds=5")
    
    # Initialize runtime
    runtime = InProcessRuntime()
    runtime.start()
    print(f"[DEBUG] ⚡ Runtime started")
    
    print("🚀 Starting Travel Planner...")
    print("=" * 50)
    
    try:
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
        
        print(f"[DEBUG] 📥 Received result from group chat")
        value = await result.get()
        print(f"[DEBUG] 📋 Final value: {value}")
        
        print("=" * 50)
        print("✅ Final Travel Itinerary:")
        print(f"📝 {value}")
        
        return value
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"[DEBUG] ❌ Exception details: {type(e).__name__}: {str(e)}")
        return None
    
    finally:
        print(f"[DEBUG] 🛑 Stopping runtime")
        await runtime.stop_when_idle()

async def interactive_travel_session():
    """Run an interactive travel planning session."""
    print("✈️ Simple Travel Planner")
    print("=" * 50)
    print("Ask me to plan any trip!")
    print("Type 'quit' to exit.")
    print("=" * 50)
    
    while True:
        try:
            user_request = input("\n✈️ Your travel request: ").strip()
            print(f"[DEBUG] 👤 User input received: '{user_request}'")
            
            if user_request.lower() in ['quit', 'exit', 'q']:
                print("[DEBUG] 👋 User requested to quit")
                print("👋 Thank you for using the Travel Planner!")
                break
            
            if not user_request:
                print("[DEBUG] ❌ Empty user input")
                print("❌ Please enter a valid travel request.")
                continue
            
            print(f"[DEBUG] 🚀 Starting travel planning for: '{user_request}'")
            print("\n🔄 Planning your trip...")
            result = await run_simple_travel_planner(user_request)
            
            if result:
                print(f"[DEBUG] ✅ Travel planning successful")
                print("\n✅ Travel planning completed!")
            else:
                print(f"[DEBUG] ❌ Travel planning failed")
                print("\n❌ Travel planning failed. Please try again.")
                
        except KeyboardInterrupt:
            print(f"[DEBUG] ⌨️ Keyboard interrupt received")
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"[DEBUG] ❌ Exception in interactive session: {type(e).__name__}: {str(e)}")
            print(f"\n❌ Error: {e}")
            print("Please try again.")

async def main():
    """Main function to demonstrate the Simple Travel Planner."""
    print("🚀 Starting Simple Travel Planner System")
    print("[DEBUG] 🚀 Main function started")
    
    # Load environment variables
    load_dotenv()
    print("[DEBUG] 📄 Environment variables loaded")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("[DEBUG] ❌ OpenAI API key not found")
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    print("[DEBUG] ✅ OpenAI API key found")
    print("✅ OpenAI API key loaded from .env file.")
    
    # Example travel requests
    example_requests = [
        "Plan a trip to Japan for cherry blossoms.",
        "I want to visit Paris for 5 days.",
        "Plan a beach vacation in Bali.",
        "Create an itinerary for a business trip to New York."
    ]
    
    print("\n📋 Example travel requests you can try:")
    for i, request in enumerate(example_requests, 1):
        print(f"{i}. {request}")
    
    print("\n🎯 Starting interactive mode...")
    print("[DEBUG] 🎯 Calling interactive_travel_session")
    await interactive_travel_session()
    print("[DEBUG] 🏁 Main function completed")

if __name__ == "__main__":
    asyncio.run(main()) 