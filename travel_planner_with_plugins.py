#!/usr/bin/env python3
"""
Microsoft Semantic Kernel Multi-Agent Travel Planning System with Plugins

This implementation demonstrates proper Semantic Kernel plugin usage:
- TravelPlannerPlugin: Contains functions for analyzing travel requests
- TravelAdvisorPlugin: Contains functions for creating itineraries
- DefaultProviderPlugin: Contains functions for providing default values

Based on Microsoft Semantic Kernel plugin best practices.
"""

import os
import asyncio
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import KernelFunctionFromPrompt
from semantic_kernel.functions import KernelPlugin
from pydantic import BaseModel, Field

# Pydantic model for travel request analysis
class TravelRequest(BaseModel):
    destination: str = Field(description="The destination for the trip")
    duration: Optional[str] = Field(default=None, description="Duration of the trip (e.g., '5 days', '2 weeks')")
    purpose: str = Field(description="The main purpose of the trip")
    missing_info: List[str] = Field(default_factory=list, description="List of missing information needed")

def create_travel_planner_plugin(kernel: Kernel) -> KernelPlugin:
    """
    Create TravelPlannerPlugin with functions for analyzing travel requests.
    
    Args:
        kernel: Semantic Kernel instance
        
    Returns:
        KernelPlugin: The travel planner plugin
    """
    # Function 1: Analyze travel request and return JSON
    analyze_request_prompt = """
    You are a Travel Planning Agent. Your role is to analyze travel requests and extract structured information.
    
    Analyze the user's travel request and return a JSON response with the following structure:
    {
        "destination": "string",
        "duration": "string or null",
        "purpose": "string", 
        "missing_info": ["list of missing information"]
    }
    
    Rules:
    1. Always return valid JSON
    2. If duration is mentioned, include it
    3. If duration is not mentioned, set it to null and add "duration" to missing_info
    4. Identify the main purpose of the trip
    5. List any missing critical information needed for planning
    
    User request: {{$input}}
    
    Return ONLY the JSON response, no additional text.
    """
    
    analyze_request_function = KernelFunctionFromPrompt(
        function_name="analyze_request",
        prompt=analyze_request_prompt,
        description="Analyzes travel requests and returns structured JSON data"
    )
    
    # Function 2: Provide default values for missing information
    provide_defaults_prompt = """
    You are a Travel Planning Agent that provides default values for missing travel information.
    
    When asked for missing information, provide sensible defaults in JSON format:
    
    Default rules:
    - For duration: "7 days" (unless specified otherwise)
    - For budget: "moderate" (unless specified otherwise)
    - For accommodation: "hotel" (unless specified otherwise)
    - For transportation: "public transport" (unless specified otherwise)
    
    Return a JSON response with the default values:
    {
        "defaults": {
            "duration": "7 days",
            "budget": "moderate",
            "accommodation": "hotel",
            "transportation": "public transport"
        }
    }
    
    Query: {{$input}}
    
    Return ONLY the JSON response, no additional text.
    """
    
    provide_defaults_function = KernelFunctionFromPrompt(
        function_name="provide_defaults",
        prompt=provide_defaults_prompt,
        description="Provides default values for missing travel information"
    )
    
    # Create plugin with both functions
    travel_planner_plugin = KernelPlugin(
        name="TravelPlanner",
        description="Plugin for analyzing travel requests and providing default values",
        functions=[analyze_request_function, provide_defaults_function]
    )
    
    return travel_planner_plugin

