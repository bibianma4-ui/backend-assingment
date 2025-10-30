"""
Backend API for VectorShift Pipeline Assessment

This module implements the FastAPI backend with pipeline validation,
DAG detection, and node/edge counting functionality.
"""

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="VectorShift Pipeline API",
    description="API for validating and parsing pipeline configurations",
    version="1.0.0"
)

# Configure CORS to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NodeData(BaseModel):
    """Pydantic model for node data validation"""
    id: str
    nodeType: str


class EdgeData(BaseModel):
    """Pydantic model for edge data validation"""
    id: str
    source: str
    target: str
    sourceHandle: str
    targetHandle: str


def build_adjacency_list(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Build adjacency list representation of the graph for DAG detection.
    
    Args:
        nodes: List of node objects from the pipeline
        edges: List of edge objects connecting nodes
        
    Returns:
        Dictionary mapping node IDs to lists of connected node IDs
    """
    logger.info("📊 Building adjacency list from graph structure")
    logger.info(f"   Nodes: {len(nodes)}, Edges: {len(edges)}")
    
    adjacency_list = {node['id']: [] for node in nodes}
    
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        
        if source and target and source in adjacency_list:
            if target not in adjacency_list[source]:
                adjacency_list[source].append(target)
                logger.debug(f"   Added edge: {source} → {target}")
    
    logger.info("✅ Adjacency list built successfully")
    logger.info(f"   Graph structure: {adjacency_list}")
    return adjacency_list


def detect_cycles_dfs(node: str, adjacency_list: Dict[str, List[str]], visited: set, rec_stack: set) -> bool:
    """
    Detect cycles in directed graph using depth-first search.
    
    Args:
        node: Current node being processed
        adjacency_list: Graph representation
        visited: Set of nodes that have been visited
        rec_stack: Set of nodes in current recursion stack
        
    Returns:
        True if cycle detected, False otherwise
    """
    visited.add(node)
    rec_stack.add(node)
    logger.debug(f"   Visiting node: {node}")
    
    # Check all neighbors
    for neighbor in adjacency_list.get(node, []):
        if neighbor not in visited:
            if detect_cycles_dfs(neighbor, adjacency_list, visited, rec_stack):
                logger.warning(f"   ⚠️  CYCLE DETECTED: {node} → {neighbor}")
                return True
        elif neighbor in rec_stack:
            logger.warning(f"   ⚠️  CYCLE DETECTED: {node} → {neighbor} (back edge)")
            return True
    
    rec_stack.remove(node)
    return False


def is_dag(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
    """
    Determine if the pipeline forms a Directed Acyclic Graph (DAG).
    
    Uses DFS-based cycle detection algorithm.
    
    Args:
        nodes: List of node objects
        edges: List of edge objects
        
    Returns:
        True if graph is acyclic (DAG), False otherwise
    """
    logger.info("🔍 Starting DAG validation...")
    
    if not nodes:
        logger.info("   Empty graph detected - considered valid DAG")
        return True
    
    adjacency_list = build_adjacency_list(nodes, edges)
    visited = set()
    rec_stack = set()
    
    # Check for cycles starting from each unvisited node
    logger.info("   Checking for cycles using DFS algorithm...")
    for node in adjacency_list.keys():
        if node not in visited:
            if detect_cycles_dfs(node, adjacency_list, visited, rec_stack):
                logger.warning("   ❌ CYCLE DETECTED - Not a valid DAG")
                return False
    
    logger.info("   ✅ No cycles found - Valid DAG")
    return True


@app.get('/')
def read_root():
    """
    Health check endpoint.
    
    Returns:
        Simple ping-pong response to verify API is running
    """
    return {'Ping': 'Pong'}


@app.post('/pipelines/parse')
async def parse_pipeline(pipeline: str = Form(...)):
    """
    Parse and validate pipeline configuration.
    
    This endpoint:
    1. Parses the JSON pipeline string
    2. Counts nodes and edges
    3. Validates the graph structure (DAG check)
    
    Args:
        pipeline: JSON string containing nodes and edges
        
    Returns:
        Dictionary with num_nodes, num_edges, and is_dag
        
    Raises:
        HTTPException: If pipeline data is invalid or malformed
    """
    logger.info("=" * 70)
    logger.info("🚀 NEW PIPELINE VALIDATION REQUEST RECEIVED")
    logger.info("=" * 70)
    
    try:
        # Parse JSON string to Python dictionary
        logger.info("📥 Parsing pipeline data from request...")
        pipeline_data = json.loads(pipeline)
        logger.info("✅ Successfully parsed JSON data")
        
        # Extract nodes and edges from parsed data
        nodes = pipeline_data.get('nodes', [])
        edges = pipeline_data.get('edges', [])
        
        logger.info("📊 Extracted pipeline components:")
        logger.info(f"   ├─ Nodes: {len(nodes)}")
        logger.info(f"   └─ Edges: {len(edges)}")
        
        # Validate that nodes and edges are lists
        if not isinstance(nodes, list):
            logger.error("❌ Validation error: Nodes must be a list")
            raise HTTPException(status_code=400, detail="Nodes must be a list")
        
        if not isinstance(edges, list):
            logger.error("❌ Validation error: Edges must be a list")
            raise HTTPException(status_code=400, detail="Edges must be a list")
        
        # Log detailed node information
        logger.info("")
        logger.info("🗂️  Node Details:")
        for i, node in enumerate(nodes, 1):
            node_type = node.get('type', 'unknown')
            node_id = node.get('id', 'unknown')
            logger.info(f"   {i}. Type: {node_type}, ID: {node_id}")
        
        logger.info("")
        logger.info("🔗 Edge Details:")
        for i, edge in enumerate(edges, 1):
            source = edge.get('source', 'unknown')
            target = edge.get('target', 'unknown')
            logger.info(f"   {i}. {source} → {target}")
        
        # Calculate pipeline statistics
        num_nodes = len(nodes)
        num_edges = len(edges)
        
        logger.info("")
        logger.info("📈 Calculating pipeline statistics...")
        
        # Check if pipeline forms a DAG
        is_valid_dag = is_dag(nodes, edges)
        
        # Prepare response
        response = {
            'num_nodes': num_nodes,
            'num_edges': num_edges,
            'is_dag': is_valid_dag
        }
        
        logger.info("")
        logger.info("╔════════════════════════════════════════════════════════════╗")
        logger.info("║              ✅ VALIDATION COMPLETE                        ║")
        logger.info("╚════════════════════════════════════════════════════════════╝")
        logger.info("📊 Validation Results:")
        logger.info(f"   ├─ Total Nodes: {num_nodes}")
        logger.info(f"   ├─ Total Edges: {num_edges}")
        logger.info(f"   ├─ Is Valid DAG: {is_valid_dag}")
        logger.info(f"   └─ Status: {'🟢 VALID - Ready for execution' if is_valid_dag else '🔴 INVALID - Contains cycles'}")
        logger.info("")
        logger.info("📤 Sending response to frontend...")
        logger.info("=" * 70)
        logger.info("")
        
        return response
        
    except json.JSONDecodeError as e:
        logger.error("❌ JSON parsing failed")
        logger.error(f"   Error: {str(e)}")
        logger.info("=" * 70)
        logger.info("")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        logger.info("=" * 70)
        logger.info("")
        raise
    except Exception as e:
        logger.error("❌ Unexpected error occurred")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Error message: {str(e)}")
        logger.info("=" * 70)
        logger.info("")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
