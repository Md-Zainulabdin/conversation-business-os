"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import type { Page } from "@/types";

interface Category {
  id: string;
  name: string;
}

const units = ["Piece", "Pack", "KG", "Litre", "Carton", "Box", "Bag", "Bottle"];

export default function NewProductPage() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [category, setCategory] = useState("");
  const [unit, setUnit] = useState("Piece");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [sellingPrice, setSellingPrice] = useState("");
  const [stockQuantity, setStockQuantity] = useState("");
  const [minimumStock, setMinimumStock] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Page<Category>>("/categories?limit=500")
      .then((data) => setCategories(data.items))
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !sku.trim()) {
      setError("Name and SKU are required");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post("/products", {
        name,
        sku,
        category: category || "Uncategorized",
        unit,
        purchase_price: purchasePrice || "0",
        selling_price: sellingPrice || "0",
        stock_quantity: parseInt(stockQuantity) || 0,
        minimum_stock: parseInt(minimumStock) || 0,
      });
      router.push("/products");
      return;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create product");
    }
    setSaving(false);
  };

  return (
    <div className="mx-auto max-w-7xl">
      <div className="max-w-2xl">
        <Link
          href="/products"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-3.5" />
          Back to Products
        </Link>

        <div className="mt-6 mb-8">
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Add Product</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Add a new product to your inventory.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name" className="text-sm font-medium">Name</Label>
            <Input
              id="name"
              placeholder="e.g. Coca Cola 500ml"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="sku" className="text-sm font-medium">SKU</Label>
              <Input
                id="sku"
                placeholder="e.g. COKE-500"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label className="text-sm font-medium">Category</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="Uncategorized" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={c.name}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label className="text-sm font-medium">Unit</Label>
              <Select value={unit} onValueChange={setUnit}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {units.map((u) => (
                    <SelectItem key={u} value={u}>{u}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="purchase_price" className="text-sm font-medium">Purchase Price (PKR)</Label>
              <Input
                id="purchase_price"
                type="number"
                step="0.01"
                min="0"
                placeholder="0"
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="selling_price" className="text-sm font-medium">Selling Price (PKR)</Label>
              <Input
                id="selling_price"
                type="number"
                step="0.01"
                min="0"
                placeholder="0"
                value={sellingPrice}
                onChange={(e) => setSellingPrice(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="stock_quantity" className="text-sm font-medium">Stock Quantity</Label>
              <Input
                id="stock_quantity"
                type="number"
                min="0"
                placeholder="0"
                value={stockQuantity}
                onChange={(e) => setStockQuantity(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="minimum_stock" className="text-sm font-medium">Minimum Stock</Label>
              <Input
                id="minimum_stock"
                type="number"
                min="0"
                placeholder="0"
                value={minimumStock}
                onChange={(e) => setMinimumStock(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md border border-destructive/20 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button type="submit" disabled={saving}>
              {saving && <Spinner data-icon="inline-start" />}
              {saving ? "Creating" : "Create Product"}
            </Button>
            <Link href="/products">
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
