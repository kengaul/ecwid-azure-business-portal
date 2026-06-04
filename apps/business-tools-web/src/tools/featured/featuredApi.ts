import { getJson, postJson } from "../../api/client";

export type SupplierOption = {
  name: string;
  product_count: number;
};

export type FeaturedCategory = {
  id: number;
  name: string;
};

export type FeaturedProduct = {
  id: number;
  sku: string;
  name: string;
  enabled: boolean;
  supplier?: string | null;
  category_ids: number[];
  default_category_id?: number | null;
  is_currently_featured: boolean;
};

export type FeaturedPlan = {
  supplier: string;
  featured_category: FeaturedCategory;
  selected_products: FeaturedProduct[];
  selectable_products: FeaturedProduct[];
  products_to_add: FeaturedProduct[];
  products_to_keep: FeaturedProduct[];
  products_to_remove: FeaturedProduct[];
};

export type SuppliersResponse = {
  ok: boolean;
  supplierAttributeName: string;
  suppliers: SupplierOption[];
};

export type FeaturedPreviewResponse = {
  ok: boolean;
  canApply: boolean;
  plan: FeaturedPlan;
};

export type FeaturedApplyResponse = {
  ok: boolean;
  result: {
    plan: FeaturedPlan;
    updates: Array<{
      product: FeaturedProduct;
      success: boolean;
      action: "add" | "remove" | "keep";
      error?: string | null;
    }>;
    partial_failure: boolean;
  };
};

export function fetchFeaturedSuppliers() {
  return getJson<SuppliersResponse>("/api/featured/suppliers");
}

export function previewFeatured(supplier: string) {
  return postJson<FeaturedPreviewResponse>("/api/featured/preview", { supplier });
}

export function applyFeatured(supplier: string, productIds: number[]) {
  return postJson<FeaturedApplyResponse>("/api/featured/apply", { supplier, productIds });
}
