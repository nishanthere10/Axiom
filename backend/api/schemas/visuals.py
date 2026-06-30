import re
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Union, Optional

NodeType = Literal["root", "decision", "outcome", "leaf"]
ArchNodeType = Literal["service", "database", "queue", "client", "gateway", "cache", "component"]
HighlightType = Literal["metric", "tradeoff", "warning", "recommendation"]

class DecisionTreeNode(BaseModel):
    id: str = Field(description="Unique identifier for the node (e.g. 'n1')")
    label: str = Field(description="Short text to display inside the node (max 5 words)")
    node_type: NodeType = Field(
        "leaf",
        description="Role of this node: 'root'=starting question, 'decision'=branch/choice point, 'outcome'=final recommendation, 'leaf'=intermediate step"
    )
    description: str = Field(
        description="REQUIRED. 1-2 sentence explanation with at least one specific number, metric, or technology version. Shown as tooltip AND preview on the node face."
    )

class DecisionTreeEdge(BaseModel):
    source: str = Field(description="ID of the source node")
    target: str = Field(description="ID of the target node")
    label: Optional[str] = Field(None, description="Condition or criteria on this branch (e.g. 'Write-heavy' or 'Need ACID?')")

class DecisionTreeSchema(BaseModel):
    type: Literal["decision_tree"] = "decision_tree"
    title: str = Field(description="Title of the decision tree")
    subtitle: Optional[str] = Field(None, description="1 sentence describing what decision this tree maps out")
    nodes: List[DecisionTreeNode] = Field(description="List of nodes. Generate 8-12 nodes for real depth. Must include exactly one 'root' node and at least one 'outcome' node.", max_length=12)
    edges: List[DecisionTreeEdge] = Field(description="List of directed edges (connections) between nodes")

class FlowNode(BaseModel):
    id: str = Field(..., description="Unique alphanumeric ID (e.g., 'web_client')")
    label: str = Field(..., description="Short display name for the component (e.g. 'React Frontend')")
    type: str = Field("custom", description="Always use 'custom'")
    node_type: ArchNodeType = Field(
        "component",
        description="Category: 'service'=microservice/API, 'database'=any DB/storage, 'queue'=Kafka/RabbitMQ/SQS, 'client'=frontend/user, 'gateway'=API gateway/LB, 'cache'=Redis/Memcached, 'component'=other"
    )
    description: str = Field(
        description="REQUIRED. 1-2 sentences: what this component does, technology used, key performance characteristic. Must include at least one concrete number or spec."
    )
    spec: Optional[str] = Field(
        None,
        description="Short 1-line metric shown directly on the node face — e.g. '50k writes/s', 'p99: 4ms', '3 replicas'. The single most important performance characteristic."
    )
    group: Optional[str] = Field(None, description="Optional: ID of the parent subgraph/group")

class FlowEdge(BaseModel):
    source: str = Field(..., description="ID of the source node")
    target: str = Field(..., description="ID of the target node")
    label: Optional[str] = Field(None, description="What data/event flows on this edge (e.g. 'User events', 'SQL queries')")
    animated: bool = Field(False, description="Set to true if representing active/real-time data flow")

class ArchitectureDiagramSchema(BaseModel):
    type: Literal["architecture_diagram"] = "architecture_diagram"
    title: str = Field(description="Title of the architecture diagram")
    subtitle: Optional[str] = Field(None, description="1 sentence: what architecture pattern this diagram shows")
    nodes: List[FlowNode] = Field(description="List of architectural nodes. Generate 8-15 nodes covering the full data path from client to storage, including caching and async layers.", max_length=15)
    edges: List[FlowEdge] = Field(description="List of directional edges between nodes.")

class SummaryCardHighlight(BaseModel):
    label: str = Field(description="Name of the metric, tradeoff, or insight")
    value: str = Field(description="Concrete value or short assessment (e.g. '~100k writes/s', 'Strong Consistency', 'High')")
    highlight_type: HighlightType = Field(
        "metric",
        description="'metric'=quantitative stat, 'tradeoff'=pro/con, 'warning'=risk or limitation, 'recommendation'=prescriptive advice"
    )

class SummaryCardSchema(BaseModel):
    type: Literal["summary_card"] = "summary_card"
    title: str = Field(description="Title of the summary card")
    summary: str = Field(description="1-2 sentence precise summary of the recommendation, naming exact technologies chosen")
    confidence: str = Field(description="Confidence level: 'High', 'Medium', or 'Low' — derived from evidence strength")
    consensus: str = Field(description="1 sentence: what the broader industry evidence says about this choice")
    highlights: List[SummaryCardHighlight] = Field(description="6-10 key metrics, tradeoffs, or insights. Must include at least 2 metrics with real numbers, 2 tradeoffs, 1 warning, 1 recommendation.", min_length=6, max_length=10)

VisualType = Union[DecisionTreeSchema, ArchitectureDiagramSchema, SummaryCardSchema]

class VisualSpecResponse(BaseModel):
    visuals: List[VisualType] = Field(
        description="A list of 1-3 structured visual specifications. Return an empty list ONLY for trivial non-technical topics.",
        max_length=3
    )

