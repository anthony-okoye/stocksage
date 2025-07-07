# NOTE: This file's content has been regenerated due to previous file read errors.
import json
import sys
import os
from typing import List

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from libs.common.models import SessionContext, PlannerTask
from .client import GroqClient

class PlanningService:
    """
    This service is responsible for creating a task plan from a user query
    by interacting with the Groq API via the GroqClient.
    """

    def __init__(self, groq_client: GroqClient):
        self.groq_client = groq_client
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Loads the prompt template from a file."""
        # A real implementation would likely load this from a file.
        # For now, we define it here for simplicity.
        return """
            You are a master financial research planner. Your task is to take a user's query
            and break it down into a series of precise, executable tasks for a team of AI agents.
            The available agents are: "FundamentalsAgent", "TechnicalsAgent", and "SentimentAgent".

            Based on the user's query, create a JSON object that represents the plan.
            The JSON object should have a single key, "plan", which is an array of tasks.
            Each task object in the array must have the following properties:
            - "task_id": A unique integer identifier for the task, starting from 1.
            - "agent_name": The name of the agent assigned to this task.
            - "tool_name": The specific tool the agent should use.
            - "instructions": A clear, concise instruction for the agent.

            Here are the tools available for each agent:
            - "FundamentalsAgent": "get_company_overview", "get_income_statement", "get_balance_sheet", "get_cash_flow"
            - "TechnicalsAgent": "get_historical_prices", "calculate_sma", "calculate_ema", "calculate_rsi"
            - "SentimentAgent": "get_market_news", "analyze_social_media_sentiment"

            Analyze the user's query and select the appropriate agent and tool for each step.
            Be logical and efficient. For example, to analyze fundamentals, you might first get the company overview
            to find the stock ticker, then fetch the financial statements.

            User Query: "{query}"

            Produce only the JSON object in your response.
        """

    def _build_prompt(self, query: str) -> str:
        """Builds the full prompt from the template and user query."""
        return self._prompt_template.format(query=query)

    async def create_plan_from_query(self, query: str, session_id: str) -> SessionContext:
        """
        Creates a structured plan from a natural language query.

        Args:
            query: The user's research query.
            session_id: The unique ID for this session.

        Returns:
            A SessionContext object populated with the generated plan.
        """
        prompt = self._build_prompt(query)
        
        # Get the JSON plan from the Groq client
        json_response = await self.groq_client.create_chat_completion(prompt)
        
        # Parse the JSON response to extract the plan
        plan_data = json.loads(json_response)
        
        # Create PlannerTask objects from the plan data
        tasks: List[PlannerTask] = []
        for task_item in plan_data.get("plan", []):
            task = PlannerTask(
                task_id=task_item["task_id"],
                agent_name=task_item["agent_name"],
                tool_name=task_item["tool_name"],
                instructions=task_item["instructions"],
                status="pending"
            )
            tasks.append(task)
            
        # Create and return the session context
        return SessionContext(
            session_id=session_id,
            original_query=query,
            status="plan_created",
            planned_tasks=tasks
        ) 