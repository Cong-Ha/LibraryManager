import { useEffect, useRef, useCallback, useState } from 'react';
import { Network, Options, Data } from 'vis-network';
import { DataSet } from 'vis-data';
import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from 'streamlit-component-lib';
import { GraphComponentArgs, GraphEvent } from './types';
import './styles.css';

// Use any for DataSet to avoid complex type issues with vis-network
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type VisDataSet = DataSet<any>;

// Loading spinner component
function LoadingSpinner({ height }: { height: number }) {
  return (
    <div
      className="loading-container"
      style={{ height: `${height}px` }}
    >
      <div className="loading-spinner">
        <div className="spinner"></div>
        <div className="loading-text">Loading graph...</div>
      </div>
    </div>
  );
}

// Physics presets matching current PyVis configuration
const PHYSICS_PRESETS: Record<string, Options['physics']> = {
  barnes_hut: {
    enabled: true,
    solver: 'barnesHut',
    barnesHut: {
      gravitationalConstant: -3000,
      centralGravity: 0.3,
      springLength: 200,
      springConstant: 0.001,
      damping: 0.09,
    },
    stabilization: {
      enabled: true,
      iterations: 1000,
      updateInterval: 25,
    },
  },
  force_atlas: {
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {
      gravitationalConstant: -80,
      centralGravity: 0.005,
      springLength: 150,
      springConstant: 0.04,
      damping: 0.4,
    },
    stabilization: {
      enabled: true,
      iterations: 1000,
      updateInterval: 25,
    },
  },
};

