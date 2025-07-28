#!/usr/bin/env python3
"""
Microsoft Semantic Kernel Multi-Agent Travel Planning System with Plugins

This implementation demonstrates proper Semantic Kernel plugin usage with OpenAI function calling:
- TravelPlannerPlugin - Agent 1 : Contains functions for analyzing travel requests and providing defaults
- TravelAdvisorPlugin - Agent 2 : Contains functions for creating and enhancing itineraries

Based on Microsoft Semantic Kernel plugin best practices with OpenAI function calling.
"""

import os
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import KernelFunctionFromPrompt
from semantic_kernel.functions import KernelPlugin
from semantic_kernel.kernel_pydantic import KernelBaseModel
from pydantic import Field

# Configure detailed logging for agent interactions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_interactions.log')
    ]
)
logger = logging.getLogger(__name__)

# Pydantic models for structured output using Semantic Kernel
# Similar to zod in javascript
class TravelAnalysis(KernelBaseModel):
    """
    Structured output model for travel request analysis.
    Used by TravelPlanner agent to return structured JSON data.
    This model ensures type-safe communication between agents using OpenAI function calling.
    """
    destination: str = Field(description="The destination for the trip")
    duration: Optional[str] = Field(default=None, description="Duration of the trip (e.g., '5 days', '2 weeks')")
    purpose: str = Field(description="The main purpose of the trip")
    missing_info: List[str] = Field(default_factory=list, description="List of missing critical information needed for planning")

class DefaultValues(KernelBaseModel):
    """
    Structured output model for default values.
    Used by TravelPlanner agent to provide default values for missing information.
    This model ensures consistent default value responses using OpenAI function calling.
    """
    duration: Optional[str] = Field(default="7 days", description="Default duration for the trip")
    budget: Optional[str] = Field(default="moderate", description="Default budget level")
    accommodation: Optional[str] = Field(default="hotel", description="Default accommodation type")
    transportation: Optional[str] = Field(default="public transport", description="Default transportation method")

class ItineraryRequest(KernelBaseModel):
    """
    Structured model for itinerary requests with missing information.
    Used by TravelAdvisor agent to request missing data from TravelPlanner.
    This model enables structured function calling instead of legacy string parsing.
    """
    missing_items: List[str] = Field(description="List of missing information items needed for itinerary creation")
    reason: str = Field(description="Reason why this information is needed")

