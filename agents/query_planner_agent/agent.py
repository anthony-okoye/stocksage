import sys
import os
import asyncio
from uagents import Agent, Bureau, Context

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.config import settings
from libs.common.models import PlannerQueryRequest, SessionContext
from .client import GroqClient
from .service import PlanningService

# --- Agent Setup ---
if not settings.QUERY_PLANNER_AGENT_SEED:
    raise ValueError("QUERY_PLANNER_AGENT_SEED is not set in the environment.")

# Instantiate the layers
groq_client = GroqClient()
planning_service = PlanningService(groq_client)

# Create the agent
agent = Agent(
    name="QueryPlannerAgent",
    seed=settings.QUERY_PLANNER_AGENT_SEED,
)

bureau = Bureau()
bureau.add(agent)

@agent.on_event("startup")
async def startup(ctx: Context):
    """Log the agent's address on startup."""
    ctx.logger.info(f"Query Planner Agent started with address: {agent.address}")

@agent.on_query(model=PlannerQueryRequest, replies=SessionContext)
async def handle_query(ctx: Context, sender: str, msg: PlannerQueryRequest):
    """
    Handles incoming queries, uses the PlanningService to create a plan,
    and returns the updated SessionContext. This is a query handler,
    so it must return a value.
    """
    ctx.logger.info(f"Received query for session {msg.session_id} from {sender}: '{msg.query}'")
    
    try:
        session_context = await planning_service.create_plan_from_query(
            query=msg.query, 
            session_id=msg.session_id
        )
        ctx.logger.info(f"Plan created successfully for session {session_context.session_id}")
        return session_context
    except Exception as e:
        error_message = f"An error occurred while creating the plan: {e}"
        ctx.logger.error(error_message, exc_info=True)
        # Return a context with the failure status
        return SessionContext(
            session_id=msg.session_id,
            original_query=msg.query,
            status="planning_failed",
            final_report=error_message
        )

if __name__ == "__main__":
    bureau.run() 