function GraphComponent({ args }: ComponentProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const nodesDataRef = useRef<VisDataSet | null>(null);
  const edgesDataRef = useRef<VisDataSet | null>(null);
  const hasInitializedRef = useRef<boolean>(false);
  const [currentLayout, setCurrentLayout] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const loadingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const {
    nodes,
    edges,
    physics,
    height,
    directed,
    multiSelect,
  } = args as GraphComponentArgs;

  // Send event to Python
  const sendEvent = useCallback((event: GraphEvent) => {
    Streamlit.setComponentValue(event);
  }, []);

  // Update physics without rebuilding network
  const updatePhysics = useCallback((layout: string) => {
    if (networkRef.current && layout !== currentLayout) {
      const physicsOptions = PHYSICS_PRESETS[layout] || PHYSICS_PRESETS.barnes_hut;
      networkRef.current.setOptions({ physics: physicsOptions });
      setCurrentLayout(layout);
    }
  }, [currentLayout]);

  // Initialize or update network
  useEffect(() => {
    if (!containerRef.current) return;

    const isInitialLoad = !networkRef.current;

    // Prepare node data with vis-network format
    const visNodes = nodes.map((n) => ({
      id: n.id,
      label: n.label,
      title: n.title || `${n.type}: ${n.label}`,
      size: n.size || 25,
      color: n.color || '#888888',
      shape: n.shape || 'dot',
      font: { color: '#ffffff' },
    }));

    // Prepare edge data with vis-network format
    // Use index in ID to handle multiple edges between same nodes
    const visEdges = edges.map((e, index) => ({
      id: `${e.from}-${e.to}-${index}`,
      from: e.from,
      to: e.to,
      label: e.label || '',
      title: e.title || e.label || '',
      color: e.color || '#888888',
    }));

    // Create network if not exists
    if (!networkRef.current) {
      // Initialize DataSets
      nodesDataRef.current = new DataSet(visNodes);
      edgesDataRef.current = new DataSet(visEdges);

      const options: Options = {
        nodes: {
          font: {
            size: 14,
            face: 'arial',
            color: '#ffffff',
          },
          borderWidth: 2,
          borderWidthSelected: 4,
        },
        edges: {
          color: { inherit: false },
          smooth: true,
          font: {
            size: 10,
            color: '#ffffff',
            strokeWidth: 0,
          },
          arrows: directed
            ? { to: { enabled: true, scaleFactor: 0.5 } }
            : {},
        },
        interaction: {
          hover: true,
          tooltipDelay: 100,
          hideEdgesOnDrag: true,
          navigationButtons: true,
          keyboard: { enabled: true },
          multiselect: multiSelect,
        },
        physics: PHYSICS_PRESETS[physics.layout] || PHYSICS_PRESETS.barnes_hut,
      };

      const data: Data = {
        nodes: nodesDataRef.current,
        edges: edgesDataRef.current,
      };

      networkRef.current = new Network(containerRef.current, data, options);
      setCurrentLayout(physics.layout);

      // TODO: Fix loading spinner timing issue
      // The spinner currently hides before nodes are visually rendered, causing
      // a brief black screen. The vis-network stabilization events fire before
      // the canvas is painted. Need to find a reliable way to detect when the
      // graph is actually visible on screen (not just when physics calculations
      // are complete). Possible approaches to try:
      // - Use IntersectionObserver on canvas
      // - Check canvas pixel data for non-background colors
      // - Use MutationObserver to detect vis-network DOM changes
      // - Investigate if Streamlit re-renders are causing the issue

      // Only show loading spinner if graph takes more than 200ms to stabilize
      // This avoids flash for fast graphs, but shows spinner for slow ones
      loadingTimerRef.current = setTimeout(() => {
        if (!hasInitializedRef.current) {
          setIsLoading(true);
        }
      }, 200);

      // Hide spinner when stabilization is done
      networkRef.current.once('stabilizationIterationsDone', () => {
        if (loadingTimerRef.current) {
          clearTimeout(loadingTimerRef.current);
          loadingTimerRef.current = null;
        }
        hasInitializedRef.current = true;
        setIsLoading(false);
      });

      // Fallback in case stabilization doesn't fire
      setTimeout(() => {
        if (loadingTimerRef.current) {
          clearTimeout(loadingTimerRef.current);
          loadingTimerRef.current = null;
        }
        hasInitializedRef.current = true;
        setIsLoading(false);
      }, 5000);

      // Event handlers
      networkRef.current.on('click', (params: { nodes: string[]; edges: string[] }) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const nodeData = nodesDataRef.current?.get(nodeId);
          if (nodeData) {
            sendEvent({
              type: 'nodeClick',
              nodeId,
              nodeData,
            });
          }
        } else if (params.edges.length > 0) {
          const edgeId = params.edges[0];
          const edgeData = edgesDataRef.current?.get(edgeId);
          if (edgeData) {
            sendEvent({
              type: 'edgeClick',
              edgeId,
              edgeData,
            });
          }
        }
      });

      networkRef.current.on('doubleClick', (params: { nodes: string[] }) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const nodeData = nodesDataRef.current?.get(nodeId);
          if (nodeData) {
            sendEvent({
              type: 'doubleClick',
              nodeId,
              nodeData,
            });
          }
        }
      });

      networkRef.current.on('selectNode', (params: { nodes: string[] }) => {
        sendEvent({
          type: 'nodeSelect',
          nodeIds: params.nodes,
        });
      });

      networkRef.current.on('hoverNode', (params: { node: string }) => {
        const nodeData = nodesDataRef.current?.get(params.node);
        if (nodeData) {
          sendEvent({
            type: 'hover',
            nodeId: params.node,
            nodeData,
          });
        }
      });
    } else {
      // Update existing network data
      nodesDataRef.current?.clear();
      nodesDataRef.current?.add(visNodes);
      edgesDataRef.current?.clear();
      edgesDataRef.current?.add(visEdges);

      // Update physics if changed
      if (physics.layout !== currentLayout) {
        updatePhysics(physics.layout);
      }
    }

    // Set frame height for Streamlit
    Streamlit.setFrameHeight(height);
  }, [nodes, edges, physics, height, directed, multiSelect, sendEvent, updatePhysics, currentLayout]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
        loadingTimerRef.current = null;
      }
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, []);

  return (
    <div style={{ position: 'relative', width: '100%', height: `${height}px` }}>
      <div
        ref={containerRef}
        className="graph-container"
        style={{
          height: `${height}px`,
          width: '100%',
          backgroundColor: '#0e1117',
        }}
      />
      {isLoading && <LoadingSpinner height={height} />}
    </div>
  );
}

export default withStreamlitConnection(GraphComponent);
