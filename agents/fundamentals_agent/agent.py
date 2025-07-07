import sys
import os
import asyncio
from uagents import Agent, Bureau, Context

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.config import settings
from libs.common.models import SessionContext, PlannerTask, TaskResult
from .client import YahooFinanceClient
from .service import FundamentalsService

# --- Agent Setup ---
if not settings.FUNDAMENTALS_AGENT_SEED:
    raise ValueError("FUNDAMENTALS_AGENT_SEED is not set in the environment.")

# Instantiate the layers
yahoo_client = YahooFinanceClient()
fundamentals_service = FundamentalsService(yahoo_client)

# Create the agent
agent = Agent(
    name="FundamentalsAgent",
    seed=settings.FUNDAMENTALS_AGENT_SEED,
)

bureau = Bureau()
bureau.add(agent)

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Fundamentals Agent started with address: {agent.address}")

@agent.on_message(model=SessionContext)
async def handle_request(ctx: Context, sender: str, msg: SessionContext):
    """
    Handles requests to fetch fundamental data.
    It iterates through its assigned tasks, executes them, and forwards the context.
    """
    ctx.logger.info(f"Received session {msg.session_id} from {sender}")

    # Process all tasks assigned to this agent
    tasks_for_this_agent = [
        task for task in msg.planned_tasks 
        if task.agent_name == agent.name and task.status == "pending"
    ]

    for task in tasks_for_this_agent:
        ctx.logger.info(f"Executing task {task.task_id}: {task.instructions}")
        try:
            result_data = await fundamentals_service.get_fundamental_data(task)
            task_result = TaskResult(
                task_id=task.task_id,
                result=str(result_data) # Ensure result is a string
            )
            msg.execution_history.append(task_result)
            task.status = "completed"
            ctx.logger.info(f"Task {task.task_id} completed successfully.")
        except Exception as e:
            error_message = f"Error executing task {task.task_id}: {e}"
            ctx.logger.error(error_message, exc_info=True)
            task.status = "failed"
            task_result = TaskResult(
                task_id=task.task_id,
                result=error_message
            )
            msg.execution_history.append(task_result)

    await forward_to_next_agent(ctx, msg)

def find_next_pending_task(context: SessionContext) -> PlannerTask | None:
    """Finds the first task in the plan that is still pending."""
    for task in context.planned_tasks:
        if task.status == "pending":
            return task
    return None

async def forward_to_next_agent(ctx: Context, context: SessionContext):
    """
    Determines the next agent based on the plan and forwards the context.
    If no tasks are left, it sends the final context back to the gateway.
    """
    next_task = find_next_pending_task(context)

    if not next_task:
        ctx.logger.info(f"All tasks for session {context.session_id} are complete. Returning to gateway.")
        # All tasks are done, send the final context back to the API Gateway
        if settings.API_GATEWAY_AGENT_ADDRESS:
            await ctx.send(settings.API_GATEWAY_AGENT_ADDRESS, context)
        else:
            ctx.logger.error("API_GATEWAY_AGENT_ADDRESS not set. Cannot return final context.")
        return

    # Determine the address of the agent for the next task
    agent_name_upper = next_task.agent_name.upper().replace(" ", "_").replace("-", "_")
    address_key = f"{agent_name_upper}_AGENT_ADDRESS"
    next_agent_address = getattr(settings, address_key, None)

    if next_agent_address:
        ctx.logger.info(f"Forwarding session {context.session_id} to next agent: {next_task.agent_name}")
        await ctx.send(next_agent_address, context)
    else:
        error_msg = f"Configuration error: Address for agent '{next_task.agent_name}' (config key: {address_key}) is not set. Workflow stopped."
        ctx.logger.error(error_msg)
        # To-Do: Should we send a failure message back to the gateway here?

if __name__ == "__main__":
    bureau.run() 