def create_travel_advisor_plugin(kernel: Kernel) -> KernelPlugin:
    """
    Create TravelAdvisorPlugin with functions for creating itineraries.
    
    Args:
        kernel: Semantic Kernel instance
        
    Returns:
        KernelPlugin: The travel advisor plugin
    """
    # Function 1: Create itinerary from JSON data
    create_itinerary_prompt = """
    You are a Travel Advisory Agent. Your role is to create detailed travel itineraries.
    
    You will receive JSON data from the TravelPlanner agent. Create a detailed human-readable itinerary.
    
    The JSON data will be in this format:
    {
        "destination": "string",
        "duration": "string or null",
        "purpose": "string",
        "missing_info": ["list of missing information"]
    }
    
    If there is missing information, ask the TravelPlanner plugin to provide default values by responding with: 
    "TRAVELPLANNER_QUERY: [list the missing information items]"
    
    If creating an itinerary, include:
    - Best time to visit
    - Recommended duration
    - Key attractions and activities
    - Accommodation suggestions
    - Transportation tips
    - Cultural considerations
    - Budget considerations
    
    JSON data: {{$input}}
    
    Provide a helpful, detailed response.
    """
    
    create_itinerary_function = KernelFunctionFromPrompt(
        function_name="create_itinerary",
        prompt=create_itinerary_prompt,
        description="Creates detailed travel itineraries from JSON data"
    )
    
    # Function 2: Enhance itinerary with additional details
    enhance_itinerary_prompt = """
    You are a Travel Advisory Agent that enhances itineraries with additional details.
    
    Take an existing itinerary and add more specific details like:
    - Exact locations and addresses
    - Opening hours for attractions
    - Cost estimates
    - Booking recommendations
    - Local tips and customs
    - Weather considerations
    - Safety tips
    
    Original itinerary: {{$input}}
    
    Provide an enhanced version with more specific details.
    """
    
    enhance_itinerary_function = KernelFunctionFromPrompt(
        function_name="enhance_itinerary",
        prompt=enhance_itinerary_prompt,
        description="Enhances itineraries with additional specific details"
    )
    
    # Create plugin with both functions
    travel_advisor_plugin = KernelPlugin(
        name="TravelAdvisor",
        description="Plugin for creating and enhancing travel itineraries",
        functions=[create_itinerary_function, enhance_itinerary_function]
    )
    
    return travel_advisor_plugin

