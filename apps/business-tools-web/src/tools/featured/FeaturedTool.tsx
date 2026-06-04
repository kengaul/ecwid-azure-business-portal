import { AlertTriangle, CheckCircle2, Play, Search, Star } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  FeaturedApplyResponse,
  FeaturedPlan,
  FeaturedPreviewResponse,
  FeaturedProduct,
  SupplierOption,
  applyFeatured,
  fetchFeaturedSuppliers,
  previewFeatured
} from "./featuredApi";

export function FeaturedTool() {
  const [suppliers, setSuppliers] = useState<SupplierOption[]>([]);
  const [supplierAttributeName, setSupplierAttributeName] = useState("Supplier");
  const [selectedSupplier, setSelectedSupplier] = useState("");
  const [preview, setPreview] = useState<FeaturedPreviewResponse | null>(null);
  const [selectedProductIds, setSelectedProductIds] = useState<Set<number>>(new Set());
  const [applyResult, setApplyResult] = useState<FeaturedApplyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"load" | "preview" | "apply" | null>("load");

  useEffect(() => {
    fetchFeaturedSuppliers()
      .then((response) => {
        setSupplierAttributeName(response.supplierAttributeName);
        setSuppliers(response.suppliers);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Suppliers failed to load."))
      .finally(() => setBusy(null));
  }, []);

  const selectedSupplierOption = useMemo(
    () => suppliers.find((supplier) => supplier.name === selectedSupplier) ?? null,
    [selectedSupplier, suppliers]
  );
  const canPreview = Boolean(selectedSupplier && !busy);
  const canApply = Boolean(preview?.canApply && selectedSupplier && !busy);

  async function handlePreview() {
    if (!selectedSupplier) {
      return;
    }

    setBusy("preview");
    setError(null);
    setApplyResult(null);
    try {
      const nextPreview = await previewFeatured(selectedSupplier);
      setPreview(nextPreview);
      setSelectedProductIds(new Set(nextPreview.plan.selectable_products.map((product) => product.id)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview failed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleApply() {
    if (!selectedSupplier) {
      return;
    }

    setBusy("apply");
    setError(null);
    try {
      setApplyResult(await applyFeatured(selectedSupplier, Array.from(selectedProductIds)));
      const nextPreview = await previewFeatured(selectedSupplier);
      setPreview(nextPreview);
      setSelectedProductIds(new Set(nextPreview.plan.selectable_products.map((product) => product.id)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Apply failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="featured-tool">
      <div className="input-panel">
        <div className="panel-heading">
          <h2>{supplierAttributeName}</h2>
          <span className="muted">{busy === "load" ? "Loading" : `${suppliers.length} available`}</span>
        </div>
        <select
          value={selectedSupplier}
          disabled={busy === "load"}
          onChange={(event) => {
            setSelectedSupplier(event.target.value);
            setPreview(null);
            setSelectedProductIds(new Set());
            setApplyResult(null);
          }}
        >
          <option value="">Select a supplier</option>
          {suppliers.map((supplier) => (
            <option key={supplier.name} value={supplier.name}>
              {supplier.name} ({supplier.product_count})
            </option>
          ))}
        </select>
        {selectedSupplierOption ? (
          <div className="category-summary">
            <strong>{selectedSupplierOption.name}</strong>
            <span>{selectedSupplierOption.product_count} enabled products</span>
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
        {preview && selectedProductIds.size === 0 ? (
          <StatusMessage
            tone="danger"
            icon={<AlertTriangle size={18} />}
            text={`Confirming with no selected products will remove every product from ${preview.plan.featured_category.name}.`}
          />
        ) : null}
        {applyResult ? (
          <StatusMessage
            tone={applyResult.result.partial_failure ? "danger" : "success"}
            icon={applyResult.result.partial_failure ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
            text={
              applyResult.result.partial_failure
                ? "The update stopped after a failed Ecwid request."
                : "Featured Products update completed."
            }
          />
        ) : null}
      </div>

      <div className="preview-panel">
        {preview ? (
          <FeaturedPlanDetails
            plan={preview.plan}
            selectedProductIds={selectedProductIds}
            onSelectionChange={setSelectedProductIds}
          />
        ) : (
          <div className="empty-state">
            <Star size={28} aria-hidden="true" />
            <p>Preview a supplier before updating Featured Products.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function StatusMessage({ tone, icon, text }: { tone: "success" | "danger"; icon: JSX.Element; text: string }) {
  return (
    <div className={`status-message ${tone}`}>
      {icon}
      <span>{text}</span>
    </div>
  );
}

function FeaturedPlanDetails({
  plan,
  selectedProductIds,
  onSelectionChange
}: {
  plan: FeaturedPlan;
  selectedProductIds: Set<number>;
  onSelectionChange: (selectedProductIds: Set<number>) => void;
}) {
  const selectedProducts = plan.selectable_products.filter((product) => selectedProductIds.has(product.id));
  const selectedIds = new Set(selectedProducts.map((product) => product.id));
  const productsToAdd = selectedProducts.filter((product) => !product.is_currently_featured);
  const productsToKeep = selectedProducts.filter((product) => product.is_currently_featured);
  const productsToRemove = plan.products_to_remove.filter((product) => !selectedIds.has(product.id));
  const metrics = [
    { label: "Selected", value: selectedProductIds.size },
    { label: "Will add", value: productsToAdd.length },
    { label: "Will keep", value: productsToKeep.length },
    { label: "Will remove", value: productsToRemove.length }
  ];

  function selectAll() {
    onSelectionChange(new Set(plan.selectable_products.map((product) => product.id)));
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
      <div className="metrics">
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
            <h3>{plan.supplier} products</h3>
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
            products={plan.selectable_products}
            selectedProductIds={selectedProductIds}
            onToggle={toggleProduct}
            empty="No products were found for this supplier."
          />
        </section>
        <ProductList
          title="Will be removed from Featured Products"
          products={productsToRemove}
          empty="No current featured products will be removed."
        />
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
  products: FeaturedProduct[];
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
        <label className="product-row featured-row selectable-row" key={`selectable-${product.id}`}>
          <input
            type="checkbox"
            checked={selectedProductIds.has(product.id)}
            onChange={() => onToggle(product.id)}
          />
          <span className="sku">{product.sku || product.id}</span>
          <span>{product.name}</span>
          <span className="priority">{product.is_currently_featured ? "Featured" : "Add"}</span>
        </label>
      ))}
    </div>
  );
}

function ProductList({ title, products, empty }: { title: string; products: FeaturedProduct[]; empty: string }) {
  return (
    <section>
      <h3>{title}</h3>
      {products.length === 0 ? (
        <p className="muted">{empty}</p>
      ) : (
        <div className="product-table">
          {products.map((product) => (
            <div className="product-row featured-row" key={`${title}-${product.id}`}>
              <span className="sku">{product.sku || product.id}</span>
              <span>{product.name}</span>
              <span className="priority">Remove</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