def create_travel_planner_plugin(kernel: Kernel) -> KernelPlugin:
    """
    Create TravelPlannerPlugin with functions for analyzing travel requests.
    
    This plugin contains two main functions that use OpenAI function calling:
    1. analyze_request: Analyzes user input and returns structured JSON using OpenAI function calling
    2. provide_defaults: Provides default values for missing travel information using structured models
    
    Args:
        kernel: Semantic Kernel instance with OpenAI service configured
        
    Returns:
        KernelPlugin: The travel planner plugin with structured output capabilities
    """
    logger.info("🔧 [AGENT 1] Creating TravelPlanner plugin with structured output functions...")
    
    # Function 1: Analyze travel request and return JSON using OpenAI function calling
    # This function uses structured output to ensure consistent JSON responses
    # OpenAI function calling ensures type-safe communication between agents
    analyze_request_prompt = """
    You are a Travel Planning Agent (Agent 1). Your role is to analyze travel requests and extract structured information.
    
    Analyze the user's travel request and extract the following information:
    - destination: The destination for the trip
    - duration: The duration of the trip (e.g., "5 days", "2 weeks") or null if not mentioned
    - purpose: The main purpose of the trip
    - missing_info: List of missing critical information needed for planning
    
    Rules:
    1. If duration is mentioned, include it
    2. If duration is not mentioned, set it to null and add "duration" to missing_info
    3. Identify the main purpose of the trip
    4. List any missing critical information needed for planning
    
    User request: {{$input}}
    """
    
    # Configure execution settings for structured output using OpenAI function calling
    # This ensures the AI model returns JSON in the exact format we need
    # OpenAI function calling provides reliable, type-safe responses
    logger.info("⚙️ [AGENT 1] Configuring execution settings for TravelAnalysis structured output...")
    req_settings = kernel.get_prompt_execution_settings_from_service_id(service_id="default")
    req_settings.temperature = 0.1  # Low temperature for consistent structured output
    req_settings.response_format = TravelAnalysis  # Enforce JSON schema compliance using OpenAI function calling
    
    analyze_request_function = KernelFunctionFromPrompt(
        function_name="analyze_request",
        prompt=analyze_request_prompt,
        description="Analyzes travel requests and returns structured JSON data using OpenAI function calling",
        prompt_execution_settings=req_settings
    )
    
    logger.info("✅ [AGENT 1] Created analyze_request function with TravelAnalysis structured output")
    
    # Function 2: Provide default values for missing information using OpenAI function calling
    # This function provides sensible defaults when information is missing
    # Uses structured models for reliable communication between agents
    provide_defaults_prompt = """
    You are a Travel Planning Agent (Agent 1) that provides default values for missing travel information.
    
    When asked for missing information, provide sensible defaults based on the query.
    
    Default rules:
    - For duration: "7 days" (unless specified otherwise)
    - For budget: "moderate" (unless specified otherwise)
    - For accommodation: "hotel" (unless specified otherwise)
    - For transportation: "public transport" (unless specified otherwise)
    
    Return the default values as individual fields in the response using OpenAI function calling.
    
    Query: {{$input}}
    """
    
    # Configure execution settings for defaults function using OpenAI function calling
    # This ensures consistent default value responses with structured models
    logger.info("⚙️ [AGENT 1] Configuring execution settings for DefaultValues structured output...")
    defaults_settings = kernel.get_prompt_execution_settings_from_service_id(service_id="default")
    defaults_settings.temperature = 0.1  # Low temperature for consistent defaults
    defaults_settings.response_format = DefaultValues  # Enforce JSON schema compliance using OpenAI function calling
    
    provide_defaults_function = KernelFunctionFromPrompt(
        function_name="provide_defaults",
        prompt=provide_defaults_prompt,
        description="Provides default values for missing travel information using OpenAI function calling",
        prompt_execution_settings=defaults_settings
    )
    
    logger.info("✅ [AGENT 1] Created provide_defaults function with DefaultValues structured output")
    
    # Create plugin with both functions that use OpenAI function calling
    # This plugin will be used by the TravelPlanner agent for structured communication
    travel_planner_plugin = KernelPlugin(
        name="TravelPlanner",
        description="Plugin for analyzing travel requests and providing default values using OpenAI function calling",
        functions=[analyze_request_function, provide_defaults_function]
    )
    
    logger.info("🎯 [AGENT 1] Successfully created TravelPlanner plugin with 2 functions using OpenAI function calling")
    return travel_planner_plugin

