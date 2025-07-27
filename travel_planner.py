#!/usr/bin/env python3
"""
Multi-Agent Travel Planner System using Semantic Kernel

This is a true multi-agent system with two specialized agents:

1. **Agent 1 (Destination Analyzer)**: 
   - Analyzes user input with LLM
   - Extracts structured information (destination, duration, purpose)
   - Returns JSON with missing_info field for Agent 2 to check

2. **Agent 2 (Itinerary Builder)**:
   - Generates itineraries using structured output from Agent 1
   - Uses LLM to create destination-specific, dynamic itineraries
   - Can reach back to Agent 1 if information is missing

**Multi-Agent Coordination Flow:**
- Agent 1 analyzes user input → returns structured JSON
- Agent 2 checks structured output → generates itinerary OR requests clarification
- Agent 1 processes clarification → updates analysis with defaults
- Agent 2 creates final LLM-generated itinerary

Key Features:
- LLM-powered analysis with structured output (Agent 1)
- LLM-powered itinerary generation (Agent 2)
- Intelligent feedback loop between agents
- No hallucination - proper coordination for missing info
- Type-safe communication with Pydantic models
"""

import os
import asyncio
import json
from typing import List
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, GroupChatOrchestration, RoundRobinGroupChatManager
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIPromptExecutionSettings
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

# Pydantic models for structured output
class TravelAnalysis(KernelBaseModel):
    """
    Structured output for travel request analysis.
    
    This Pydantic model defines the exact structure that the LLM must return,
    ensuring type safety and preventing malformed responses.
    
    Fields:
        destination (str): Where the user wants to travel (or "Unknown" if not found)
        duration (str | None): How long the trip should be (or None if not found)
        purpose (str): Why they're traveling (e.g., "vacation", "business")
        missing_info (List[str]): List of missing information items for Agent 2 to check
    """
    destination: str
    duration: str | None
    purpose: str
    missing_info: List[str]