async def run_multi_agent_workflow_with_plugins(user_request: str) -> str:
    """
    Run the multi-agent workflow using Semantic Kernel plugins.
    
    Workflow:
    1. TravelPlannerPlugin.analyze_request: Analyzes user input → returns JSON
    2. TravelAdvisorPlugin.create_itinerary: Processes JSON → creates itinerary or asks for missing info
    3. TravelPlannerPlugin.provide_defaults: Provides defaults if needed
    4. TravelAdvisorPlugin.enhance_itinerary: Enhances final itinerary
    
    Args:
        user_request (str): Natural language travel request from user
        
    Returns:
        str: Final response from the workflow
    """
    print(f"✈️ Travel Request: {user_request}")
    print("🤖 Starting Microsoft Semantic Kernel Multi-Agent Workflow with Plugins...")
    
    try:
        # Create kernel with OpenAI service
        kernel = Kernel()
        kernel.add_service(OpenAIChatCompletion(ai_model_id="gpt-4o-mini"))
        
        print("[DEBUG] 🏗️ Created kernel with OpenAI service")
        
        # Create and add plugins
        travel_planner_plugin = create_travel_planner_plugin(kernel)
        travel_advisor_plugin = create_travel_advisor_plugin(kernel)
        
        # Add plugins to kernel
        kernel.add_plugin(travel_planner_plugin)
        kernel.add_plugin(travel_advisor_plugin)
        
        print("[DEBUG] 🤖 Added TravelPlanner and TravelAdvisor plugins to kernel")
        
        # Step 1: TravelPlannerPlugin.analyze_request analyzes user request
        print("[DEBUG] 🔄 Step 1: TravelPlanner.analyze_request analyzing request...")
        planner_result = await kernel.invoke(plugin_name="TravelPlanner", function_name="analyze_request", input=user_request)
        json_response = planner_result.value[0].content
        
        print(f"[DEBUG] 📋 TravelPlanner JSON response: {json_response}")
        
        # Parse and validate JSON response
        try:
            travel_data = json.loads(json_response)
            print(f"[DEBUG] ✅ Successfully parsed JSON: {travel_data}")
        except json.JSONDecodeError as e:
            print(f"[DEBUG] ❌ JSON parsing error: {e}")
            return f"❌ Error: TravelPlanner returned invalid JSON: {json_response}"
        
        # Step 2: TravelAdvisorPlugin.create_itinerary processes JSON
        print("[DEBUG] 🔄 Step 2: TravelAdvisor.create_itinerary processing JSON...")
        advisor_result = await kernel.invoke(plugin_name="TravelAdvisor", function_name="create_itinerary", input=json_response)
        advisor_response = advisor_result.value[0].content
        
        print(f"[DEBUG] ✅ TravelAdvisor response length: {len(advisor_response)} characters")
        
        # Check if TravelAdvisor is asking for missing information
        if advisor_response.startswith("TRAVELPLANNER_QUERY:"):
            print("[DEBUG] 🔄 Step 3: TravelAdvisor asking TravelPlanner for missing info...")
            
            # Extract the query from TravelAdvisor
            query = advisor_response.replace("TRAVELPLANNER_QUERY:", "").strip()
            print(f"[DEBUG] 📝 Query to TravelPlanner: {query}")
            
            # Step 3: TravelPlannerPlugin.provide_defaults provides default values
            print("[DEBUG] 🔄 Step 4: TravelPlanner.provide_defaults providing defaults...")
            defaults_result = await kernel.invoke(plugin_name="TravelPlanner", function_name="provide_defaults", input=query)
            defaults_response = defaults_result.value[0].content
            
            print(f"[DEBUG] 📋 TravelPlanner defaults response: {defaults_response}")
            
            # Parse defaults JSON (handle markdown code blocks)
            try:
                # Clean up the response if it contains markdown code blocks
                cleaned_response = defaults_response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]  # Remove ```
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]  # Remove ```
                cleaned_response = cleaned_response.strip()
                
                defaults_data = json.loads(cleaned_response)
                print(f"[DEBUG] ✅ Successfully parsed defaults JSON: {defaults_data}")
                
                # Update original travel data with defaults
                if "defaults" in defaults_data:
                    if "duration" in defaults_data["defaults"] and travel_data["duration"] is None:
                        travel_data["duration"] = defaults_data["defaults"]["duration"]
                        if "duration" in travel_data["missing_info"]:
                            travel_data["missing_info"].remove("duration")
                
                # Create updated JSON for TravelAdvisor
                updated_json = json.dumps(travel_data)
                print(f"[DEBUG] 📋 Updated JSON with defaults: {updated_json}")
                
                # Step 4: TravelAdvisorPlugin.create_itinerary creates final itinerary
                print("[DEBUG] 🔄 Step 5: TravelAdvisor.create_itinerary creating final itinerary...")
                final_advisor_result = await kernel.invoke(plugin_name="TravelAdvisor", function_name="create_itinerary", input=updated_json)
                final_response = final_advisor_result.value[0].content
                
                print(f"[DEBUG] ✅ Final TravelAdvisor response length: {len(final_response)} characters")
                
            except json.JSONDecodeError as e:
                print(f"[DEBUG] ❌ Defaults JSON parsing error: {e}")
                return f"❌ Error: TravelPlanner returned invalid JSON: {defaults_response}"
        else:
            # TravelAdvisor provided a complete response (itinerary)
            final_response = advisor_response
            print(f"[DEBUG] ✅ TravelAdvisor provided complete response")
        
        # Step 5: TravelAdvisorPlugin.enhance_itinerary enhances the final response
        print("[DEBUG] 🔄 Step 6: TravelAdvisor.enhance_itinerary enhancing itinerary...")
        enhanced_result = await kernel.invoke(plugin_name="TravelAdvisor", function_name="enhance_itinerary", input=final_response)
        enhanced_response = enhanced_result.value[0].content
        
        print(f"[DEBUG] ✅ Enhanced response length: {len(enhanced_response)} characters")
        
        # Display workflow summary
        print("\n" + "="*50)
        print("📊 Multi-Agent Workflow with Plugins Summary:")
        print(f"  🔍 TravelPlanner.analyze_request analyzed: {user_request}")
        print(f"  📋 JSON output: {travel_data}")
        print(f"  ✨ TravelAdvisor.create_itinerary response length: {len(final_response)} characters")
        print(f"  🚀 TravelAdvisor.enhance_itinerary enhanced response length: {len(enhanced_response)} characters")
        print("="*50)
        
        return enhanced_response
        
    except Exception as e:
        print(f"[DEBUG] ❌ Workflow error: {type(e).__name__}: {str(e)}")
        return f"❌ Error in multi-agent workflow: {str(e)}"

