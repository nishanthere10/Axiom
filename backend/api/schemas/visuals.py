from pydantic import BaseModel, Field
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

class ArchitectureDiagramSchema(BaseModel):
    type: Literal["architecture_diagram"] = "architecture_diagram"
    title: str = Field(description="Title of the architecture diagram")
    mermaid_syntax: str = Field(description='''Raw Mermaid JS syntax. 
CRITICAL RULES:
1. ONLY use 'graph TD' or 'graph LR'. No other types.
2. Node definitions MUST use brackets: ID[Label]. Keep labels short (max 4-5 words).
3. Edge definitions MUST use valid syntax: --> or -->|label|
4. NEVER use "note right:" or sequence diagram features in graphs.
5. NEVER use quotes outside brackets (e.g. a -- 'Label' is INVALID).
6. Do not wrap in markdown ``` codeblocks.
7. MAX 8 nodes total. Use subgraphs for logical grouping if needed.
Example:
graph TD
  subgraph Frontend
    A[Client App]
  end
  subgraph Backend
    B[Load Balancer] --> C[API Server]
  end
  A -->|HTTPS| B
''')

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
