import * as d3 from "d3";
import { GraphNode, GraphEdge } from "./types";
import {
  DEFAULT_LINK_DISTANCE,
  DEFAULT_CHARGE_STRENGTH,
  DEFAULT_COLLISION_RADIUS_MULTIPLIER,
  BOUNDARY_FORCE_STRENGTH,
  CENTER_FORCE_STRENGTH,
  LINK_STRENGTH,
  ALPHA_DECAY,
  VELOCITY_DECAY,
} from "./constants";

/**
 * Creates and configures the D3 force simulation
 */
export const createSimulation = (nodes: GraphNode[], edges: GraphEdge[], width: number, height: number, nodeRadius: number): d3.Simulation<GraphNode, GraphEdge> => {
  return (
    d3
      .forceSimulation<GraphNode>(nodes)
      .force(
        "link",
        d3
          .forceLink<GraphNode, GraphEdge>(edges)
          .id((d) => d.id)
          .distance(DEFAULT_LINK_DISTANCE)
          .strength(LINK_STRENGTH) // Force de liaison pour garder les nœuds connectés ensemble
      )
      .force("charge", d3.forceManyBody().strength(DEFAULT_CHARGE_STRENGTH))
      .force("center", d3.forceCenter(width / 2, height / 2).strength(CENTER_FORCE_STRENGTH)) // Force vers le centre avec intensité modérée
      .force("collision", d3.forceCollide().radius(nodeRadius + DEFAULT_COLLISION_RADIUS_MULTIPLIER))
      // Forces de contrainte X et Y pour garder les nœuds dans les limites de l'écran
      .force(
        "x",
        d3.forceX(width / 2).strength(BOUNDARY_FORCE_STRENGTH) // Attire doucement les nœuds vers le centre horizontal
      )
      .force(
        "y",
        d3.forceY(height / 2).strength(BOUNDARY_FORCE_STRENGTH) // Attire doucement les nœuds vers le centre vertical
      )
      .alphaDecay(ALPHA_DECAY) // Contrôle la vitesse de stabilisation
      .velocityDecay(VELOCITY_DECAY)
  ); // Friction pour ralentir les nœuds
};
