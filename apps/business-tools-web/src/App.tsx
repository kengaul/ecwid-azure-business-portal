import { Construction, Home, Percent, Star } from "lucide-react";
import { useMemo, useState } from "react";
import { AppShell, ToolDefinition } from "./layout/AppShell";
import { FeaturedTool } from "./tools/featured/FeaturedTool";
import { FrontpageTool } from "./tools/frontpage/FrontpageTool";
import { ComingSoon } from "./tools/placeholder/ComingSoon";
import { VatTool } from "./tools/vat/VatTool";

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
        label: "Zero-rate VAT",
        route: "/catalog",
        icon: Percent,
        enabled: true,
        component: <VatTool />
      },
      {
        id: "featured",
        label: "Featured Products",
        route: "/featured",
        icon: Star,
        enabled: true,
        component: <FeaturedTool />
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
