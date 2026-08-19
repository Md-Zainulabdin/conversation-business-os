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
import type { Page, Product } from "@/types";

interface Customer {
  id: string;
  name: string;
}

interface LineItem {
  key: number;
  productId: string;
  quantity: string;
  unitPrice: string;
}

let lineKey = 0;

function useLineItems(initial: LineItem[]) {
  return useState<LineItem[]>(initial);
}

export default function NewSalePage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  const [customerId, setCustomerId] = useState("");
  const [items, setItems] = useLineItems([
    { key: ++lineKey, productId: "", quantity: "", unitPrice: "" },
  ]);
  const [saleDate, setSaleDate] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<Page<Product>>("/products?limit=500"),
      api.get<Page<Customer>>("/customers?limit=500"),
    ])
      .then(([prods, custs]) => {
        setProducts(prods.items);
        setCustomers(custs.items);
      })
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
      unitPrice: product ? String(product.selling_price) : "",
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
      const product = productById(item.productId);
      if (product && qty > product.stock_quantity) {
        setError(
          `Insufficient stock for ${product.name}. Available: ${product.stock_quantity}`
        );
        return;
      }
    }

    setSaving(true);
    setError(null);
    try {
      await api.post("/sales", {
        customer_id: customerId || null,
        items: validItems.map((item) => {
          const qty = parseInt(item.quantity);
          const unitPrice = parseFloat(item.unitPrice) || 0;
          return {
            product_id: item.productId,
            quantity: qty,
            unit_price: unitPrice,
            total_amount: qty * unitPrice,
          };
        }),
        sale_date: saleDate
          ? new Date(saleDate).toISOString()
          : new Date().toISOString(),
        notes: notes || null,
      });
      router.push("/sales");
      return;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record sale");
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
          href="/sales"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-3.5" />
          Back to Sales
        </Link>

        <div className="mt-6 mb-8">
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Record Sale</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Record a customer sale with one or more products. Stock is reduced automatically.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label className="text-sm font-medium">Customer</Label>
            <Select value={customerId} onValueChange={setCustomerId}>
              <SelectTrigger>
                <SelectValue placeholder="Walk-in customer" />
              </SelectTrigger>
              <SelectContent>
                {customers.map((c) => (
                  <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
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
              const product = productById(item.productId);
              const qty = parseInt(item.quantity) || 0;
              const price = parseFloat(item.unitPrice) || 0;
              const stockShort = product && qty > product.stock_quantity;
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
                            {p.name} (Stock: {p.stock_quantity})
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
                  {product && stockShort && (
                    <p className="mt-1.5 text-xs text-destructive">
                      Only {product.stock_quantity} {product.unit} in stock.
                      You entered {qty}.
                    </p>
                  )}
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
              <Label htmlFor="sale_date" className="text-sm font-medium">Sale Date</Label>
              <Input
                id="sale_date"
                type="datetime-local"
                value={saleDate}
                onChange={(e) => setSaleDate(e.target.value)}
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
              {saving ? "Recording" : "Record Sale"}
            </Button>
            <Link href="/sales">
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