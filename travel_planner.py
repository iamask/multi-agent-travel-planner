#!/usr/bin/env python3
"""
Microsoft Semantic Kernel Multi-Agent Travel Planning System

This implementation uses Microsoft's Semantic Kernel to create a custom multi-agent workflow:
- Agent 1 (TravelPlanner): Analyzes user input and returns structured JSON data
- Agent 2 (TravelAdvisor): Takes JSON data and creates itineraries or asks for missing info

Based on Microsoft Semantic Kernel documentation and best practices.
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
from pydantic import BaseModel, Field

# Pydantic model for travel request analysis
class TravelRequest(BaseModel):
    destination: str = Field(description="The destination for the trip")
    duration: Optional[str] = Field(default=None, description="Duration of the trip (e.g., '5 days', '2 weeks')")
    purpose: str = Field(description="The main purpose of the trip")
    missing_info: List[str] = Field(default_factory=list, description="List of missing information needed")

def create_travel_planner_agent(kernel: Kernel) -> KernelFunctionFromPrompt:
    """
    Create Agent 1: TravelPlanner that analyzes user input and returns structured JSON data.
    
    Args:
        kernel: Semantic Kernel instance
        
    Returns:
        KernelFunctionFromPrompt: The travel planner function
    """
    travel_planner_prompt = """
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
    
    return KernelFunctionFromPrompt(
        function_name="travel_planner",
        prompt=travel_planner_prompt,
        description="Analyzes travel requests and returns structured JSON data"
    )

def create_travel_advisor_agent(kernel: Kernel) -> KernelFunctionFromPrompt:
    """
    Create Agent 2: TravelAdvisor that processes JSON data and creates itineraries or asks Agent 1 for missing info.
    
    Args:
        kernel: Semantic Kernel instance
        
    Returns:
        KernelFunctionFromPrompt: The travel advisor function
    """
    travel_advisor_prompt = """
    You are a Travel Advisory Agent. Your role is to create detailed travel itineraries or ask Agent 1 for missing information.
    
    You will receive JSON data from the TravelPlanner agent. Your task is to:
    
    1. If the JSON is complete (no missing_info or empty missing_info), create a detailed human-readable itinerary
    2. If there is missing information, ask Agent 1 to provide default values for the missing details
    
    The JSON data will be in this format:
    {
        "destination": "string",
        "duration": "string or null",
        "purpose": "string",
        "missing_info": ["list of missing information"]
    }
    
    If creating an itinerary, include:
    - Best time to visit
    - Recommended duration
    - Key attractions and activities
    - Accommodation suggestions
    - Transportation tips
    - Cultural considerations
    - Budget considerations
    
    If asking for missing information, respond with: "AGENT1_QUERY: [list the missing information items]"
    
    JSON data: {{$input}}
    
    Provide a helpful, detailed response.
    """
    
    return KernelFunctionFromPrompt(
        function_name="travel_advisor",
        prompt=travel_advisor_prompt,
        description="Creates itineraries or asks Agent 1 for missing information based on JSON data"
    )

def create_travel_planner_followup_agent(kernel: Kernel) -> KernelFunctionFromPrompt:
    """
    Create Agent 1 Follow-up: TravelPlanner that provides default values for missing information.
    
    Args:
        kernel: Semantic Kernel instance
        
    Returns:
        KernelFunctionFromPrompt: The travel planner follow-up function
    """
    travel_planner_followup_prompt = """
    You are a Travel Planning Agent that provides default values for missing travel information.
    
    When Agent 2 asks for missing information, provide sensible defaults in JSON format:
    
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
    
    Agent 2 query: {{$input}}
    
    Return ONLY the JSON response, no additional text.
    """
    
    return KernelFunctionFromPrompt(
        function_name="travel_planner_followup",
        prompt=travel_planner_followup_prompt,
        description="Provides default values for missing travel information"
    )

