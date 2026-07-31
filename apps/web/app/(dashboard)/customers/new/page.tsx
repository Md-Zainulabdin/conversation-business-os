"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";

export default function NewCustomerPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    if (!phone.trim()) {
      setError("Phone number is required");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post("/customers", { name, phone, address: address || null });
      router.push("/customers");
      return;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create customer");
    }
    setSaving(false);
  };

  return (
    <div className="mx-auto max-w-7xl">
      <div className="max-w-lg">
        <Link
          href="/customers"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-3.5" />
          Back to Customers
        </Link>

        <div className="mt-6 mb-8">
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Add Customer</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Add a new customer to your directory.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name" className="text-sm font-medium">Name</Label>
            <Input
              id="name"
              placeholder="e.g. Ali Hassan"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="phone" className="text-sm font-medium">Phone Number</Label>
            <Input
              id="phone"
              placeholder="e.g. +92 300 1234567"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="address" className="text-sm font-medium">Address</Label>
            <Textarea
              id="address"
              placeholder="Optional delivery address..."
              value={address}
              onChange={(e) => setAddress(e.target.value)}
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
              {saving ? "Creating" : "Create Customer"}
            </Button>
            <Link href="/customers">
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
