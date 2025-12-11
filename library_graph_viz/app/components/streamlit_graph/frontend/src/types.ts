// Node data structure matching current Python implementation
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  title?: string;
  size?: number;
  color?: string;
  shape?: string;
}

// Edge data structure
export interface GraphEdge {
  from: string;
  to: string;
  label?: string;
  title?: string;
  color?: string;
}

// Physics layout type
export type PhysicsLayout = 'barnes_hut' | 'force_atlas';

// Physics configuration
export interface PhysicsConfig {
  layout: PhysicsLayout;
  gravity: number;
  centralGravity: number;
  springLength: number;
  springStrength: number;
  damping: number;
}

// Component props from Python
export interface GraphComponentArgs {
  nodes: GraphNode[];
  edges: GraphEdge[];
  physics: PhysicsConfig;
  height: number;
  directed: boolean;
  multiSelect: boolean;
}

// Event types sent back to Python
export type GraphEventType = 'nodeClick' | 'nodeSelect' | 'edgeClick' | 'hover' | 'doubleClick';

export interface GraphEvent {
  type: GraphEventType;
  nodeId?: string;
  nodeIds?: string[];
  edgeId?: string;
  nodeData?: GraphNode;
  edgeData?: GraphEdge;
}