class DestinationAnalyzerPlugin:
    """
    Plugin for Agent 1: Destination Analyzer
    
    This plugin provides the core functionality for Agent 1 in the multi-agent system:
    1. analyze_travel_request: Analyzes user input with LLM and extracts structured information
    2. handle_clarification: Processes clarification requests from Agent 2 when information is missing
    
    **Agent 1's Role in Multi-Agent System:**
    - Analyzes user input with LLM
    - Extracts destination, duration, and purpose from natural language
    - Returns structured JSON with missing_info field for Agent 2 to check
    - Processes clarification requests from Agent 2 when information is missing
    
    Key Features:
    - LLM-powered analysis with structured output using Pydantic models
    - Type-safe JSON responses with guaranteed structure
    - Proper agent coordination (only processes clarifications when Agent 2 asks)
    - Simple default processing for missing information
    """
    
    def __init__(self):
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
        
        llm_service = OpenAIChatCompletion(ai_model_id="gpt-4o-mini")
        
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
            settings = OpenAIPromptExecutionSettings(
                max_tokens=200,
                temperature=0.1,
                function_choice_behavior=FunctionChoiceBehavior.Auto(),
                response_format=TravelAnalysis
            )
            
            response = await llm_service.get_text_content(prompt, settings)
            llm_result = response.text.strip()
            
            print(f"[DEBUG] 🤖 LLM Response: {llm_result}")
            
            analysis = json.loads(llm_result)
            
            # Calculate missing info based on what we have
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
        the analysis with simple default values for missing information.
        
        Args:
            original_analysis (str): JSON string of the original analysis
            user_clarification (str): User's clarification input (not used in current implementation)
            
        Returns:
            str: Updated JSON analysis with resolved missing information using defaults
        """
        print(f"[DEBUG] 🔄 Agent 1: Destination Analyzer (GPT-4o-mini) Plugin: handle_clarification called")
        print(f"[DEBUG] 📥 Original analysis: {original_analysis}")
        print(f"[DEBUG] 📥 User clarification: {user_clarification}")
        
        try:
            analysis = json.loads(original_analysis)
            
            print(f"[DEBUG] 🔍 Processing clarification")
            
            # Update duration if it was missing - use simple default
            if "duration" in analysis.get("missing_info", []):
                print(f"[DEBUG] ⏰ Duration missing - using default: 7 days")
                analysis["duration"] = "7 days"
                print(f"[DEBUG] ✅ Set duration to 7 days (default)")
            
            # Update destination if it was missing - use simple default
            if "destination" in analysis.get("missing_info", []):
                print(f"[DEBUG] 🎯 Destination missing - using default: India")
                analysis["destination"] = "India"
                print(f"[DEBUG] ✅ Set destination to India (default)")
            
            # Remove resolved missing info from the missing_info list
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
    Plugin for Agent 2: Itinerary Builder
    
    This plugin provides the core functionality for Agent 2 in the multi-agent system:
    - build_itinerary: Generates itineraries using structured output from Agent 1
    - _request_clarification: Requests clarification from Agent 1 when information is missing
    - _generate_general_itinerary: Uses LLM to create destination-specific itineraries
    
    **Agent 2's Role in Multi-Agent System:**
    - Generates itineraries using structured output from Agent 1
    - Uses LLM to create destination-specific, dynamic itineraries
    - Can reach back to Agent 1 if information is missing
    - Only creates itineraries when all required information is complete
    
    Key Features:
    - LLM-powered itinerary generation for dynamic, destination-specific content
    - Checks for missing information from Agent 1's analysis
    - Requests clarification from Agent 1 when info is missing
    - Proper agent coordination (detects missing info, requests clarification)
    - Type-safe communication using structured JSON from Agent 1
    """
    
    def __init__(self):
        self.kernel = Kernel()
    
    @kernel_function(
        description="Build travel itinerary based on analysis",
        name="build_itinerary"
    )
    async def build_itinerary(self, analysis: str) -> str:
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
            data = json.loads(analysis)
        except json.JSONDecodeError as e:
            print(f"[DEBUG] ❌ Agent 2: JSON parsing error: {e}")
            print(f"[DEBUG] ❌ Agent 2: Raw analysis received: {analysis}")
            return "Error: Could not parse Agent 1's analysis. Please try again."
        
        # Check if Agent 1 failed during analysis
        if "error" in data:
            print(f"[DEBUG] ❌ Agent 2: Itinerary Builder (GPT-4o-mini): Agent 1 failed: {data.get('error')}")
            return f"❌ Travel planning failed: {data.get('error')}. Please try again."
        
        # Extract travel information from Agent 1's analysis
        destination = data.get("destination", "Unknown")
        duration = data.get("duration", "7 days")
        purpose = data.get("purpose", "General Travel")
        missing_info = data.get("missing_info", [])
        
        print(f"[DEBUG] 🎯 Agent 2: Itinerary Builder (GPT-4o-mini): Destination={destination}, Duration={duration}, Purpose={purpose}")
        
        # If missing info, request clarification from Agent 1
        if missing_info:
            print(f"[DEBUG] ❓ Agent 2: Itinerary Builder (GPT-4o-mini): Missing info detected: {missing_info}")
            print(f"[DEBUG] ❓ Agent 2: Itinerary Builder (GPT-4o-mini): Asking Agent 1 for clarification")
            return self._request_clarification(missing_info)
        
        # Generate LLM-powered itinerary based on available information
        print(f"[DEBUG] 📝 Agent 2: Itinerary Builder (GPT-4o-mini): All info complete, creating LLM-generated itinerary")
        print(f"[DEBUG] 🎯 Agent 2: Itinerary Builder (GPT-4o-mini): Creating LLM-generated itinerary for {destination}")
        return await self._generate_general_itinerary(destination, duration, purpose)
    
    def _request_clarification(self, missing_info: List[str]) -> str:
        """
        Request clarification for missing information.
        
        This function creates a structured clarification request that Agent 1
        can process to get the missing information. This is the key function
        that enables Agent 2 to communicate with Agent 1 for missing info.
        
        Args:
            missing_info (List[str]): List of missing information items from Agent 1's analysis
            
        Returns:
            str: JSON string containing clarification request for Agent 1 to process
        """
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
    
    async def _generate_general_itinerary(self, destination: str, duration: str, purpose: str) -> str:
        """
        Generate LLM-powered travel itinerary.
        
        This function uses LLM to create dynamic, destination-specific itineraries
        based on the destination, duration, and purpose of travel.
        
        Args:
            destination (str): Travel destination
            duration (str): Trip duration (e.g., "7 days")
            purpose (str): Purpose of travel (e.g., "General Travel")
            
        Returns:
            str: LLM-generated travel itinerary
        """
        print(f"[DEBUG] 🤖 Agent 2: Using LLM to generate itinerary for {destination}")
        
        llm_service = OpenAIChatCompletion(ai_model_id="gpt-4o-mini")
        
        prompt = f"""
        Create a detailed {duration} travel itinerary for {destination} for {purpose.lower()} travel.
        
        The itinerary should include:
        
        ## Trip Overview
        - Brief introduction about the destination and trip purpose
        
        ## Day-by-Day Itinerary
        - Day 1: Arrival and initial exploration
        - Day 2-6: Daily activities, sightseeing, cultural experiences
        - Final day: Departure activities
        
        ## Accommodation
        - Recommendations for where to stay in {destination}
        - Booking tips and considerations
        
        ## Transportation
        - How to get around in {destination}
        - Airport transfers and local transport options
        
        ## Travel Tips
        - Local customs and culture
        - Language considerations
        - Visa requirements if needed
        - Weather and packing tips
        
        Make the itinerary specific to {destination} and {purpose.lower()} travel.
        Include realistic activities, local attractions, and cultural experiences.
        Format it nicely with clear sections and bullet points.
        """
        
        try:
            settings = OpenAIPromptExecutionSettings(
                max_tokens=1000,
                temperature=0.7,
                function_choice_behavior=FunctionChoiceBehavior.Auto()
            )
            
            response = await llm_service.get_text_content(prompt, settings)
            itinerary = response.text.strip()
            
            print(f"[DEBUG] ✅ Agent 2: LLM generated itinerary successfully")
            return itinerary
            
        except Exception as e:
            print(f"[DEBUG] ❌ Agent 2: LLM itinerary generation failed: {e}")
            return f"# Travel Itinerary: {destination} ({duration})\n\nPlan your {duration} trip to {destination} for {purpose.lower()} travel.\n\n*LLM generation failed - please try again.*"

