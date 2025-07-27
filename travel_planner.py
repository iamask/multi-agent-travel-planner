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
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

# Pydantic models for structured output
class TravelAnalysis(KernelBaseModel):
    """Structured output for travel request analysis."""
    destination: str
    duration: str | None
    purpose: str
    missing_info: List[str]

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
    async def analyze_travel_request(self, user_request: str) -> str:
        """
        Extract destination, duration, and purpose from travel request using LLM.
        
        This function uses LLM for natural language understanding to identify:
        - Destination: Where the user wants to travel
        - Duration: How long the trip should be
        - Purpose: Why they're traveling (vacation, business, etc.)
        
        Args:
            user_request (str): Natural language travel request from user
            
        Returns:
            str: JSON string containing structured analysis with missing_info field
        """
        print(f"[DEBUG] 🔍 Agent 1: Destination Analyzer (GPT-4o-mini): Starting LLM analysis of: {user_request}")
        print(f"[DEBUG] 🔍 Agent 1: This function should ONLY analyze, NOT call handle_clarification")
        
        # Create LLM service for analysis
        llm_service = OpenAIChatCompletion(ai_model_id="gpt-4o-mini")
        
        # Craft a detailed prompt for LLM extraction
        prompt = f"""
        Analyze this travel request and extract key information: "{user_request}"
        
        Extract the following information:
        1. **Destination**: Where they want to travel (city, country, region)
        2. **Duration**: How long the trip should be (e.g., "7 days", "2 weeks", "1 month")
        3. **Purpose**: Why they're traveling (e.g., "vacation", "business", "cherry blossom viewing", "beach vacation")
        
        Return ONLY a valid JSON object with these fields:
        - destination: string (use "Unknown" if not found)
        - duration: string (use null if not found)
        - purpose: string (default to "General Travel" if not specified)
        - missing_info: array of strings (list what's missing: "destination", "duration", etc.)
        
        Examples:
        - "Plan a trip to Japan for cherry blossoms" → {{"destination": "Japan", "duration": null, "purpose": "Cherry Blossom Viewing", "missing_info": ["duration"]}}
        - "I want to visit Paris for 5 days" → {{"destination": "Paris", "duration": "5 days", "purpose": "General Travel", "missing_info": []}}
        - "Plan a beach vacation in Bali" → {{"destination": "Bali", "duration": null, "purpose": "Beach Vacation", "missing_info": ["duration"]}}
        
        Return ONLY the JSON, no other text.
        """
        
        try:
            # Create settings for the LLM request with structured output
            from semantic_kernel.connectors.ai.open_ai import OpenAIPromptExecutionSettings
            
            settings = OpenAIPromptExecutionSettings(
                max_tokens=200,
                temperature=0.1,  # Low temperature for more consistent output
                function_choice_behavior=FunctionChoiceBehavior.Auto(),
                response_format=TravelAnalysis  # Use Pydantic model for structured output
            )
            
            # Get LLM response using the correct method
            response = await llm_service.get_text_content(prompt, settings)
            llm_result = response.text.strip()
            
            print(f"[DEBUG] 🤖 LLM Response: {llm_result}")
            
            # Parse structured response (should be valid due to response_format)
            analysis = json.loads(llm_result)
            
            # Validate and clean the response
            if "destination" not in analysis:
                analysis["destination"] = "Unknown"
            if "duration" not in analysis:
                analysis["duration"] = None
            if "purpose" not in analysis:
                analysis["purpose"] = "General Travel"
            if "missing_info" not in analysis:
                analysis["missing_info"] = []
            
            # Ensure missing_info is properly populated
            missing_info = []
            if not analysis.get("duration"):
                missing_info.append("duration")
            if analysis.get("destination") == "Unknown":
                missing_info.append("destination")
            analysis["missing_info"] = missing_info
            
            print(f"[DEBUG] 📊 Agent 1: Destination Analyzer (GPT-4o-mini): LLM analysis: {analysis}")
            print(f"[DEBUG] ✅ Agent 1: Analysis complete, returning to Agent 2 for processing")
            return json.dumps(analysis)
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            print(f"[DEBUG] ❌ LLM parsing error: {e}")
            print(f"[DEBUG] ❌ Agent 1: Destination Analyzer failed to process request")
            
            # Return error when LLM fails - no fallback
            return json.dumps({
                "destination": "Unknown",
                "duration": None,
                "purpose": "General Travel",
                "missing_info": ["destination", "duration"],
                "error": f"Agent 1 failed to analyze request: {str(e)}"
            })
    

    
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
        print(f"[DEBUG] 🔍 This should only be called when Agent 2 requests clarification")
        
        try:
            # Parse the original analysis JSON
            analysis = json.loads(original_analysis)
            clarification_lower = user_clarification.lower()
            
            print(f"[DEBUG] 🔍 Processing clarification: {clarification_lower}")
            
            # Update duration if it was missing and provided in clarification
            if "duration" in analysis.get("missing_info", []):
                print(f"[DEBUG] ⏰ Updating duration from clarification")
                
                # Simple duration extraction - use default if not specified
                import re
                numbers = re.findall(r'\d+', clarification_lower)
                if numbers and "day" in clarification_lower:
                    days = numbers[0]
                    analysis["duration"] = f"{days} days"
                    print(f"[DEBUG] ✅ Set duration to {days} days")
                else:
                    analysis["duration"] = "7 days"  # Default fallback
                    print(f"[DEBUG] ✅ Set duration to 7 days (default)")
            
            # Update destination if it was missing and provided in clarification
            if "destination" in analysis.get("missing_info", []):
                print(f"[DEBUG] 🎯 Updating destination from clarification")
                
                # Extract destination from clarification using generic logic
                destination = "Unknown"
                
                # Generic travel keywords that indicate destinations
                travel_keywords = [
                    "to ", "visit ", "go to ", "travel to ", "trip to ", "vacation to ",
                    "in ", "at ", "for ", "destination", "place", "want to go to"
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
                        if word[0].isupper() and len(word) > 2 and word.lower() not in ['the', 'and', 'for', 'with', 'from', 'this', 'that', 'would', 'like', 'want']:
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
            
            # Check if Agent 1 failed
            if "error" in data:
                print(f"[DEBUG] ❌ Agent 2: Itinerary Builder (GPT-4o-mini): Agent 1 failed: {data.get('error')}")
                return f"❌ Travel planning failed: {data.get('error')}. Please try again."
            
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
                print(f"[DEBUG] 🔄 Agent 2: This is the CORRECT flow - Agent 2 requesting clarification from Agent 1")
                return self._request_clarification(missing_info)
            
            # Generate simple itinerary based on available information
            print(f"[DEBUG] 📝 Agent 2: Itinerary Builder (GPT-4o-mini): All info complete, creating itinerary")
            # Use general itinerary template for any destination
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
        # Extract number of days for dynamic day planning
        days = 7  # Default
        if duration:
            import re
            day_match = re.search(r'(\d+)', duration)
            if day_match:
                days = int(day_match.group(1))
        
        # Generate dynamic day structure
        day_activities = ""
        for day in range(2, days):
            day_activities += f"### Day {day}: Exploration\n"
            day_activities += "- Sightseeing and activities\n"
            day_activities += "- Local cuisine experiences\n"
            day_activities += "- Cultural activities\n"
            day_activities += "- Shopping and exploration\n\n"
        
        return f"""
# Travel Itinerary: {destination} ({duration})

## Trip Overview
Experience {destination} with this {duration} itinerary for {purpose.lower()} travel.

## Day-by-Day Itinerary

### Day 1: Arrival
- Arrive at {destination}
- Check into hotel
- Light exploration of the area
- Welcome dinner

{day_activities}### Day {days}: Departure
- Final activities
- Souvenir shopping
- Departure

## Accommodation
- Research hotels in the city center of {destination}
- Book in advance for better rates
- Consider your budget and preferences

## Transportation
- Research local transportation options in {destination}
- Consider city passes for attractions
- Plan airport transfers

## Budget Tips
- Research accommodation rates in {destination}
- Plan for local cuisine experiences
- Include must-see attractions
- Factor in transportation costs

## Travel Tips for {destination}
- Research local customs and culture
- Learn basic phrases in the local language
- Check visa requirements if needed
- Pack according to the local climate

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
2. **Use the handle_clarification function** ONLY when Agent 2 asks for missing information
3. **DO NOT call handle_clarification directly** - only Agent 2 should request clarifications
4. **DO NOT hallucinate** - if information is missing, indicate it in the missing_info field
5. **Provide structured JSON output** for Agent 2 to process

**IMPORTANT: You MUST use the available functions:**
- Use `analyze_travel_request` to analyze the initial request
- Use `handle_clarification` ONLY when Agent 2 asks for missing info

**Debug Messages**:
- Start with: "🔍 Agent 1: Destination Analyzer (GPT-4o-mini): Extracted [destination, duration, purpose]"
- If asked for clarification: "🔄 Agent 1: Destination Analyzer (GPT-4o-mini): Processing clarification request from Agent 2"
- After user clarification: "✅ Agent 1: Destination Analyzer (GPT-4o-mini): Updated analysis with user clarification"

**Focus on**:
- Destination (where they want to go)
- Duration (how long the trip should be)
- Purpose (why they're traveling - vacation, business, etc.)
- Missing information that needs clarification

**CRITICAL: Do NOT call handle_clarification directly. Only Agent 2 should request clarifications.**

Keep your analysis simple and focused on the essential travel planning elements.""",
            service=OpenAIChatCompletion(
                ai_model_id="gpt-4o-mini"
            ),
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
4. **Return the actual itinerary content** from the build_itinerary function

**IMPORTANT: You MUST use the available functions:**
- Use `build_itinerary` to process Agent 1's analysis and create itineraries
- **DO NOT add extra text or explanations** - just return the itinerary content

**Debug Messages**:
- If missing info: "❓ Agent 2: Itinerary Builder (GPT-4o-mini): Missing [missing_info], requesting clarification from Agent 1"
- When creating itinerary: "📝 Agent 2: Itinerary Builder (GPT-4o-mini): Creating itinerary with complete information"

**Focus on**:
- Day-by-day structure with clear activities
- Practical details like accommodation and transportation
- Budget-friendly and luxury options
- Local experiences and cultural activities

**CRITICAL: Return only the itinerary content, no additional text or explanations.**""",
            service=OpenAIChatCompletion(
                ai_model_id="gpt-4o-mini"
            ),
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

**IMPORTANT: Follow the EXACT coordination flow - Agent 1 analyzes, Agent 2 requests clarifications**

**EXACT Step-by-Step Process**:
1. **Agent 1: Destination Analyzer (GPT-4o-mini)**: Use `analyze_travel_request` function to extract destination, duration, and purpose
2. **Agent 2: Itinerary Builder (GPT-4o-mini)**: Use `build_itinerary` function to check if information is missing
3. **If missing info**: Agent 2 will ask Agent 1 for clarification
4. **Agent 1**: If Agent 2 asks for missing info, use `handle_clarification` function to process the clarification
5. **Agent 2**: Create the final itinerary only when all info is complete

**CRITICAL: Use the available functions:**
- Agent 1: Use `analyze_travel_request` and `handle_clarification` functions
- Agent 2: Use `build_itinerary` function

**EXACT Coordination Flow**:
- Agent 1 analyzes the request and returns analysis with missing_info if any
- Agent 2 checks the analysis and requests clarification from Agent 1 if info is missing
- Agent 1 processes the clarification request using `handle_clarification` function ONLY when Agent 2 asks
- Agent 2 creates the final itinerary when all information is complete

**CRITICAL RULES**:
- Agent 1 should NOT call handle_clarification directly
- Agent 1 should NOT hallucinate missing information
- Agent 1 should indicate missing info in the missing_info field
- Agent 2 should request clarification from Agent 1 when info is missing
- Agent 1 should use `handle_clarification` function to process clarification requests
- Only proceed with itinerary creation when all required information is available

**Debug Messages to Show**:
- "🔍 Agent 1: Destination Analyzer (GPT-4o-mini): Extracted [destination, duration, purpose]"
- "❓ Agent 2: Itinerary Builder (GPT-4o-mini): Missing [missing_info], requesting clarification from Agent 1"
- "🔄 Agent 1: Destination Analyzer (GPT-4o-mini): Processing clarification request from Agent 2"
- "✅ Agent 1: Destination Analyzer (GPT-4o-mini): Updated analysis with user clarification"
- "📝 Agent 2: Itinerary Builder (GPT-4o-mini): Creating itinerary with complete information"

**Expected Output**:
- Clear day-by-day travel itinerary with actual content
- Practical activities and recommendations
- Accommodation and transportation tips
- Budget considerations

**CRITICAL: Agent 2 must return the actual itinerary content, not just a message saying the itinerary is ready.**

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