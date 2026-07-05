import { LucideIcon } from "lucide-react";
import { ReactNode, useEffect, useMemo, useState } from "react";
import { getCurrentUser } from "../api/client";
import { ToolDock } from "./ToolDock";

export type ToolDefinition = {
  id: string;
  label: string;
  route: string;
  icon: LucideIcon;
  enabled: boolean;
  component: ReactNode;
};

type AppShellProps = {
  tools: ToolDefinition[];
  activeToolId: string;
  environment: string;
  onSelectTool: (toolId: string) => void;
};

export function AppShell({ tools, activeToolId, environment, onSelectTool }: AppShellProps) {
  const [userName, setUserName] = useState<string>("Local user");
  const [canSignOut, setCanSignOut] = useState(false);
  const activeTool = useMemo(
    () => tools.find((tool) => tool.id === activeToolId) ?? tools[0],
    [activeToolId, tools]
  );

  useEffect(() => {
    getCurrentUser()
      .then((user) => {
        setUserName(user.clientPrincipal?.userDetails ?? "Local user");
        setCanSignOut(Boolean(user.clientPrincipal));
      })
      .catch(() => {
        setUserName("Local user");
        setCanSignOut(false);
      });
  }, []);

  return (
    <div className="app-shell">
      <ToolDock tools={tools} activeToolId={activeTool.id} onSelectTool={onSelectTool} />
      <main className="workspace">
        <header className="top-bar">
          <div>
            <p className="eyebrow">{environment}</p>
            <h1>{activeTool.label}</h1>
          </div>
          <div className="session">
            <span>{userName}</span>
            {canSignOut ? <a href="/.auth/logout?post_logout_redirect_uri=/">Sign out</a> : null}
          </div>
        </header>
        <section className="tool-surface">{activeTool.component}</section>
      </main>
    </div>
  );
}
