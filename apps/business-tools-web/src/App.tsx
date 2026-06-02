import { Boxes, Construction, Home } from "lucide-react";
import { useMemo, useState } from "react";
import { AppShell, ToolDefinition } from "./layout/AppShell";
import { FrontpageTool } from "./tools/frontpage/FrontpageTool";
import { ComingSoon } from "./tools/placeholder/ComingSoon";

export function App() {
  const tools = useMemo<ToolDefinition[]>(
    () => [
      {
        id: "frontpage",
        label: "Frontpage SKUs",
        route: "/frontpage",
        icon: Home,
        enabled: true,
        component: <FrontpageTool />
      },
      {
        id: "catalog",
        label: "Catalog Tasks",
        route: "/catalog",
        icon: Boxes,
        enabled: false,
        component: <ComingSoon title="Catalog Tasks" />
      },
      {
        id: "operations",
        label: "Operations",
        route: "/operations",
        icon: Construction,
        enabled: false,
        component: <ComingSoon title="Operations" />
      }
    ],
    []
  );
  const [activeToolId, setActiveToolId] = useState(tools[0].id);

  return (
    <AppShell
      tools={tools}
      activeToolId={activeToolId}
      onSelectTool={setActiveToolId}
      environment={import.meta.env.VITE_APP_ENVIRONMENT ?? "Production"}
    />
  );
}
