import { AlertTriangle, CheckCircle2, Play, Search } from "lucide-react";
import { useMemo, useState } from "react";
import {
  ApplyResponse,
  FrontpageProduct,
  FrontpagePlan,
  PreviewResponse,
  applyFrontpage,
  previewFrontpage
} from "./frontpageApi";

const exampleText = "5039041122803\n5039041122810";

export function FrontpageTool() {
  const [skuText, setSkuText] = useState("");
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [applyResult, setApplyResult] = useState<ApplyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"preview" | "apply" | null>(null);

  const hasText = skuText.trim().length > 0;
  const canApply = Boolean(preview?.canApply && !busy);

  const summary = useMemo(() => {
    if (!preview) {
      return null;
    }
    return [
      { label: "Valid SKUs", value: preview.plan.valid_skus.length },
      { label: "Warnings", value: preview.plan.warnings.length },
      { label: "Remove", value: preview.plan.removals.length },
      { label: "Set order", value: preview.plan.additions.length + preview.plan.unchanged.length }
    ];
  }, [preview]);

  async function handlePreview() {
    setBusy("preview");
    setError(null);
    setApplyResult(null);
    try {
      setPreview(await previewFrontpage(skuText));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview failed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleApply() {
    setBusy("apply");
    setError(null);
    try {
      setApplyResult(await applyFrontpage(skuText));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Apply failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="frontpage-tool">
      <div className="input-panel">
        <div className="panel-heading">
          <h2>SKU List</h2>
          <button type="button" className="text-button" onClick={() => setSkuText(exampleText)}>
            Use example
          </button>
        </div>
        <textarea
          value={skuText}
          onChange={(event) => {
            setSkuText(event.target.value);
            setPreview(null);
            setApplyResult(null);
          }}
          placeholder="Paste SKUs here"
          spellCheck={false}
        />
        <div className="actions">
          <button type="button" className="primary-action" disabled={!hasText || Boolean(busy)} onClick={handlePreview}>
            <Search size={18} aria-hidden="true" />
            {busy === "preview" ? "Checking" : "Preview"}
          </button>
          <button type="button" className="danger-action" disabled={!canApply} onClick={handleApply}>
            <Play size={18} aria-hidden="true" />
            {busy === "apply" ? "Updating" : "Confirm update"}
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
                : "Frontpage update completed."
            }
          />
        ) : null}
      </div>

      <div className="preview-panel">
        {summary ? (
          <div className="metrics">
            {summary.map((item) => (
              <div className="metric" key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        ) : null}
        {preview ? <PlanDetails plan={preview.plan} /> : <div className="empty-state">Preview changes before updating.</div>}
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

function PlanDetails({ plan }: { plan: FrontpagePlan }) {
  return (
    <div className="plan-details">
      <ProductList title="Final order" products={[...plan.additions, ...plan.unchanged]} empty="No valid SKUs found." />
      <ProductList title="Removed" products={plan.removals} empty="No current frontpage products will be removed." />
      {plan.warnings.length > 0 ? (
        <section>
          <h3>Warnings</h3>
          <ul className="warning-list">
            {plan.warnings.map((warning, index) => (
              <li key={`${warning.code}-${warning.sku}-${index}`}>{warning.message}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function ProductList({ title, products, empty }: { title: string; products: FrontpageProduct[]; empty: string }) {
  return (
    <section>
      <h3>{title}</h3>
      {products.length === 0 ? (
        <p className="muted">{empty}</p>
      ) : (
        <div className="product-table">
          {products.map((product) => (
            <div className="product-row" key={`${title}-${product.id}`}>
              <span className="sku">{product.sku}</span>
              <span>{product.name}</span>
              <span className="priority">{product.target_priority ?? product.current_priority ?? "-"}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