async def run_multi_agent_workflow(user_request: str) -> str:
    """
    Run the multi-agent workflow using Microsoft Semantic Kernel.
    
    Workflow:
    1. Agent 1 (TravelPlanner): Analyzes user input → returns JSON
    2. Agent 2 (TravelAdvisor): Processes JSON → creates itinerary or asks for missing info
    
    Args:
        user_request (str): Natural language travel request from user
        
    Returns:
        str: Final response from the workflow
    """
    print(f"✈️ Travel Request: {user_request}")
    print("🤖 Starting Microsoft Semantic Kernel Multi-Agent Workflow...")
    
    try:
        # Create kernel with OpenAI service
        kernel = Kernel()
        kernel.add_service(OpenAIChatCompletion(ai_model_id="gpt-4o-mini"))
        
        print("[DEBUG] 🏗️ Created kernel with OpenAI service")
        
        # Create Agent 1: TravelPlanner
        travel_planner = create_travel_planner_agent(kernel)
        print("[DEBUG] 🤖 Created TravelPlanner agent")
        
        # Create Agent 2: TravelAdvisor  
        travel_advisor = create_travel_advisor_agent(kernel)
        print("[DEBUG] 🤖 Created TravelAdvisor agent")
        
        # Create Agent 1 Follow-up for default values
        travel_planner_followup = create_travel_planner_followup_agent(kernel)
        print("[DEBUG] 🤖 Created TravelPlanner Follow-up agent")
        
        # Step 1: Agent 1 analyzes user request and returns JSON
        print("[DEBUG] 🔄 Step 1: TravelPlanner analyzing request...")
        planner_result = await kernel.invoke(travel_planner, input=user_request)
        json_response = planner_result.value[0].content
        
        print(f"[DEBUG] 📋 TravelPlanner JSON response: {json_response}")
        
        # Parse and validate JSON response
        try:
            travel_data = json.loads(json_response)
            print(f"[DEBUG] ✅ Successfully parsed JSON: {travel_data}")
        except json.JSONDecodeError as e:
            print(f"[DEBUG] ❌ JSON parsing error: {e}")
            return f"❌ Error: TravelPlanner returned invalid JSON: {json_response}"
        
        # Step 2: Agent 2 processes JSON and creates response
        print("[DEBUG] 🔄 Step 2: TravelAdvisor processing JSON...")
        advisor_result = await kernel.invoke(travel_advisor, input=json_response)
        advisor_response = advisor_result.value[0].content
        
        print(f"[DEBUG] ✅ TravelAdvisor response length: {len(advisor_response)} characters")
        
        # Check if Agent 2 is asking for missing information
        if advisor_response.startswith("AGENT1_QUERY:"):
            print("[DEBUG] 🔄 Step 3: Agent 2 asking Agent 1 for missing info...")
            
            # Extract the query from Agent 2
            query = advisor_response.replace("AGENT1_QUERY:", "").strip()
            print(f"[DEBUG] 📝 Query to Agent 1: {query}")
            
            # Step 3: Agent 1 provides default values
            print("[DEBUG] 🔄 Step 4: TravelPlanner Follow-up providing defaults...")
            followup_result = await kernel.invoke(travel_planner_followup, input=query)
            defaults_response = followup_result.value[0].content
            
            print(f"[DEBUG] 📋 Agent 1 defaults response: {defaults_response}")
            
            # Parse defaults JSON
            try:
                defaults_data = json.loads(defaults_response)
                print(f"[DEBUG] ✅ Successfully parsed defaults JSON: {defaults_data}")
                
                # Update original travel data with defaults
                if "defaults" in defaults_data:
                    if "duration" in defaults_data["defaults"] and travel_data["duration"] is None:
                        travel_data["duration"] = defaults_data["defaults"]["duration"]
                        travel_data["missing_info"].remove("duration")
                
                # Create updated JSON for Agent 2
                updated_json = json.dumps(travel_data)
                print(f"[DEBUG] 📋 Updated JSON with defaults: {updated_json}")
                
                # Step 4: Agent 2 creates final itinerary with defaults
                print("[DEBUG] 🔄 Step 5: TravelAdvisor creating final itinerary...")
                final_advisor_result = await kernel.invoke(travel_advisor, input=updated_json)
                final_response = final_advisor_result.value[0].content
                
                print(f"[DEBUG] ✅ Final TravelAdvisor response length: {len(final_response)} characters")
                
            except json.JSONDecodeError as e:
                print(f"[DEBUG] ❌ Defaults JSON parsing error: {e}")
                return f"❌ Error: TravelPlanner Follow-up returned invalid JSON: {defaults_response}"
        else:
            # Agent 2 provided a complete response (itinerary or user question)
            final_response = advisor_response
            print(f"[DEBUG] ✅ TravelAdvisor provided complete response")
        
        # Display workflow summary
        print("\n" + "="*50)
        print("📊 Multi-Agent Workflow Summary:")
        print(f"  🔍 Agent 1 (TravelPlanner) analyzed: {user_request}")
        print(f"  📋 JSON output: {travel_data}")
        print(f"  ✨ Agent 2 (TravelAdvisor) response length: {len(final_response)} characters")
        print("="*50)
        
        return final_response
        
    except Exception as e:
        print(f"[DEBUG] ❌ Workflow error: {type(e).__name__}: {str(e)}")
        return f"❌ Error in multi-agent workflow: {str(e)}"

