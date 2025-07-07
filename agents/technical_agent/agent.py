import sys
import os
from uagents import Agent, Context, Model

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.config import settings
from libs.common.models import SessionContext, AgentResult, Task
from .client import OHLVC_Client
from .service import TechnicalAnalysisService

# --- Agent Setup ---
if not settings.TECHNICAL_AGENT_SEED:
    raise ValueError("TECHNICAL_AGENT_SEED is not set.")

# Instantiate the layers
ohlvc_client = OHLVC_Client()
technical_service = TechnicalAnalysisService(ohlvc_client)

# Create the agent
agent = Agent(
    name="TechnicalAgent",
    seed=settings.TECHNICAL_AGENT_SEED,
)

class TechnicalRequest(Model):
    context: SessionContext

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Technical Agent address: {agent.address}")

@agent.on_message(model=TechnicalRequest)
async def handle_request(ctx: Context, sender: str, msg: TechnicalRequest):
    """
    Handles requests to calculate technical indicators.
    """
    ctx.logger.info(f"Received request for session: {msg.context.session_id}")
    
    next_task = find_next_task_for_agent(agent.name, msg.context)

    if not next_task:
        ctx.logger.warning("No pending tasks found for this agent. Forwarding context.")
        await forward_to_next_agent(ctx, msg.context)
        return

    ctx.logger.info(f"Executing task: {next_task.action} for {next_task.params.get('ticker')}")
    result_data = technical_service.calculate_indicators(next_task)
    
    agent_result = AgentResult(task_completed=next_task, output=result_data)
    msg.context.execution_history.append(agent_result)
    
    ctx.logger.info("Task completed. Forwarding context.")
    await forward_to_next_agent(ctx, msg.context)

def find_next_task_for_agent(agent_name: str, context: SessionContext) -> Task | None:
    """Finds the first unfinished task assigned to any agent or a specific agent."""
    completed_tasks_ids = {
        (res.task_completed.agent_name, res.task_completed.action, tuple(sorted(res.task_completed.params.items())))
        for res in context.execution_history
    }

    for task in context.planned_tasks:
        task_id = (task.agent_name, task.action, tuple(sorted(task.params.items())))
        if task_id not in completed_tasks_ids:
            if agent_name == "any" or task.agent_name == agent_name:
                return task
    return None

async def forward_to_next_agent(ctx: Context, context: SessionContext):
    """
    Determines the next agent based on the plan and forwards the context.
    """
    next_task = find_next_task_for_agent("any", context)

    if not next_task:
        ctx.logger.info("All tasks completed. Returning final context to gateway.")
        context.status = "execution_complete"
        next_agent_address = settings.API_GATEWAY_ADDRESS
    else:
        agent_name_upper = next_task.agent_name.upper()
        address_key = f"{agent_name_upper}_ADDRESS"
        next_agent_address = getattr(settings, address_key, None)

    if next_agent_address:
        await ctx.send(next_agent_address, SessionContext.construct(**context.dict()))
        ctx.logger.info(f"Forwarded context to {next_agent_address}")
    else:
        error_msg = f"Could not determine next agent address for {next_task.agent_name if next_task else 'gateway'}. Flow stopped."
        ctx.logger.error(error_msg)

if __name__ == "__main__":
    agent.run() 