def create_travel_advisor_plugin(kernel: Kernel) -> KernelPlugin:
    """
    Create TravelAdvisorPlugin with functions for creating itineraries.
    
    This plugin contains three main functions that use OpenAI function calling:
    1. create_itinerary: Creates detailed itineraries from structured travel data
    2. request_missing_info: Requests missing info using structured function calling (NEW)
    3. enhance_itinerary: Enhances itineraries with additional specific details
    
    Args:
        kernel: Semantic Kernel instance with OpenAI service configured
        
    Returns:
        KernelPlugin: The travel advisor plugin for itinerary creation with OpenAI function calling
    """
    logger.info("🔧 [AGENT 2] Creating TravelAdvisor plugin with itinerary functions using OpenAI function calling...")
    
    # Function 1: Create itinerary from JSON data using OpenAI function calling
    # This function processes structured data from TravelPlanner and creates human-readable itineraries
    # Uses structured data checking instead of legacy string parsing
    create_itinerary_prompt = """
    You are a Travel Advisory Agent (Agent 2). Your role is to create detailed travel itineraries.
    
    You will receive JSON data from the TravelPlanner agent (Agent 1). Create a detailed human-readable itinerary.
    
    The JSON data will be in this format:
    {
        "destination": "string",
        "duration": "string or null",
        "purpose": "string",
        "missing_info": ["list of missing information"]
    }
    
    If there is missing information, the workflow will automatically use structured function calling to request it.
    You don't need to handle missing info here - just create the best itinerary possible with the available data.
    
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
    
    # Configure execution settings for create itinerary function using OpenAI function calling
    # Higher temperature for more creative and detailed responses
    logger.info("⚙️ [AGENT 2] Configuring execution settings for create_itinerary function...")
    create_settings = kernel.get_prompt_execution_settings_from_service_id(service_id="default")
    create_settings.temperature = 0.3  # Moderate temperature for creative but consistent responses
    
    create_itinerary_function = KernelFunctionFromPrompt(
        function_name="create_itinerary",
        prompt=create_itinerary_prompt,
        description="Creates detailed travel itineraries from JSON data using OpenAI function calling",
        prompt_execution_settings=create_settings
    )
    
    logger.info("✅ [AGENT 2] Created create_itinerary function using OpenAI function calling")
    
    # Function 2: Request missing information using OpenAI function calling (NEW)
    # This function uses structured output to request missing data from Agent 1
    # Replaces legacy string parsing with reliable structured function calling
    request_missing_info_prompt = """
    You are a Travel Advisory Agent (Agent 2) that requests missing information from the TravelPlanner agent (Agent 1).
    
    When you need missing information to create a proper itinerary, use this function to request it.
    
    Analyze the missing information and provide a structured request using OpenAI function calling.
    
    Missing information: {{$input}}
    """
    
    # Configure execution settings for request missing info function using OpenAI function calling
    logger.info("⚙️ [AGENT 2] Configuring execution settings for request_missing_info function...")
    request_settings = kernel.get_prompt_execution_settings_from_service_id(service_id="default")
    request_settings.temperature = 0.1  # Low temperature for consistent requests
    request_settings.response_format = ItineraryRequest  # Enforce JSON schema compliance using OpenAI function calling
    
    request_missing_info_function = KernelFunctionFromPrompt(
        function_name="request_missing_info",
        prompt=request_missing_info_prompt,
        description="Requests missing information from TravelPlanner agent using OpenAI function calling",
        prompt_execution_settings=request_settings
    )
    
    logger.info("✅ [AGENT 2] Created request_missing_info function with ItineraryRequest structured output")
    
    # Function 3: Enhance itinerary with additional details using OpenAI function calling
    # This function takes an existing itinerary and adds more specific, actionable details
    # Uses structured models for reliable enhancement
    enhance_itinerary_prompt = """
    You are a Travel Advisory Agent (Agent 2) that enhances itineraries with additional details.
    
    Take an existing itinerary and add more specific details like:
    - Exact locations and addresses
    - Opening hours for attractions
    - Cost estimates
    - Booking recommendations
    - Local tips and customs
    - Weather considerations
    - Safety tips
    
    Original itinerary: {{$input}}
    
    Provide an enhanced version with more specific details using OpenAI function calling.
    """
    
    # Configure execution settings for enhance itinerary function using OpenAI function calling
    # Higher temperature for more detailed and specific enhancements
    logger.info("⚙️ [AGENT 2] Configuring execution settings for enhance_itinerary function...")
    enhance_settings = kernel.get_prompt_execution_settings_from_service_id(service_id="default")
    enhance_settings.temperature = 0.3  # Moderate temperature for detailed enhancements
    
    enhance_itinerary_function = KernelFunctionFromPrompt(
        function_name="enhance_itinerary",
        prompt=enhance_itinerary_prompt,
        description="Enhances itineraries with additional specific details using OpenAI function calling",
        prompt_execution_settings=enhance_settings
    )
    
    logger.info("✅ [AGENT 2] Created enhance_itinerary function using OpenAI function calling")
    
    # Create plugin with all three functions that use OpenAI function calling
    # This plugin will be used by the TravelAdvisor agent for structured communication
    travel_advisor_plugin = KernelPlugin(
        name="TravelAdvisor",
        description="Plugin for creating and enhancing travel itineraries using OpenAI function calling",
        functions=[create_itinerary_function, request_missing_info_function, enhance_itinerary_function]
    )
    
    logger.info("🎯 [AGENT 2] Successfully created TravelAdvisor plugin with 3 functions using OpenAI function calling")
    return travel_advisor_plugin

async def run_multi_agent_workflow_with_plugins(user_request: str) -> str:
    """
    Run the multi-agent workflow using Semantic Kernel plugins with OpenAI function calling.
    
    Workflow Steps using OpenAI function calling:
    1. TravelPlannerPlugin.analyze_request: Analyzes user input → returns structured JSON using OpenAI function calling
    2. TravelAdvisorPlugin.create_itinerary: Processes JSON → creates itinerary or requests missing info using structured data
    3. TravelAdvisorPlugin.request_missing_info: Requests missing info using structured function calling (NEW)
    4. TravelPlannerPlugin.provide_defaults: Provides defaults if needed using OpenAI function calling (conditional step)
    5. TravelAdvisorPlugin.enhance_itinerary: Enhances final itinerary using OpenAI function calling
    
    Agent Interactions using OpenAI function calling:
    - TravelPlanner Agent (Agent 1): Handles structured data analysis and default value provision
    - TravelAdvisor Agent (Agent 2): Handles itinerary creation and enhancement
    - Agents communicate through structured JSON data and OpenAI function calling
    
    Args:
        user_request (str): Natural language travel request from user
        
    Returns:
        str: Final enhanced response from the workflow
    """
    logger.info(f"🚀 Starting multi-agent workflow for request: '{user_request}' using OpenAI function calling")
    print(f"✈️ Travel Request: {user_request}")
    print("🤖 Starting Microsoft Semantic Kernel Multi-Agent Workflow with OpenAI Function Calling...")
    
    try:
        # Step 1: Initialize Kernel and Services
        logger.info("🔧 Step 1: Initializing kernel and AI services with OpenAI function calling...")
        kernel = Kernel()
        kernel.add_service(OpenAIChatCompletion(service_id="default", ai_model_id="gpt-4o-mini"))
        
        print("[DEBUG] 🏗️ Created kernel with OpenAI service for function calling")
        logger.info("✅ Kernel initialized with OpenAI service (gpt-4o-mini) for function calling")
        
        # Step 2: Create and Register Plugins with OpenAI function calling
        logger.info("🔧 Step 2: Creating and registering agent plugins with OpenAI function calling...")
        travel_planner_plugin = create_travel_planner_plugin(kernel)
        travel_advisor_plugin = create_travel_advisor_plugin(kernel)
        
        # Add plugins to kernel for agent access with OpenAI function calling
        kernel.add_plugin(travel_planner_plugin)
        kernel.add_plugin(travel_advisor_plugin)
        
        print("[DEBUG] 🤖 Added TravelPlanner and TravelAdvisor plugins to kernel with OpenAI function calling")
        logger.info("✅ Both plugins registered with kernel - agents ready for collaboration using OpenAI function calling")
        
        # Step 3: TravelPlanner Agent (Agent 1) - Analyze Request using OpenAI function calling
        logger.info("🔄 Step 3: [AGENT 1] TravelPlanner agent analyzing user request using OpenAI function calling...")
        print("[DEBUG] 🔄 Step 1: TravelPlanner.analyze_request analyzing request using OpenAI function calling...")
        
        # Agent Tool Call: TravelPlanner.analyze_request using OpenAI function calling
        # This agent function uses structured output to ensure consistent JSON responses
        # OpenAI function calling provides reliable, type-safe communication
        planner_result = await kernel.invoke(plugin_name="TravelPlanner", function_name="analyze_request", input=user_request)
        json_response = planner_result.value[0].content
        
        logger.info(f"📋 [AGENT 1] TravelPlanner agent returned structured data using OpenAI function calling: {json_response}")
        print(f"[DEBUG] 📋 TravelPlanner JSON response using OpenAI function calling: {json_response}")
        
        # Step 4: Parse Structured Output from OpenAI function calling
        logger.info("🔧 Step 4: Parsing structured output from [AGENT 1] TravelPlanner agent using OpenAI function calling...")
        try:
            # The response is already a TravelAnalysis object from OpenAI function calling, convert to dict
            travel_data = json_response.model_dump() if hasattr(json_response, 'model_dump') else json.loads(json_response)
            logger.info(f"✅ Successfully parsed structured output from OpenAI function calling: {travel_data}")
            print(f"[DEBUG] ✅ Successfully parsed structured output from OpenAI function calling: {travel_data}")
        except Exception as e:
            logger.error(f"❌ Structured output parsing error from OpenAI function calling: {e}")
            print(f"[DEBUG] ❌ Structured output parsing error from OpenAI function calling: {e}")
            return f"❌ Error: TravelPlanner returned invalid structured output from OpenAI function calling: {json_response}"
        
        # Step 5: TravelAdvisor Agent (Agent 2) - Create Initial Itinerary using OpenAI function calling
        logger.info("🔄 Step 5: [AGENT 2] TravelAdvisor agent creating initial itinerary using OpenAI function calling...")
        print("[DEBUG] 🔄 Step 2: TravelAdvisor.create_itinerary processing JSON using OpenAI function calling...")
        
        # Agent Tool Call: TravelAdvisor.create_itinerary using OpenAI function calling
        # This agent function processes the structured data and creates a human-readable itinerary
        # Uses structured data checking instead of legacy string parsing
        advisor_result = await kernel.invoke(plugin_name="TravelAdvisor", function_name="create_itinerary", input=json_response)
        advisor_response = advisor_result.value[0].content
        
        logger.info(f"✅ [AGENT 2] TravelAdvisor agent response length using OpenAI function calling: {len(advisor_response)} characters")
        print(f"[DEBUG] ✅ TravelAdvisor response length using OpenAI function calling: {len(advisor_response)} characters")
        
        # Step 6: Check for Missing Information and Handle Agent Collaboration using OpenAI function calling
        logger.info("🔍 Step 6: Checking for missing information and agent collaboration using OpenAI function calling...")
        
        # Check if there's missing information that needs to be requested using structured data
        # This replaces legacy string parsing with reliable structured data checking
        if travel_data.get("missing_info") and len(travel_data["missing_info"]) > 0:
            logger.info("🔄 Missing information detected, [AGENT 2] TravelAdvisor requesting missing info from [AGENT 1] TravelPlanner using OpenAI function calling...")
            print("[DEBUG] 🔄 Step 3: TravelAdvisor requesting missing info from TravelPlanner using OpenAI function calling...")
            
            # Step 7: TravelAdvisor Agent (Agent 2) - Request Missing Information using OpenAI function calling
            logger.info("🔄 Step 7: [AGENT 2] TravelAdvisor agent requesting missing information using OpenAI function calling...")
            print("[DEBUG] 🔄 Step 4: TravelAdvisor.request_missing_info requesting missing info using OpenAI function calling...")
            
            # Agent Tool Call: TravelAdvisor.request_missing_info using OpenAI function calling
            # This agent function uses structured output to request missing information
            # Replaces legacy string parsing with reliable structured function calling
            missing_info_input = json.dumps(travel_data["missing_info"])
            request_result = await kernel.invoke(plugin_name="TravelAdvisor", function_name="request_missing_info", input=missing_info_input)
            request_response = request_result.value[0].content
            
            logger.info(f"📋 [AGENT 2] TravelAdvisor request response using OpenAI function calling: {request_response}")
            print(f"[DEBUG] 📋 TravelAdvisor request response using OpenAI function calling: {request_response}")
            
            # Step 8: Parse Structured Request from OpenAI function calling
            logger.info("🔧 Step 8: Parsing structured request from [AGENT 2] TravelAdvisor agent using OpenAI function calling...")
            try:
                # The response is already an ItineraryRequest object from OpenAI function calling, convert to dict
                request_data = request_response.model_dump() if hasattr(request_response, 'model_dump') else json.loads(request_response)
                logger.info(f"✅ Successfully parsed structured request from OpenAI function calling: {request_data}")
                print(f"[DEBUG] ✅ Successfully parsed structured request from OpenAI function calling: {request_data}")
                
                # Step 9: TravelPlanner Agent (Agent 1) - Provide Default Values using OpenAI function calling
                logger.info("🔄 Step 9: [AGENT 1] TravelPlanner agent providing default values using OpenAI function calling...")
                print("[DEBUG] 🔄 Step 5: TravelPlanner.provide_defaults providing defaults using OpenAI function calling...")
                
                # Agent Tool Call: TravelPlanner.provide_defaults using OpenAI function calling
                # This agent function provides structured default values for missing information
                # Uses structured models for reliable communication between agents
                defaults_query = json.dumps(request_data["missing_items"])
                defaults_result = await kernel.invoke(plugin_name="TravelPlanner", function_name="provide_defaults", input=defaults_query)
                defaults_response = defaults_result.value[0].content
                
                logger.info(f"📋 [AGENT 1] TravelPlanner defaults response using OpenAI function calling: {defaults_response}")
                print(f"[DEBUG] 📋 TravelPlanner defaults response using OpenAI function calling: {defaults_response}")
                
                # Step 10: Parse Structured Default Values from OpenAI function calling
                logger.info("🔧 Step 10: Parsing structured defaults from [AGENT 1] TravelPlanner agent using OpenAI function calling...")
                try:
                    # The response is already a DefaultValues object from OpenAI function calling, convert to dict
                    defaults_data = defaults_response.model_dump() if hasattr(defaults_response, 'model_dump') else json.loads(defaults_response)
                    logger.info(f"✅ Successfully parsed structured defaults from OpenAI function calling: {defaults_data}")
                    print(f"[DEBUG] ✅ Successfully parsed structured defaults from OpenAI function calling: {defaults_data}")
                    
                    # Step 11: Update Travel Data with Defaults using OpenAI function calling
                    logger.info("🔧 Step 11: Updating travel data with default values using OpenAI function calling...")
                    
                    # Update original travel data with defaults from structured models
                    if "duration" in defaults_data and travel_data["duration"] is None:
                        travel_data["duration"] = defaults_data["duration"]
                        if "duration" in travel_data["missing_info"]:
                            travel_data["missing_info"].remove("duration")
                        logger.info(f"✅ Updated duration with default using OpenAI function calling: {defaults_data['duration']}")
                    
                    # Create updated JSON for TravelAdvisor using structured data
                    updated_json = json.dumps(travel_data)
                    logger.info(f"📋 Updated JSON with defaults using OpenAI function calling: {updated_json}")
                    print(f"[DEBUG] 📋 Updated JSON with defaults using OpenAI function calling: {updated_json}")
                    
                    # Step 12: TravelAdvisor Agent (Agent 2) - Create Final Itinerary using OpenAI function calling
                    logger.info("🔄 Step 12: [AGENT 2] TravelAdvisor agent creating final itinerary with complete data using OpenAI function calling...")
                    print("[DEBUG] 🔄 Step 6: TravelAdvisor.create_itinerary creating final itinerary using OpenAI function calling...")
                    
                    # Agent Tool Call: TravelAdvisor.create_itinerary (second call) using OpenAI function calling
                    # This agent function creates the final itinerary with complete information
                    # Uses structured models for reliable communication
                    final_advisor_result = await kernel.invoke(plugin_name="TravelAdvisor", function_name="create_itinerary", input=updated_json)
                    final_response = final_advisor_result.value[0].content
                    
                    logger.info(f"✅ [AGENT 2] Final TravelAdvisor response length using OpenAI function calling: {len(final_response)} characters")
                    print(f"[DEBUG] ✅ Final TravelAdvisor response length using OpenAI function calling: {len(final_response)} characters")
                    
                except Exception as e:
                    logger.error(f"❌ Structured defaults parsing error from OpenAI function calling: {e}")
                    print(f"[DEBUG] ❌ Structured defaults parsing error from OpenAI function calling: {e}")
                    return f"❌ Error: TravelPlanner returned invalid structured output from OpenAI function calling: {defaults_response}"
                    
            except Exception as e:
                logger.error(f"❌ Structured request parsing error from OpenAI function calling: {e}")
                print(f"[DEBUG] ❌ Structured request parsing error from OpenAI function calling: {e}")
                return f"❌ Error: TravelAdvisor returned invalid structured output from OpenAI function calling: {request_response}"
        else:
            # TravelAdvisor provided a complete response (itinerary) using OpenAI function calling
            logger.info("✅ [AGENT 2] TravelAdvisor provided complete response without missing information using OpenAI function calling")
            final_response = advisor_response
            print(f"[DEBUG] ✅ TravelAdvisor provided complete response using OpenAI function calling")
        
        # Step 13: TravelAdvisor Agent (Agent 2) - Enhance Final Itinerary using OpenAI function calling
        logger.info("🔄 Step 13: [AGENT 2] TravelAdvisor agent enhancing final itinerary with additional details using OpenAI function calling...")
        print("[DEBUG] 🔄 Step 7: TravelAdvisor.enhance_itinerary enhancing itinerary using OpenAI function calling...")
        
        # Agent Tool Call: TravelAdvisor.enhance_itinerary using OpenAI function calling
        # This agent function adds specific details like addresses, costs, booking info, etc.
        # Uses structured models for reliable enhancement
        enhanced_result = await kernel.invoke(plugin_name="TravelAdvisor", function_name="enhance_itinerary", input=final_response)
        enhanced_response = enhanced_result.value[0].content
        
        logger.info(f"✅ [AGENT 2] Enhanced response length using OpenAI function calling: {len(enhanced_response)} characters")
        print(f"[DEBUG] ✅ Enhanced response length using OpenAI function calling: {len(enhanced_response)} characters")
        
        # Step 14: Workflow Summary and Logging with OpenAI function calling
        logger.info("📊 Multi-agent workflow completed successfully using OpenAI function calling")
        print("\n" + "="*50)
        print("📊 Multi-Agent Workflow with OpenAI Function Calling Summary:")
        print(f"  🔍 TravelPlanner.analyze_request analyzed: {user_request}")
        print(f"  📋 JSON output using OpenAI function calling: {travel_data}")
        print(f"  ✨ TravelAdvisor.create_itinerary response length using OpenAI function calling: {len(final_response)} characters")
        print(f"  🚀 TravelAdvisor.enhance_itinerary enhanced response length using OpenAI function calling: {len(enhanced_response)} characters")
        print("="*50)
        
        # Log detailed workflow summary with OpenAI function calling
        logger.info("="*60)
        logger.info("MULTI-AGENT WORKFLOW SUMMARY USING OPENAI FUNCTION CALLING:")
        logger.info(f"  Input: {user_request}")
        logger.info(f"  [AGENT 1] TravelPlanner Analysis using OpenAI function calling: {travel_data}")
        logger.info(f"  [AGENT 2] Final Response Length using OpenAI function calling: {len(enhanced_response)} characters")
        logger.info(f"  Agent Interactions using OpenAI function calling: [AGENT 1] TravelPlanner → [AGENT 2] TravelAdvisor → [AGENT 1] TravelPlanner → [AGENT 2] TravelAdvisor")
        logger.info("="*60)
        
        return enhanced_response
        
    except Exception as e:
        logger.error(f"❌ Workflow error using OpenAI function calling: {type(e).__name__}: {str(e)}")
        print(f"[DEBUG] ❌ Workflow error using OpenAI function calling: {type(e).__name__}: {str(e)}")
        return f"❌ Error in multi-agent workflow using OpenAI function calling: {str(e)}"

async def interactive_demo_session_with_plugins():
    """
    Run an interactive demonstration session with plugins.
    
    This function provides a command-line interface for users to:
    1. Enter travel requests
    2. See the multi-agent workflow with plugins in action
    3. Exit the application
    
    Agent Interaction Flow:
    - User Input → [AGENT 1] TravelPlanner Agent (analyze_request) → [AGENT 2] TravelAdvisor Agent (create_itinerary)
    - If missing info: [AGENT 2] TravelAdvisor (request_missing_info) → [AGENT 1] TravelPlanner Agent (provide_defaults) → [AGENT 2] TravelAdvisor (final itinerary)
    - Final step: [AGENT 2] TravelAdvisor Agent (enhance_itinerary) → Enhanced Response
    """
    logger.info("🎯 Starting interactive demo session with multi-agent plugins")
    print("✈️ Microsoft Semantic Kernel Multi-Agent Travel Planner with Plugins")
    print("=" * 60)
    print("🤖 Two AI agent plugins will collaborate to help plan your trip!")
    print("   - TravelPlanner Plugin (Agent 1): Analyzes requests and provides defaults")
    print("   - TravelAdvisor Plugin (Agent 2): Creates and enhances itineraries")
    print("=" * 60)
    print("💡 Type your travel request below, or 'quit' to exit.")
    print("=" * 60)
    
    session_count = 0
    while True:
        try:
            session_count += 1
            logger.info(f"🔄 Starting session #{session_count}")
            print("\n" + "="*60)
            user_request = input("✈️ Your travel request: ").strip()
            logger.info(f"👤 User input received: '{user_request}'")
            print(f"[DEBUG] 👤 User input received: '{user_request}'")
            
            if user_request.lower() in ['quit', 'exit', 'q']:
                logger.info("👋 User requested to quit application")
                print("[DEBUG] 👋 User requested to quit")
                print("👋 Thank you for using the Microsoft Semantic Kernel Multi-Agent Plugin System!")
                break
            
            if not user_request:
                logger.warning("❌ Empty user input received")
                print("[DEBUG] ❌ Empty user input")
                print("❌ Please enter a valid travel request.")
                print("💡 Try: 'Plan a trip to Japan for cherry blossoms'")
                continue
            
            logger.info(f"🚀 Starting multi-agent workflow for session #{session_count}")
            print(f"[DEBUG] 🚀 Starting plugin workflow for: '{user_request}'")
            print("\n🔄 Running Microsoft Semantic Kernel Multi-Agent Plugin Workflow...")
            print("🤖 Plugin agents are collaborating to help you...")
            
            # Run the multi-agent workflow with plugins
            logger.info("🔄 Executing multi-agent workflow with plugins...")
            result = await run_multi_agent_workflow_with_plugins(user_request)
            
            if result and not result.startswith("❌"):
                logger.info(f"✅ Plugin workflow completed successfully for session #{session_count}")
                print(f"[DEBUG] ✅ Plugin workflow successful")
                print("\n" + "="*60)
                print("🎯 FINAL ENHANCED RESPONSE:")
                print("="*60)
                print(result)
                print("="*60)
                print("\n✅ Plugin workflow completed!")
                print("💡 Ask another question or type 'quit' to exit.")
            else:
                logger.error(f"❌ Plugin workflow failed for session #{session_count}")
                print(f"[DEBUG] ❌ Plugin workflow failed")
                print("\n❌ Plugin workflow failed. Please try again.")
                
        except KeyboardInterrupt:
            logger.info("⌨️ Keyboard interrupt received - shutting down gracefully")
            print(f"[DEBUG] ⌨️ Keyboard interrupt received")
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"❌ Exception in interactive session: {type(e).__name__}: {str(e)}")
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
    
    System Architecture:
    - Two specialized AI agents ([AGENT 1] TravelPlanner and [AGENT 2] TravelAdvisor)
    - Structured JSON communication between agents using OpenAI function calling
    - Plugin-based architecture using Microsoft Semantic Kernel
    - Detailed logging for agent interactions and tool calls
    """
    logger.info("🚀 Starting Microsoft Semantic Kernel Multi-Agent Travel Planning System")
    print("🚀 Starting Microsoft Semantic Kernel Multi-Agent Travel Planning System with Plugins")
    print("[DEBUG] 🚀 Main function with plugins started")
    
    # Step 1: Environment Setup
    logger.info("🔧 Step 1: Loading environment variables...")
    load_dotenv()
    print("[DEBUG] 📄 Environment variables loaded")
    
    # Step 2: API Key Validation
    logger.info("🔧 Step 2: Validating OpenAI API key...")
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OpenAI API key not found in environment variables")
        print("[DEBUG] ❌ OpenAI API key not found")
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    logger.info("✅ OpenAI API key validated successfully")
    print("[DEBUG] ✅ OpenAI API key found")
    print("✅ OpenAI API key loaded from .env file.")
    
    # Step 3: Display Example Requests
    logger.info("🔧 Step 3: Displaying example travel requests...")
    example_requests = [
        "Plan a trip to Japan for cherry blossoms.",
        "I want to visit Paris for 5 days.",
        "What should I know about traveling to Bali?",
        "Give me travel tips for New York City."
    ]
    
    print("\n📋 Example travel requests you can try:")
    for i, request in enumerate(example_requests, 1):
        print(f"{i}. {request}")
    
    logger.info("✅ Example requests displayed successfully")
    
    # Step 4: Start Interactive Session
    logger.info("🔧 Step 4: Starting interactive demonstration session...")
    print("\n🎯 Starting interactive demonstration mode with plugins...")
    print("[DEBUG] 🎯 Calling interactive_demo_session_with_plugins")
    await interactive_demo_session_with_plugins()
    
    logger.info("🏁 Main function completed successfully")
    print("[DEBUG] 🏁 Main function with plugins completed")

if __name__ == "__main__":
    asyncio.run(main_with_plugins()) 