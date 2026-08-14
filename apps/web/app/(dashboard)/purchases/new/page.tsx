"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import type { Product } from "@/types";

interface LineItem {
  key: number;
  productId: string;
  quantity: string;
  unitPrice: string;
}

let lineKey = 0;

export default function NewPurchasePage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const [supplierName, setSupplierName] = useState("");
  const [items, setItems] = useState<LineItem[]>([
    { key: ++lineKey, productId: "", quantity: "", unitPrice: "" },
  ]);
  const [purchaseDate, setPurchaseDate] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Product[]>("/products")
      .then(setProducts)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const productById = (id: string) => products.find((p) => p.id === id);

  const updateItem = (key: number, patch: Partial<LineItem>) => {
    setItems((prev) =>
      prev.map((item) => (item.key === key ? { ...item, ...patch } : item))
    );
  };

  const handleProductChange = (key: number, id: string) => {
    const product = productById(id);
    updateItem(key, {
      productId: id,
      unitPrice: product ? String(product.purchase_price) : "",
    });
  };

  const addItem = () => {
    setItems((prev) => [
      ...prev,
      { key: ++lineKey, productId: "", quantity: "", unitPrice: "" },
    ]);
  };

  const removeItem = (key: number) => {
    setItems((prev) =>
      prev.length > 1 ? prev.filter((item) => item.key !== key) : prev
    );
  };

  const grandTotal = items.reduce((sum, item) => {
    const qty = parseInt(item.quantity) || 0;
    const price = parseFloat(item.unitPrice) || 0;
    return sum + qty * price;
  }, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supplierName.trim()) {
      setError("Supplier name is required");
      return;
    }
    const validItems = items.filter((item) => item.productId && item.quantity);
    if (validItems.length === 0) {
      setError("Add at least one product with a quantity");
      return;
    }
    for (const item of validItems) {
      const qty = parseInt(item.quantity);
      if (!qty || qty <= 0) {
        setError("Quantity must be greater than 0");
        return;
      }
    }

    setSaving(true);
    setError(null);
    try {
      await api.post("/purchases", {
        supplier_name: supplierName,
        items: validItems.map((item) => {
          const qty = parseInt(item.quantity);
          const unitPrice = parseFloat(item.unitPrice) || 0;
          return {
            product_id: item.productId,
            quantity: qty,
            purchase_price: unitPrice,
            total_amount: qty * unitPrice,
          };
        }),
        purchase_date: purchaseDate
          ? new Date(purchaseDate).toISOString()
          : new Date().toISOString(),
        notes: notes || null,
      });
      router.push("/purchases");
      return;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record purchase");
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl">
        <Spinner className="size-5" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl">
      <div className="max-w-3xl">
        <Link
          href="/purchases"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-3.5" />
          Back to Purchases
        </Link>

        <div className="mt-6 mb-8">
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Record Purchase</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Record an inventory restock with one or more products. Stock is increased automatically.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="supplier_name" className="text-sm font-medium">Supplier Name</Label>
            <Input
              id="supplier_name"
              placeholder="e.g. Punjab Agro Mills"
              value={supplierName}
              onChange={(e) => setSupplierName(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Products</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addItem}
              >
                <Plus className="size-3.5" />
                Add Product
              </Button>
            </div>

            {items.map((item, index) => {
              const qty = parseInt(item.quantity) || 0;
              const price = parseFloat(item.unitPrice) || 0;
              return (
                <div
                  key={item.key}
                  className="rounded-lg border border-border bg-card p-3"
                >
                  <div className="grid grid-cols-[1fr] gap-2 sm:grid-cols-[2fr_1fr_1fr_1fr_auto]">
                    <Select
                      value={item.productId}
                      onValueChange={(id) => handleProductChange(item.key, id)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select product" />
                      </SelectTrigger>
                      <SelectContent>
                        {products.map((p) => (
                          <SelectItem key={p.id} value={p.id}>
                            {p.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Input
                      type="number"
                      min="1"
                      placeholder="Qty"
                      value={item.quantity}
                      onChange={(e) =>
                        updateItem(item.key, { quantity: e.target.value })
                      }
                    />
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="Unit price"
                      value={item.unitPrice}
                      onChange={(e) =>
                        updateItem(item.key, { unitPrice: e.target.value })
                      }
                    />
                    <div className="flex h-10 items-center rounded-md border border-border bg-background px-3 text-sm font-medium tabular-nums text-foreground">
                      Rs {(qty * price).toLocaleString()}
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() => removeItem(item.key)}
                      aria-label={`Remove product ${index + 1}`}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
              );
            })}

            <div className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2 text-sm">
              <span className="font-medium text-muted-foreground">Grand Total</span>
              <span className="font-semibold tabular-nums text-foreground">
                Rs {grandTotal.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="purchase_date" className="text-sm font-medium">Purchase Date</Label>
              <Input
                id="purchase_date"
                type="datetime-local"
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="notes" className="text-sm font-medium">Notes</Label>
            <Textarea
              id="notes"
              placeholder="Optional remarks..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
          </div>

          {error && (
            <div className="rounded-md border border-destructive/20 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button type="submit" disabled={saving}>
              {saving && <Spinner data-icon="inline-start" />}
              {saving ? "Recording" : "Record Purchase"}
            </Button>
            <Link href="/purchases">
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}