def get_travel_agents():
    """
    Create multi-agent travel planning system with two specialized agents.
    
    This function sets up the true multi-agent system by:
    1. Creating separate kernels for each agent with only their relevant plugins
    2. Creating two specialized agents with clear roles and isolated plugin access
    3. Configuring agents with proper instructions and kernel integration
    4. Ensuring proper multi-agent coordination (Agent 2 can reach back to Agent 1)
    
    **Multi-Agent Architecture:**
    - Agent 1: Analyzes user input with LLM → returns structured JSON
    - Agent 2: Generates itineraries using structured output from Agent 1
    - Agent 2 can reach back to Agent 1 if information is missing
    
    **Best Practice: Separate Kernels per Agent**
    - Each agent has its own kernel with only its relevant plugins
    - Prevents tool confusion and memory/context mixing
    - Enables future features like per-agent embeddings
    - Ensures clean separation of concerns
    
    Returns:
        List[ChatCompletionAgent]: List of configured agents for the multi-agent travel planner
    """
    # Create separate kernels for each agent
    kernel_analyzer = Kernel()
    kernel_analyzer.add_plugin(DestinationAnalyzerPlugin(), "DestinationAnalyzer")
    
    kernel_itinerary = Kernel()
    kernel_itinerary.add_plugin(ItineraryBuilderPlugin(), "ItineraryBuilder")
    
    return [
        ChatCompletionAgent(
            name="Agent1_DestinationAnalyzer",
            description="Agent 1: Destination Analyzer (GPT-4o-mini)",
            instructions="""You are Agent 1: Destination Analyzer (GPT-4o-mini). Your role is to:

1. **ALWAYS start by calling analyze_travel_request** with the user's travel request
2. **Return ONLY the JSON result** from analyze_travel_request - no additional text
3. **Use handle_clarification ONLY** when Agent 2 specifically asks for missing information
4. **DO NOT add explanations or extra text** - just return the function results

**CRITICAL WORKFLOW:**
1. When you receive a travel request, IMMEDIATELY call analyze_travel_request
2. Return ONLY the JSON output from analyze_travel_request
3. Wait for Agent 2 to process your analysis
4. If Agent 2 asks for clarification, call handle_clarification and return the updated JSON

**IMPORTANT: You MUST use the available functions:**
- Use `analyze_travel_request` to analyze the initial request
- Use `handle_clarification` ONLY when Agent 2 asks for missing info

**CRITICAL: Return ONLY function results, no additional text or explanations.**""",
            service=OpenAIChatCompletion(ai_model_id="gpt-4o-mini"),
            kernel=kernel_analyzer,
        ),
        ChatCompletionAgent(
            name="Agent2_ItineraryBuilder", 
            description="Agent 2: Itinerary Builder (GPT-4o-mini)",
            instructions="""You are Agent 2: Itinerary Builder (GPT-4o-mini). Your role is to:

1. **ALWAYS start by calling build_itinerary** with Agent 1's analysis
2. **Return ONLY the result** from build_itinerary - no additional text
3. **Process Agent 1's JSON analysis** to create itineraries or request clarifications
4. **DO NOT add explanations or extra text** - just return the function results

**CRITICAL WORKFLOW:**
1. When you receive Agent 1's analysis, IMMEDIATELY call build_itinerary
2. Pass Agent 1's JSON analysis to build_itinerary
3. Return ONLY the output from build_itinerary (itinerary or clarification request)
4. If build_itinerary returns a clarification request, wait for Agent 1's response

**IMPORTANT: You MUST use the available functions:**
- Use `build_itinerary` to process Agent 1's analysis and create itineraries
- **DO NOT add extra text or explanations** - just return the function results

**CRITICAL: Return only function results, no additional text or explanations.**""",
            service=OpenAIChatCompletion(ai_model_id="gpt-4o-mini"),
            kernel=kernel_itinerary,
        ),
    ]

