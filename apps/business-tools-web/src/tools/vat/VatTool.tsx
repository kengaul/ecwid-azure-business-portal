import { AlertTriangle, CheckCircle2, Play, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  CategoryOption,
  VatApplyResponse,
  VatPlan,
  VatProduct,
  VatPreviewResponse,
  applyVat,
  fetchVatCategories,
  previewVat
} from "./vatApi";

export function VatTool() {
  const [categories, setCategories] = useState<CategoryOption[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [preview, setPreview] = useState<VatPreviewResponse | null>(null);
  const [selectedProductIds, setSelectedProductIds] = useState<Set<number>>(new Set());
  const [applyResult, setApplyResult] = useState<VatApplyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"load" | "preview" | "apply" | null>("load");

  useEffect(() => {
    fetchVatCategories()
      .then((response) => setCategories(response.categories))
      .catch((err) => setError(err instanceof Error ? err.message : "Categories failed to load."))
      .finally(() => setBusy(null));
  }, []);

  const selectedCategory = useMemo(
    () => categories.find((category) => category.id === selectedCategoryId) ?? null,
    [categories, selectedCategoryId]
  );
  const categoryOptions = useMemo(() => buildCategoryOptions(categories), [categories]);
  const canPreview = Boolean(selectedCategoryId && !busy);
  const canApply = Boolean(preview?.canApply && selectedCategoryId && selectedProductIds.size > 0 && !busy);

  async function handlePreview() {
    if (!selectedCategoryId) {
      return;
    }

    setBusy("preview");
    setError(null);
    setApplyResult(null);
    try {
      const nextPreview = await previewVat(selectedCategoryId);
      setPreview(nextPreview);
      setSelectedProductIds(new Set(nextPreview.plan.products_to_update.map((product) => product.id)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview failed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleApply() {
    if (!selectedCategoryId) {
      return;
    }

    setBusy("apply");
    setError(null);
    try {
      setApplyResult(await applyVat(selectedCategoryId, Array.from(selectedProductIds)));
      const nextPreview = await previewVat(selectedCategoryId);
      setPreview(nextPreview);
      setSelectedProductIds(new Set(nextPreview.plan.products_to_update.map((product) => product.id)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Apply failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="vat-tool">
      <div className="input-panel">
        <div className="panel-heading">
          <h2>Category</h2>
          <span className="muted">{busy === "load" ? "Loading" : `${categories.length} available`}</span>
        </div>
        <select
          value={selectedCategoryId ?? ""}
          disabled={busy === "load"}
          onChange={(event) => {
            setSelectedCategoryId(event.target.value ? Number(event.target.value) : null);
            setPreview(null);
            setSelectedProductIds(new Set());
            setApplyResult(null);
          }}
        >
          <option value="">Select a category</option>
          {categoryOptions.map((option) => (
            <option key={option.category.id} value={option.category.id}>
              {option.label}
              {option.category.enabled ? "" : " (disabled)"}
            </option>
          ))}
        </select>
        {selectedCategory ? (
          <div className="category-summary">
            <strong>{selectedCategory.name}</strong>
            <span>{selectedCategory.enabled ? "Enabled" : "Disabled"}</span>
          </div>
        ) : null}
        <div className="actions">
          <button type="button" className="primary-action" disabled={!canPreview} onClick={handlePreview}>
            <Search size={18} aria-hidden="true" />
            {busy === "preview" ? "Checking" : "Preview"}
          </button>
          <button type="button" className="danger-action" disabled={!canApply} onClick={handleApply}>
            <Play size={18} aria-hidden="true" />
            {busy === "apply" ? "Updating" : `Confirm ${selectedProductIds.size}`}
          </button>
        </div>
        {error ? <StatusMessage tone="danger" icon={<AlertTriangle size={18} />} text={error} /> : null}
        {applyResult ? (
          <StatusMessage
            tone={applyResult.result.partial_failure ? "danger" : "success"}
            icon={applyResult.result.partial_failure ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
            text={
              applyResult.result.partial_failure
                ? "The update stopped after a failed Ecwid request."
                : "VAT update completed."
            }
          />
        ) : null}
      </div>

      <div className="preview-panel">
        {preview ? (
          <VatPlanDetails
            plan={preview.plan}
            selectedProductIds={selectedProductIds}
            onSelectionChange={setSelectedProductIds}
          />
        ) : (
          <div className="empty-state">Preview a category before updating.</div>
        )}
      </div>
    </div>
  );
}

type CategorySelectOption = {
  category: CategoryOption;
  label: string;
};

function buildCategoryOptions(categories: CategoryOption[]): CategorySelectOption[] {
  const byId = new Map(categories.map((category) => [category.id, category]));
  const childrenByParent = new Map<number | null, CategoryOption[]>();

  for (const category of categories) {
    const parentId = category.parent_id ?? null;
    const parentKey = parentId && byId.has(parentId) ? parentId : null;
    const children = childrenByParent.get(parentKey) ?? [];
    children.push(category);
    childrenByParent.set(parentKey, children);
  }

  for (const children of childrenByParent.values()) {
    children.sort((a, b) => a.name.localeCompare(b.name));
  }

  const options: CategorySelectOption[] = [];
  const visited = new Set<number>();

  function visit(category: CategoryOption, depth: number, parentPath: string) {
    if (visited.has(category.id)) {
      return;
    }
    visited.add(category.id);

    const path = parentPath ? `${parentPath} / ${category.name}` : category.name;
    const prefix = depth > 0 ? `${"  ".repeat(depth)}-- ` : "";
    options.push({ category, label: `${prefix}${path}` });

    for (const child of childrenByParent.get(category.id) ?? []) {
      visit(child, depth + 1, path);
    }
  }

  for (const root of childrenByParent.get(null) ?? []) {
    visit(root, 0, "");
  }

  for (const category of categories) {
    visit(category, 0, "");
  }

  return options;
}

function StatusMessage({ tone, icon, text }: { tone: "success" | "danger"; icon: JSX.Element; text: string }) {
  return (
    <div className={`status-message ${tone}`}>
      {icon}
      <span>{text}</span>
    </div>
  );
}

function VatPlanDetails({
  plan,
  selectedProductIds,
  onSelectionChange
}: {
  plan: VatPlan;
  selectedProductIds: Set<number>;
  onSelectionChange: (selectedProductIds: Set<number>) => void;
}) {
  const metrics = [
    { label: "Selected", value: selectedProductIds.size },
    { label: "Eligible", value: plan.products_to_update.length },
    { label: "Already zero", value: plan.already_zero_rated.length }
  ];

  function selectAll() {
    onSelectionChange(new Set(plan.products_to_update.map((product) => product.id)));
  }

  function selectNone() {
    onSelectionChange(new Set());
  }

  function toggleProduct(productId: number) {
    const next = new Set(selectedProductIds);
    if (next.has(productId)) {
      next.delete(productId);
    } else {
      next.add(productId);
    }
    onSelectionChange(next);
  }

  return (
    <div>
      <div className="metrics compact">
        {metrics.map((item) => (
          <div className="metric" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
      <div className="plan-details">
        <section>
          <div className="section-heading">
            <h3>Will be set to zero rate</h3>
            <div className="inline-actions">
              <button type="button" className="text-button" onClick={selectAll}>
                Select all
              </button>
              <button type="button" className="text-button" onClick={selectNone}>
                Select none
              </button>
            </div>
          </div>
          <SelectableProductList
            products={plan.products_to_update}
            selectedProductIds={selectedProductIds}
            onToggle={toggleProduct}
            empty="No products need updating."
          />
        </section>
        <ProductList title="Already zero-rated" products={plan.already_zero_rated} empty="No products are currently zero-rated." />
      </div>
    </div>
  );
}

function SelectableProductList({
  products,
  selectedProductIds,
  onToggle,
  empty
}: {
  products: VatProduct[];
  selectedProductIds: Set<number>;
  onToggle: (productId: number) => void;
  empty: string;
}) {
  if (products.length === 0) {
    return <p className="muted">{empty}</p>;
  }

  return (
    <div className="product-table">
      {products.map((product) => (
        <label className="product-row vat-row selectable-row" key={`selectable-${product.id}`}>
          <input
            type="checkbox"
            checked={selectedProductIds.has(product.id)}
            onChange={() => onToggle(product.id)}
          />
          <span className="sku">{product.sku || product.id}</span>
          <span>{product.name}</span>
          <span className="priority">{product.current_tax_class_code ?? "none"}</span>
        </label>
      ))}
    </div>
  );
}

function ProductList({ title, products, empty }: { title: string; products: VatProduct[]; empty: string }) {
  return (
    <section>
      <h3>{title}</h3>
      {products.length === 0 ? (
        <p className="muted">{empty}</p>
      ) : (
        <div className="product-table">
          {products.map((product) => (
            <div className="product-row vat-row" key={`${title}-${product.id}`}>
              <span className="sku">{product.sku || product.id}</span>
              <span>{product.name}</span>
              <span className="priority">{product.current_tax_class_code ?? "none"}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
