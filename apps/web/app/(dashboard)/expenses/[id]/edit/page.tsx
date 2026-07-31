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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";

const expenseCategories = ["Electricity", "Internet", "Transport", "Salary", "Miscellaneous"];

interface ExpenseData {
  id: string;
  title: string;
  category: string;
  amount: number;
  expense_date: string;
  notes: string | null;
}

export default function EditExpensePage() {
  const router = useRouter();
  const params = useParams();
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [amount, setAmount] = useState("");
  const [expenseDate, setExpenseDate] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ExpenseData>(`/expenses/${params.id}`)
      .then((e) => {
        setTitle(e.title);
        setCategory(e.category);
        setAmount(String(e.amount));
        setExpenseDate(e.expense_date.slice(0, 16));
        setNotes(e.notes || "");
      })
      .catch(() => router.push("/expenses"))
      .finally(() => setLoading(false));
  }, [params.id, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !category || !amount || parseFloat(amount) <= 0) {
      setError("Please fill in all required fields");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.put(`/expenses/${params.id}`, {
        title,
        category,
        amount,
        expense_date: expenseDate ? new Date(expenseDate).toISOString() : new Date().toISOString(),
        notes: notes || null,
      });
      router.push("/expenses");
      return;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update expense");
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
          href="/expenses"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-3.5" />
          Back to Expenses
        </Link>

        <div className="mt-6 mb-8">
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Edit Expense</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Update expense details.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="title" className="text-sm font-medium">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label className="text-sm font-medium">Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {expenseCategories.map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="amount" className="text-sm font-medium">Amount (PKR)</Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="expense_date" className="text-sm font-medium">Date</Label>
              <Input
                id="expense_date"
                type="datetime-local"
                value={expenseDate}
                onChange={(e) => setExpenseDate(e.target.value)}
              />
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
            <Link href="/expenses">
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