async def interactive_demo_session():
    """
    Run an interactive demonstration session.
    
    This function provides a command-line interface for users to:
    1. Enter travel requests
    2. See the multi-agent workflow in action
    3. Exit the application
    """
    print("✈️ Microsoft Semantic Kernel Multi-Agent Travel Planner")
    print("=" * 50)
    print("🤖 Two AI agents will collaborate to help plan your trip!")
    print("   - Agent 1 (TravelPlanner): Analyzes requests and returns JSON data")
    print("   - Agent 2 (TravelAdvisor): Creates itineraries or asks for missing info")
    print("=" * 50)
    print("💡 Type your travel request below, or 'quit' to exit.")
    print("=" * 50)
    
    while True:
        try:
            print("\n" + "="*50)
            user_request = input("✈️ Your travel request: ").strip()
            print(f"[DEBUG] 👤 User input received: '{user_request}'")
            
            if user_request.lower() in ['quit', 'exit', 'q']:
                print("[DEBUG] 👋 User requested to quit")
                print("👋 Thank you for using the Microsoft Semantic Kernel Multi-Agent System!")
                break
            
            if not user_request:
                print("[DEBUG] ❌ Empty user input")
                print("❌ Please enter a valid travel request.")
                print("💡 Try: 'Plan a trip to Japan for cherry blossoms'")
                continue
            
            print(f"[DEBUG] 🚀 Starting workflow for: '{user_request}'")
            print("\n🔄 Running Microsoft Semantic Kernel Multi-Agent Workflow...")
            print("🤖 Agents are collaborating to help you...")
            
            # Run the multi-agent workflow
            result = await run_multi_agent_workflow(user_request)
            
            if result and not result.startswith("❌"):
                print(f"[DEBUG] ✅ Workflow successful")
                print("\n" + "="*50)
                print("🎯 FINAL RESPONSE:")
                print("="*50)
                print(result)
                print("="*50)
                print("\n✅ Workflow completed!")
                print("💡 Ask another question or type 'quit' to exit.")
            else:
                print(f"[DEBUG] ❌ Workflow failed")
                print("\n❌ Workflow failed. Please try again.")
                
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
    Main function to demonstrate the Microsoft Semantic Kernel Multi-Agent system.
    
    This function:
    1. Loads environment variables
    2. Validates OpenAI API key
    3. Shows example requests
    4. Starts the interactive demonstration session
    """
    print("🚀 Starting Microsoft Semantic Kernel Multi-Agent Travel Planning System")
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
        "What should I know about traveling to Bali?",
        "Give me travel tips for New York City."
    ]
    
    print("\n📋 Example travel requests you can try:")
    for i, request in enumerate(example_requests, 1):
        print(f"{i}. {request}")
    
    print("\n🎯 Starting interactive demonstration mode...")
    print("[DEBUG] 🎯 Calling interactive_demo_session")
    await interactive_demo_session()
    print("[DEBUG] 🏁 Main function completed")

if __name__ == "__main__":
    asyncio.run(main()) 