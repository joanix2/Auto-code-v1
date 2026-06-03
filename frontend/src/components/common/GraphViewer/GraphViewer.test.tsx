import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { GraphViewer } from "./GraphViewer";

vi.mock("d3", () => ({
  select: vi.fn(() => ({
    selectAll: vi.fn(() => ({ remove: vi.fn() })),
    append: vi.fn(() => ({
      attr: vi.fn(() => ({
        attr: vi.fn(() => ({
          attr: vi.fn(() => ({
            attr: vi.fn(() => ({
              attr: vi.fn(() => ({
                lower: vi.fn(),
                style: vi.fn(() => ({
                  style: vi.fn(() => ({
                    lower: vi.fn(),
                  })),
                })),
                on: vi.fn(() => ({
                  on: vi.fn(),
                })),
              })),
            })),
          })),
        })),
        style: vi.fn(),
        on: vi.fn(),
        lower: vi.fn(),
        call: vi.fn(),
      })),
      attr: vi.fn(() => ({
        attr: vi.fn(),
        on: vi.fn(),
      })),
      on: vi.fn(),
      call: vi.fn(),
      style: vi.fn(),
    })),
    attr: vi.fn(),
    on: vi.fn(),
    call: vi.fn(),
    style: vi.fn(() => ({
      style: vi.fn(),
    })),
  })),
  zoom: vi.fn(() => {
    const fn = vi.fn();
    fn.transform = vi.fn();
    fn.scaleBy = vi.fn();
    fn.translateBy = vi.fn();
    return fn;
  }),
  drag: vi.fn(() => vi.fn()),
  forceSimulation: vi.fn(() => ({
    force: vi.fn(() => ({
      force: vi.fn(() => ({
        force: vi.fn(() => ({
          force: vi.fn(() => ({
            nodes: vi.fn(() => ({
              links: vi.fn(() => ({
                on: vi.fn(() => ({
                  alpha: vi.fn(() => ({
                    restart: vi.fn(),
                  })),
                })),
              })),
            })),
          })),
        })),
      })),
    })),
    nodes: vi.fn(() => ({
      links: vi.fn(() => ({
        on: vi.fn(() => ({
          alpha: vi.fn(() => ({
            restart: vi.fn(),
          })),
        })),
      })),
    })),
    on: vi.fn(() => ({
      alpha: vi.fn(() => ({
        restart: vi.fn(),
      })),
    })),
    stop: vi.fn(),
    alpha: vi.fn(),
    restart: vi.fn(),
  })),
  forceCenter: vi.fn(),
  forceManyBody: vi.fn(),
  forceLink: vi.fn(() => ({
    id: vi.fn(),
    distance: vi.fn(),
  })),
  forceCollide: vi.fn(),
  zoomIdentity: { k: 1, x: 0, y: 0 },
  selectAll: vi.fn(() => ({
    remove: vi.fn(),
    attr: vi.fn(),
    data: vi.fn(() => ({
      join: vi.fn(() => ({
        attr: vi.fn(() => ({
          attr: vi.fn(() => ({
            attr: vi.fn(() => ({
              attr: vi.fn(() => ({
                attr: vi.fn(() => ({
                  attr: vi.fn(() => ({
                    attr: vi.fn(),
                    on: vi.fn(),
                    call: vi.fn(),
                  })),
                })),
              })),
            })),
          })),
        })),
      })),
      enter: vi.fn(() => ({
        append: vi.fn(() => ({
          attr: vi.fn(() => ({
            attr: vi.fn(() => ({
              attr: vi.fn(() => ({
                attr: vi.fn(() => ({
                  attr: vi.fn(() => ({
                    attr: vi.fn(() => ({
                      attr: vi.fn(() => ({
                        attr: vi.fn(),
                        on: vi.fn(),
                        call: vi.fn(),
                      })),
                    })),
                  })),
                })),
              })),
            })),
          })),
        })),
      })),
      exit: vi.fn(() => ({
        remove: vi.fn(),
      })),
    })),
  })),
}));

describe("GraphViewer", () => {
  const defaultProps = {
    width: 800,
    height: 600,
    data: { nodes: [], edges: [] },
  };

  it("renders without crashing", () => {
    const { container } = render(<GraphViewer {...defaultProps} />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  it("renders empty state when no nodes", () => {
    render(<GraphViewer {...defaultProps} />);
    expect(screen.getByText("No data to display")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<GraphViewer {...defaultProps} className="custom-class" />);
    expect(container.firstChild).toHaveClass("custom-class");
  });
});
