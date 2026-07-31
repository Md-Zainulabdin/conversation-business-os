"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
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
  selling_price: number;
  stock_quantity: number;
}

interface Customer {
  id: string;
  name: string;
}

export default function NewSalePage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  const [customerId, setCustomerId] = useState<string>("");
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unitPrice, setUnitPrice] = useState("");
  const [saleDate, setSaleDate] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<Product[]>("/products"),
      api.get<Customer[]>("/customers"),
    ])
      .then(([prods, custs]) => {
        setProducts(prods);
        setCustomers(custs);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const selectedProduct = useMemo(
    () => products.find((p) => p.id === productId),
    [products, productId]
  );

  const handleProductChange = (id: string) => {
    setProductId(id);
    const product = products.find((p) => p.id === id);
    if (product) {
      setUnitPrice(String(product.selling_price));
    }
  };

  const total = useMemo(() => {
    const qty = parseInt(quantity) || 0;
    const price = parseFloat(unitPrice) || 0;
    return qty * price;
  }, [quantity, unitPrice]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productId) {
      setError("Please select a product");
      return;
    }
    if (!quantity || parseInt(quantity) <= 0) {
      setError("Quantity must be greater than 0");
      return;
    }
    if (selectedProduct && parseInt(quantity) > selectedProduct.stock_quantity) {
      setError(`Insufficient stock. Available: ${selectedProduct.stock_quantity}`);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post("/sales", {
        customer_id: customerId || null,
        product_id: productId,
        quantity: parseInt(quantity),
        unit_price: unitPrice || "0",
        total_amount: total,
        sale_date: saleDate ? new Date(saleDate).toISOString() : new Date().toISOString(),
        notes: notes || null,
      });
      router.push("/sales");
      return;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to record sale");
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
          href="/sales"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-3.5" />
          Back to Sales
        </Link>

        <div className="mt-6 mb-8">
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Record Sale</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Record a customer sale. Product stock will be reduced automatically.
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

          <div className="flex flex-col gap-1.5">
            <Label className="text-sm font-medium">Product</Label>
            <Select value={productId} onValueChange={handleProductChange}>
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
          </div>

          {selectedProduct && (
            <div className="rounded-md border border-border bg-card px-3 py-2 text-xs text-muted-foreground">
              Selling price: <span className="font-medium text-foreground">Rs {Number(selectedProduct.selling_price).toLocaleString()}</span> · In stock: <span className="font-medium text-foreground">{selectedProduct.stock_quantity}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="quantity" className="text-sm font-medium">Quantity</Label>
              <Input
                id="quantity"
                type="number"
                min="1"
                placeholder="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="unit_price" className="text-sm font-medium">Unit Price (PKR)</Label>
              <Input
                id="unit_price"
                type="number"
                step="0.01"
                min="0"
                placeholder="0"
                value={unitPrice}
                onChange={(e) => setUnitPrice(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="sale_date" className="text-sm font-medium">Sale Date</Label>
              <Input
                id="sale_date"
                type="datetime-local"
                value={saleDate}
                onChange={(e) => setSaleDate(e.target.value)}
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
