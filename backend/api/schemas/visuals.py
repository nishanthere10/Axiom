import re
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Union, Optional

class DecisionTreeNode(BaseModel):
    id: str = Field(description="Unique identifier for the node (e.g. 'n1')")
    label: str = Field(description="Text to display inside the node")

class DecisionTreeEdge(BaseModel):
    source: str = Field(description="ID of the source node")
    target: str = Field(description="ID of the target node")
    label: Optional[str] = Field(None, description="Optional text to display on the edge")

class DecisionTreeSchema(BaseModel):
    type: Literal["decision_tree"] = "decision_tree"
    title: str = Field(description="Title of the decision tree")
    nodes: List[DecisionTreeNode] = Field(description="List of nodes in the decision tree. Maximum 8 nodes to ensure readability.", max_length=8)
    edges: List[DecisionTreeEdge] = Field(description="List of directed edges (connections) between nodes")

class FlowNode(BaseModel):
    id: str = Field(..., description="Unique alphanumeric ID (e.g., 'web_client')")
    label: str = Field(..., description="The display text for the node")
    type: str = Field("custom", description="Always use 'custom' to trigger our styled nodes")
    group: Optional[str] = Field(None, description="Optional: ID of the parent subgraph/group")

class FlowEdge(BaseModel):
    source: str = Field(..., description="ID of the source node")
    target: str = Field(..., description="ID of the target node")
    label: Optional[str] = Field(None, description="Optional text label for the arrow")
    animated: bool = Field(False, description="Set to true if representing active data flow")

class ArchitectureDiagramSchema(BaseModel):
    type: Literal["architecture_diagram"] = "architecture_diagram"
    title: str = Field(description="Title of the architecture diagram")
    nodes: List[FlowNode] = Field(description="List of architectural nodes. Maximum 8 nodes.")
    edges: List[FlowEdge] = Field(description="List of directional edges between nodes.")

class SummaryCardHighlight(BaseModel):
    label: str = Field(description="Label for the metric or highlight")
    value: str = Field(description="Value for the metric or highlight")

class SummaryCardSchema(BaseModel):
    type: Literal["summary_card"] = "summary_card"
    title: str = Field(description="Title of the summary card")
    summary: str = Field(description="High level summary of the recommendation")
    confidence: str = Field(description="Confidence level (e.g. High, Medium, Low)")
    consensus: str = Field(description="Industry consensus summary")
    highlights: List[SummaryCardHighlight] = Field(description="Key metrics or highlights")

VisualType = Union[DecisionTreeSchema, ArchitectureDiagramSchema, SummaryCardSchema]

class VisualSpecResponse(BaseModel):
    visuals: List[VisualType] = Field(
        description="A list of structured visual specifications (max 3). Return an empty list if no visuals are helpful or warranted for the topic.",
        max_length=3
    )
