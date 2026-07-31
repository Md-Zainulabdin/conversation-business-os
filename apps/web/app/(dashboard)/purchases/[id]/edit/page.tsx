"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

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

interface Product {
  id: string;
  name: string;
  purchase_price: number;
}

interface PurchaseData {
  id: string;
  product_id: string;
  supplier_name: string;
  quantity: number;
  purchase_price: number;
  purchase_date: string;
  notes: string | null;
}

export default function EditPurchasePage() {
  const router = useRouter();
  const params = useParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const [productId, setProductId] = useState("");
  const [supplierName, setSupplierName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [purchaseDate, setPurchaseDate] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<Product[]>("/products"),
      api.get<PurchaseData>(`/purchases/${params.id}`),
    ])
      .then(([prods, purchase]) => {
        setProducts(prods);
        setProductId(purchase.product_id);
        setSupplierName(purchase.supplier_name);
        setQuantity(String(purchase.quantity));
        setPurchasePrice(String(purchase.purchase_price));
        setPurchaseDate(purchase.purchase_date.slice(0, 16));
        setNotes(purchase.notes || "");
      })
      .catch(() => router.push("/purchases"))
      .finally(() => setLoading(false));
  }, [params.id, router]);

  const total = useMemo(() => {
    const qty = parseInt(quantity) || 0;
    const price = parseFloat(purchasePrice) || 0;
    return qty * price;
  }, [quantity, purchasePrice]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productId) {
      setError("Please select a product");
      return;
    }
    if (!supplierName.trim()) {
      setError("Supplier name is required");
      return;
    }
    if (!quantity || parseInt(quantity) <= 0) {
      setError("Quantity must be greater than 0");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.put(`/purchases/${params.id}`, {
        product_id: productId,
        supplier_name: supplierName,
        quantity: parseInt(quantity),
        purchase_price: purchasePrice || "0",
        total_amount: total,
        purchase_date: purchaseDate ? new Date(purchaseDate).toISOString() : new Date().toISOString(),
        notes: notes || null,
      });
      router.push("/purchases");
      return;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update purchase");
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
      <div className="max-w-2xl">
        <Link
          href="/purchases"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-3.5" />
          Back to Purchases
        </Link>

        <div className="mt-6 mb-8">
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Edit Purchase</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Update purchase details. Product stock will be adjusted automatically.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label className="text-sm font-medium">Product</Label>
            <Select value={productId} onValueChange={setProductId}>
              <SelectTrigger>
                <SelectValue placeholder="Select product" />
              </SelectTrigger>
              <SelectContent>
                {products.map((p) => (
                  <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="supplier_name" className="text-sm font-medium">Supplier Name</Label>
            <Input
              id="supplier_name"
              value={supplierName}
              onChange={(e) => setSupplierName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="quantity" className="text-sm font-medium">Quantity</Label>
              <Input
                id="quantity"
                type="number"
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="purchase_price" className="text-sm font-medium">Purchase Price / Unit (PKR)</Label>
              <Input
                id="purchase_price"
                type="number"
                step="0.01"
                min="0"
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="purchase_date" className="text-sm font-medium">Purchase Date</Label>
              <Input
                id="purchase_date"
                type="datetime-local"
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label className="text-sm font-medium">Total Amount</Label>
              <div className="flex h-10 items-center rounded-md border border-border bg-card px-3 text-sm font-medium text-foreground">
                Rs {total.toLocaleString()}
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="notes" className="text-sm font-medium">Notes</Label>
            <Textarea
              id="notes"
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
              {saving ? "Saving" : "Save Changes"}
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
