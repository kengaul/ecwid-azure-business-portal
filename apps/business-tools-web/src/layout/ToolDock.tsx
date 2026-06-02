import { ToolDefinition } from "./AppShell";

type ToolDockProps = {
  tools: ToolDefinition[];
  activeToolId: string;
  onSelectTool: (toolId: string) => void;
};

export function ToolDock({ tools, activeToolId, onSelectTool }: ToolDockProps) {
  return (
    <aside className="tool-dock" aria-label="Business tools">
      <div className="dock-brand">BT</div>
      <nav>
        {tools.map((tool) => {
          const Icon = tool.icon;
          return (
            <button
              key={tool.id}
              type="button"
              className={tool.id === activeToolId ? "dock-button active" : "dock-button"}
              disabled={!tool.enabled}
              title={tool.enabled ? tool.label : `${tool.label} is not available yet`}
              aria-label={tool.label}
              onClick={() => onSelectTool(tool.id)}
            >
              <Icon size={20} aria-hidden="true" />
              <span>{tool.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
