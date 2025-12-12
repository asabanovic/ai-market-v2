"""State management for the AI agents system."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass
class AgentState:
    """Main state for the agent system.

    This state is passed through all nodes in the graph and accumulates
    information as the query is processed.
    """

    # Input
    query: str = field(default="")
    """The user's original query."""

    user_id: Optional[str] = field(default=None)
    """User ID for personalization."""

    business_ids: Optional[List[int]] = field(default=None)
    """Optional list of business IDs to filter results."""

    only_discounted: bool = field(default=False)
    """Filter to show only discounted products."""

    # Routing
    intent: Literal["semantic_search", "meal_planning", "general", "unknown"] = field(default="unknown")
    """Detected intent from the supervisor."""

    confidence: float = field(default=0.0)
    """Confidence score for the detected intent."""

    # Processing parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    """Extracted parameters for the agent (e.g., k, category, max_price)."""

    # Results
    results: List[Dict[str, Any]] = field(default_factory=list)
    """Results from the agent execution."""

    search_items: List[Dict[str, Any]] = field(default_factory=list)
    """Parsed search items from intent parser with expanded queries."""

    explanation: Optional[str] = field(default=None)
    """AI-generated explanation of the results."""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the execution."""

    error: Optional[str] = field(default=None)
    """Error message if something went wrong."""

    # Graph control
    next_node: Optional[str] = field(default=None)
    """Next node to execute (for dynamic routing)."""


@dataclass
class InputState:
    """Narrower input state exposed to the API."""

    query: str = field(default="")
    """The user's search query."""

    user_id: Optional[str] = field(default=None)
    """Optional user ID for personalization."""

    business_ids: Optional[List[int]] = field(default=None)
    """Optional list of business IDs to filter results."""

    only_discounted: bool = field(default=False)
    """Filter to show only discounted products."""


@dataclass
class OutputState:
    """Output state returned to the user."""

    query: str
    """The original query."""

    intent: str
    """Detected intent."""

    results: List[Dict[str, Any]]
    """Results from the agent."""

    explanation: Optional[str] = None
    """AI explanation."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Metadata about the execution."""

    error: Optional[str] = None
    """Error message if any."""
