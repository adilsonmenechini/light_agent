"""Console subscriber that prints thinking events."""

from rich.console import Console

from light_agent.core.events import Event, EventBus, EventType

console = Console()


def format_thinking(event: Event) -> str:
    """Format a thinking event for console output."""
    data = event.data

    parts = ["[cyan]Thinking:[/]"]

    if data.get("agent"):
        parts.append(f"[yellow]{data['agent']}[/]")
    if data.get("tool"):
        parts.append(f"[green]using {data['tool']}[/]")

    parts.append(data["message"])

    return " ".join(parts)


def on_thinking(event: Event) -> None:
    """Handle thinking events."""
    console.print(format_thinking(event))


def on_tool_start(event: Event) -> None:
    """Handle tool start events."""
    data = event.data
    console.print(f"[cyan]Thinking:[/] [green]using {data['name']}[/]")


def on_tool_end(event: Event) -> None:
    """Handle tool end events."""
    data = event.data
    result = data.get("result_preview", "")
    if result:
        console.print(f"[cyan]Thinking:[/] tool [green]{data['name']}[/] done: {result}...")
    else:
        console.print(f"[cyan]Thinking:[/] tool [green]{data['name']}[/] done")


def on_tool_error(event: Event) -> None:
    """Handle tool error events."""
    data = event.data
    console.print(f"[red]Thinking:[/] tool [green]{data['name']}[/] error: {data['error']}")


def on_agent_start(event: Event) -> None:
    """Handle agent start events."""
    data = event.data
    console.print(f"[cyan]Thinking:[/] [yellow]agent {data['name']}[/]: {data['task']}...")


def on_agent_end(event: Event) -> None:
    """Handle agent end events."""
    data = event.data
    console.print(f"[cyan]Thinking:[/] agent [yellow]{data['name']}[/] done")


def on_llm_call(event: Event) -> None:
    """Handle LLM call events."""
    data = event.data
    console.print(
        f"[cyan]Thinking:[/] [blue]LLM[/] calling {data['model']} ({data['message_count']} messages)"
    )


def on_llm_response(event: Event) -> None:
    """Handle LLM response events."""
    data = event.data
    preview = data.get("response_preview", "")
    console.print(f"[cyan]Thinking:[/] [blue]LLM[/] response from {data['model']}: {preview}...")


def setup_console_subscriber(bus: EventBus) -> None:
    """Register all console subscribers."""
    bus.subscribe(EventType.THINKING, on_thinking)
    bus.subscribe(EventType.TOOL_START, on_tool_start)
    bus.subscribe(EventType.TOOL_END, on_tool_end)
    bus.subscribe(EventType.TOOL_ERROR, on_tool_error)
    bus.subscribe(EventType.AGENT_START, on_agent_start)
    bus.subscribe(EventType.AGENT_END, on_agent_end)
    bus.subscribe(EventType.LLM_CALL, on_llm_call)
    bus.subscribe(EventType.LLM_RESPONSE, on_llm_response)


def remove_console_subscriber(bus: EventBus) -> None:
    """Remove console subscribers."""
    bus.unsubscribe(EventType.THINKING, on_thinking)
    bus.unsubscribe(EventType.TOOL_START, on_tool_start)
    bus.unsubscribe(EventType.TOOL_END, on_tool_end)
    bus.unsubscribe(EventType.TOOL_ERROR, on_tool_error)
    bus.unsubscribe(EventType.AGENT_START, on_agent_start)
    bus.unsubscribe(EventType.AGENT_END, on_agent_end)
    bus.unsubscribe(EventType.LLM_CALL, on_llm_call)
    bus.unsubscribe(EventType.LLM_RESPONSE, on_llm_response)
