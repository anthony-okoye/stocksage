import sys
import os
import asyncio
from uuid import uuid4

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from uagents import Agent, Bureau, Context, Model
from config.config import settings
from libs.common.models import PlannerQueryRequest, SessionContext, TaskResult

# --- API Models (for request/response validation) ---

class ApiQueryRequest(Model):
    query: str

class QueryResponse(Model):
    message: str
    session_id: str

class ReportResponse(Model):
    session_id: str
    status: str
    report: list[TaskResult] | str | None = None
    
# --- Agent and Bureau Setup ---
gateway_agent = Agent(
    name="APIGatewayAgent",
    seed=settings.API_GATEWAY_AGENT_SEED,
)

bureau = Bureau(endpoint=f"http://127.0.0.1:{settings.API_GATEWAY_PORT}/submit", port=settings.API_GATEWAY_PORT)
bureau.add(gateway_agent)

# In-memory storage for simplicity. In production, use a persistent store.
SESSION_STORE: dict[str, SessionContext] = {}

# --- Public API Endpoint ---

@gateway_agent.on_query(model=ApiQueryRequest, replies=QueryResponse)
async def handle_api_query(ctx: Context, sender: str, msg: ApiQueryRequest):
    """
    This is the public entry point for a user's query.
    It creates a session and starts the planning process.
    """
    session_id = str(uuid4())
    ctx.logger.info(f"New query received. Creating session ID: {session_id}")

    if not settings.QUERY_PLANNER_AGENT_ADDRESS:
        ctx.logger.error("QueryPlannerAgent address is not configured.")
        await ctx.send(sender, QueryResponse(message="Error: Query Planner is not configured.", session_id=""))
        return

    # Create the initial session context
    context = SessionContext(
        session_id=session_id,
        original_query=msg.query,
        status="planning"
    )
    SESSION_STORE[session_id] = context

    # Send the query to the planner and wait for the plan
    try:
        ctx.logger.info(f"Sending query to planner for session {session_id}")
        plan_response = await ctx.query(
            destination=settings.QUERY_PLANNER_AGENT_ADDRESS,
            message=PlannerQueryRequest(query=msg.query, session_id=session_id),
            timeout=60.0,
        )

        if isinstance(plan_response, SessionContext):
            ctx.logger.info(f"Plan received for session {session_id}")
            # Update the session with the plan
            planned_context = plan_response
            SESSION_STORE[session_id] = planned_context
            
            # Start the execution asynchronously
            asyncio.create_task(execute_agent_plan(planned_context, ctx.logger))

            await ctx.send(sender, QueryResponse(
                message="Query received and plan created. You can poll for results.",
                session_id=session_id
            ))
        else:
            ctx.logger.error(f"Invalid response from planner for session {session_id}: {plan_response}")
            context.status = "failed"
            context.final_report = "Failed to create a valid plan from the Query Planner."
            SESSION_STORE[session_id] = context
            await ctx.send(sender, QueryResponse(message="Error: Did not receive a valid plan.", session_id=session_id))
            
    except Exception as e:
        ctx.logger.error(f"Error querying planner for session {session_id}: {e}", exc_info=True)
        context.status = "failed"
        context.final_report = f"An exception occurred while contacting the Query Planner: {e}"
        SESSION_STORE[session_id] = context
        await ctx.send(sender, QueryResponse(message=f"Error: {e}", session_id=session_id))


# --- Internal Message Handlers ---

@gateway_agent.on_message(model=SessionContext)
async def on_final_context_received(ctx: Context, _sender: str, msg: SessionContext):
    """
    Handles the final, populated context from the last agent in the plan.
    This marks the process as complete.
    """
    session_id = str(msg.session_id)
    ctx.logger.info(f"Final context received for session {session_id}. Workflow complete.")
    
    msg.status = "completed"
    SESSION_STORE[session_id] = msg


# --- Status Check Endpoint ---

@gateway_agent.on_query(model=QueryResponse, replies=ReportResponse)
async def get_result(ctx: Context, sender: str, msg: QueryResponse):
    """Polls for the result of a query using the session_id."""
    session_id = msg.session_id
    context = SESSION_STORE.get(session_id)
    
    if not context:
        await ctx.send(sender, ReportResponse(session_id=session_id, status="not_found", report="Session ID not found."))
        return

    await ctx.send(sender, ReportResponse(
        session_id=session_id,
        status=context.status,
        report=context.execution_history if context.status == "completed" else "Processing..."
    ))

# --- Core Orchestration ---

async def execute_agent_plan(context: SessionContext, logger):
    """
    Executes the agent plan task by task.
    This function is now called asynchronously after a plan is received.
    """
    session_id = str(context.session_id)
    logger.info(f"Starting execution of plan for session {session_id}")
    
    if not context.planned_tasks:
        logger.warning(f"No tasks in plan for session {session_id}. Marking as complete.")
        context.status = "completed"
        context.final_report = "No tasks were planned for this query."
        SESSION_STORE[session_id] = context
        return

    # The plan execution is now a simple loop sending the context to the next agent.
    # The full context is passed, and each agent is responsible for updating it
    # and sending it to the next agent, or back to the gateway if it's the last one.
    first_task = context.planned_tasks[0]
    agent_name_upper = first_task.agent_name.upper().replace(" ", "_").replace("-", "_")
    address_key = f"{agent_name_upper}_AGENT_ADDRESS"
    
    # getattr needs to check the settings object
    first_agent_address = getattr(settings, address_key, None)

    if not first_agent_address:
        error_msg = f"Configuration error: Address for agent '{first_task.agent_name}' (config key: {address_key}) is not set."
        logger.error(error_msg)
        context.status = "failed"
        context.final_report = error_msg
        SESSION_STORE[session_id] = context
        return

    logger.info(f"Sending context for session {session_id} to first agent: {first_task.agent_name} at {first_agent_address}")
    # We use `send` not `query` as we don't need a direct response here.
    # The final agent in the chain will send the completed context back to our `on_final_context_received` handler.
    await gateway_agent.send(
        destination=first_agent_address,
        message=context
    )

if __name__ == "__main__":
    bureau.run()
