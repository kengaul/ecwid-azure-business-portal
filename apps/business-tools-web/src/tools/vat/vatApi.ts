import { getJson, postJson } from "../../api/client";

export type CategoryOption = {
  id: number;
  name: string;
  enabled: boolean;
  parent_id?: number | null;
  product_count?: number | null;
  enabled_product_count?: number | null;
};

export type VatProduct = {
  id: number;
  sku: string;
  name: string;
  enabled: boolean;
  current_tax_class_code?: string | null;
  current_tax_rate?: number | null;
  taxable?: boolean | null;
};

export type VatPlan = {
  category: CategoryOption;
  products_to_update: VatProduct[];
  already_zero_rated: VatProduct[];
};

export type CategoriesResponse = {
  ok: boolean;
  categories: CategoryOption[];
};

export type VatPreviewResponse = {
  ok: boolean;
  canApply: boolean;
  plan: VatPlan;
};

export type VatApplyResponse = {
  ok: boolean;
  result: {
    plan: VatPlan;
    updates: Array<{
      product: VatProduct;
      success: boolean;
      error?: string | null;
    }>;
    partial_failure: boolean;
  };
};

export function fetchVatCategories() {
  return getJson<CategoriesResponse>("/api/vat/categories");
}

export function previewVat(categoryId: number) {
  return postJson<VatPreviewResponse>("/api/vat/preview", { categoryId });
}

export function applyVat(categoryId: number, productIds: number[]) {
  return postJson<VatApplyResponse>("/api/vat/apply", { categoryId, productIds });
}
