import { NodeType } from "@/components/common/GraphViewer";

export class ArchitectureComponentNodeType extends NodeType {
  readonly id = "component";
  readonly label = "Composant";
  readonly labelPlural = "Composants";
  readonly gender = "m" as const;
  readonly article = "le";
}

export class ArchitectureServiceNodeType extends NodeType {
  readonly id = "service";
  readonly label = "Service";
  readonly labelPlural = "Services";
  readonly gender = "m" as const;
  readonly article = "le";
}

export class ArchitectureInterfaceNodeType extends NodeType {
  readonly id = "interface";
  readonly label = "Interface";
  readonly labelPlural = "Interfaces";
  readonly gender = "f" as const;
  readonly article = "l'";
}

export const ARCH_COMPONENT = new ArchitectureComponentNodeType();
export const ARCH_SERVICE = new ArchitectureServiceNodeType();
export const ARCH_INTERFACE = new ArchitectureInterfaceNodeType();

export const ARCH_NODE_TYPES: Record<string, NodeType> = {
  component: ARCH_COMPONENT,
  service: ARCH_SERVICE,
  interface: ARCH_INTERFACE,
};