async def run_simple_travel_planner(user_request: str):
    """
    Run the multi-agent travel planner system.
    
    This function orchestrates the true multi-agent system with two specialized agents:
    1. Creates agents with kernel and plugins for multi-agent coordination
    2. Sets up group chat for agent collaboration with proper feedback loop
    3. Sends the user request to the multi-agent group for processing
    4. Returns the final LLM-generated travel itinerary or error message
    
    **Multi-Agent Coordination Flow:**
    - Agent 1 analyzes user input with LLM → returns structured JSON
    - Agent 2 checks structured output → generates itinerary OR requests clarification
    - Agent 1 processes clarification → updates analysis with defaults
    - Agent 2 creates final LLM-generated itinerary
    
    Args:
        user_request (str): Natural language travel request from user
        
    Returns:
        str: Final LLM-generated travel itinerary or None if failed
    """
    print(f"✈️ Travel Request: {user_request}")
    print("🤖 Initializing Simple Travel Planner...")
    
    agents = get_travel_agents()
    print(f"[DEBUG] 🤖 Created {len(agents)} agents: {[agent.name for agent in agents]}")
    
    group_chat = GroupChatOrchestration(
        members=agents,
        manager=RoundRobinGroupChatManager(max_rounds=3),
    )
    print(f"[DEBUG] 💬 Created Agent group chat with max_rounds=3")
    
    runtime = InProcessRuntime()
    runtime.start()
    print(f"[DEBUG] ⚡ Runtime started")
    
    print("🚀 Starting Travel Planner...")
    print("=" * 50)
    
    try:
        print(f"[DEBUG] 📤 Sending task to group chat: {user_request}")
        result = await group_chat.invoke(
            task=f"""Plan a trip: "{user_request}"

**COORDINATION FLOW:**
1. Agent 1: Analyze the request and extract destination, duration, purpose
2. Agent 2: Use Agent 1's analysis to create a detailed itinerary
3. If information is missing, Agent 2 asks Agent 1 for clarification
4. Agent 1 provides clarification, Agent 2 creates final itinerary

**CRITICAL: Return ONLY the final itinerary content, no explanations.**""",
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
    
    load_dotenv()
    print("[DEBUG] 📄 Environment variables loaded")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("[DEBUG] ❌ OpenAI API key not found")
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    print("[DEBUG] ✅ OpenAI API key found")
    print("✅ OpenAI API key loaded from .env file.")
    
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