async def interactive_demo_session_with_plugins():
    """
    Run an interactive demonstration session with plugins.
    
    This function provides a command-line interface for users to:
    1. Enter travel requests
    2. See the multi-agent workflow with plugins in action
    3. Exit the application
    """
    print("✈️ Microsoft Semantic Kernel Multi-Agent Travel Planner with Plugins")
    print("=" * 60)
    print("🤖 Two AI agent plugins will collaborate to help plan your trip!")
    print("   - TravelPlanner Plugin: Analyzes requests and provides defaults")
    print("   - TravelAdvisor Plugin: Creates and enhances itineraries")
    print("=" * 60)
    print("💡 Type your travel request below, or 'quit' to exit.")
    print("=" * 60)
    
    while True:
        try:
            print("\n" + "="*60)
            user_request = input("✈️ Your travel request: ").strip()
            print(f"[DEBUG] 👤 User input received: '{user_request}'")
            
            if user_request.lower() in ['quit', 'exit', 'q']:
                print("[DEBUG] 👋 User requested to quit")
                print("👋 Thank you for using the Microsoft Semantic Kernel Multi-Agent Plugin System!")
                break
            
            if not user_request:
                print("[DEBUG] ❌ Empty user input")
                print("❌ Please enter a valid travel request.")
                print("💡 Try: 'Plan a trip to Japan for cherry blossoms'")
                continue
            
            print(f"[DEBUG] 🚀 Starting plugin workflow for: '{user_request}'")
            print("\n🔄 Running Microsoft Semantic Kernel Multi-Agent Plugin Workflow...")
            print("🤖 Plugin agents are collaborating to help you...")
            
            # Run the multi-agent workflow with plugins
            result = await run_multi_agent_workflow_with_plugins(user_request)
            
            if result and not result.startswith("❌"):
                print(f"[DEBUG] ✅ Plugin workflow successful")
                print("\n" + "="*60)
                print("🎯 FINAL ENHANCED RESPONSE:")
                print("="*60)
                print(result)
                print("="*60)
                print("\n✅ Plugin workflow completed!")
                print("💡 Ask another question or type 'quit' to exit.")
            else:
                print(f"[DEBUG] ❌ Plugin workflow failed")
                print("\n❌ Plugin workflow failed. Please try again.")
                
        except KeyboardInterrupt:
            print(f"[DEBUG] ⌨️ Keyboard interrupt received")
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"[DEBUG] ❌ Exception in interactive session: {type(e).__name__}: {str(e)}")
            print(f"\n❌ Error: {e}")
            print("Please try again.")

async def main_with_plugins():
    """
    Main function to demonstrate the Microsoft Semantic Kernel Multi-Agent plugin system.
    
    This function:
    1. Loads environment variables
    2. Validates OpenAI API key
    3. Shows example requests
    4. Starts the interactive demonstration session with plugins
    """
    print("🚀 Starting Microsoft Semantic Kernel Multi-Agent Travel Planning System with Plugins")
    print("[DEBUG] 🚀 Main function with plugins started")
    
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
        "What should I know about traveling to Bali?",
        "Give me travel tips for New York City."
    ]
    
    print("\n📋 Example travel requests you can try:")
    for i, request in enumerate(example_requests, 1):
        print(f"{i}. {request}")
    
    print("\n🎯 Starting interactive demonstration mode with plugins...")
    print("[DEBUG] 🎯 Calling interactive_demo_session_with_plugins")
    await interactive_demo_session_with_plugins()
    print("[DEBUG] 🏁 Main function with plugins completed")

if __name__ == "__main__":
    asyncio.run(main_with_plugins()) 