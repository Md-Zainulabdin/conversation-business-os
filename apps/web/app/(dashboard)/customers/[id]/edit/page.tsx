"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";

interface CustomerData {
  id: string;
  name: string;
  phone: string;
  address: string | null;
}

export default function EditCustomerPage() {
  const router = useRouter();
  const params = useParams();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<CustomerData>(`/customers/${params.id}`)
      .then((c) => {
        setName(c.name);
        setPhone(c.phone);
        setAddress(c.address || "");
      })
      .catch(() => router.push("/customers"))
      .finally(() => setLoading(false));
  }, [params.id, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !phone.trim()) {
      setError("Name and phone are required");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.put(`/customers/${params.id}`, {
        name,
        phone,
        address: address || null,
      });
      router.push("/customers");
      return;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update customer");
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
      <div className="max-w-lg">
        <Link
          href="/customers"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-3.5" />
          Back to Customers
        </Link>

        <div className="mt-6 mb-8">
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Edit Customer</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Update customer contact and delivery details.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name" className="text-sm font-medium">Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="phone" className="text-sm font-medium">Phone Number</Label>
            <Input
              id="phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="address" className="text-sm font-medium">Address</Label>
            <Textarea
              id="address"
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
              {saving ? "Saving" : "Save Changes"}
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
