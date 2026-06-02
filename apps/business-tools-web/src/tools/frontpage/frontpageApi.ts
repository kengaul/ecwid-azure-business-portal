import { postJson } from "../../api/client";

export type FrontpageProduct = {
  id: number;
  sku: string;
  name: string;
  current_priority?: number | null;
  target_priority?: number | null;
};

export type SkuWarning = {
  code: string;
  sku: string;
  message: string;
};

export type FrontpagePlan = {
  valid_skus: string[];
  warnings: SkuWarning[];
  removals: FrontpageProduct[];
  additions: FrontpageProduct[];
  unchanged: FrontpageProduct[];
};

export type PreviewResponse = {
  ok: boolean;
  canApply: boolean;
  plan: FrontpagePlan;
};

export type ApplyResponse = {
  ok: boolean;
  result: {
    plan: FrontpagePlan;
    updates: Array<{
      product: FrontpageProduct;
      success: boolean;
      action: string;
      error?: string | null;
    }>;
    partial_failure: boolean;
  };
};

export function previewFrontpage(rawSkus: string) {
  return postJson<PreviewResponse>("/api/frontpage/preview", { skus: rawSkus });
}

export function applyFrontpage(rawSkus: string) {
  return postJson<ApplyResponse>("/api/frontpage/apply", { skus: rawSkus });
}
