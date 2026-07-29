"use client";

import { useCallback, useEffect, useState } from "react";
import { Edit3, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ColorPicker } from "@/components/ui/color-picker";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  Category,
  categoriesApi,
} from "@/lib/api/categories";

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  const [dialog, setDialog] = useState<"create" | "edit" | null>(null);
  const [editing, setEditing] = useState<Category | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Category | null>(null);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [color, setColor] = useState<string | null>(null);
  const [isActive, setIsActive] = useState(true);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await categoriesApi.list();
      setCategories(data);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function resetForm() {
    setName("");
    setDescription("");
    setColor(null);
    setIsActive(true);
    setEditing(null);
    setError(null);
    setDialog(null);
  }

  function openCreate() {
    resetForm();
    setDialog("create");
  }

  function openEdit(cat: Category) {
    setName(cat.name);
    setDescription(cat.description ?? "");
    setColor(cat.color);
    setIsActive(cat.is_active);
    setEditing(cat);
    setError(null);
    setDialog("edit");
  }

  async function handleSave() {
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (dialog === "create") {
        await categoriesApi.create({
          name: name.trim(),
          description: description.trim() || null,
          color,
          is_active: isActive,
        });
      } else if (editing) {
        await categoriesApi.update(editing.id, {
          name: name.trim() || null,
          description: description.trim() || null,
          color,
          is_active: isActive,
        });
      }
      resetForm();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await categoriesApi.remove(id);
      setDeleteConfirm(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete");
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-foreground">Categories</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {categories.length} categor{categories.length === 1 ? "y" : "ies"}
          </p>
        </div>
        <Button size="sm" onClick={openCreate}>
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          New Category
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center text-sm text-muted-foreground">Loading...</div>
      ) : categories.length === 0 ? (
        <div className="py-12 text-center text-sm text-muted-foreground">
          No categories yet — create your first one.
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs font-semibold uppercase tracking-wider">Name</TableHead>
              <TableHead className="text-xs font-semibold uppercase tracking-wider">Description</TableHead>
              <TableHead className="text-xs font-semibold uppercase tracking-wider">Status</TableHead>
              <TableHead className="w-20" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {categories.map((cat) => (
              <TableRow key={cat.id}>
                <TableCell>
                  <div className="flex items-center gap-2.5">
                    {cat.color && (
                      <span
                        className="h-2.5 w-2.5 rounded-full border border-border"
                        style={{ backgroundColor: cat.color }}
                      />
                    )}
                    <span className="font-medium">{cat.name}</span>
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">{cat.description || "—"}</TableCell>
                <TableCell>
                  <Badge
                    variant={cat.is_active ? "default" : "secondary"}
                    className="rounded-md text-xs font-medium"
                  >
                    {cat.is_active ? "Active" : "Inactive"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => openEdit(cat)}
                      className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground cursor-pointer"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(cat)}
                      className="rounded-md p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive cursor-pointer"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Dialog open={dialog !== null} onOpenChange={(o) => { if (!o) resetForm(); }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{dialog === "create" ? "New Category" : "Edit Category"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Category name" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Description</label>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Color Tag</label>
              <ColorPicker value={color} onChange={setColor} />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">Status</label>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setIsActive(true)}
                  className={`cursor-pointer rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                    isActive
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Active
                </button>
                <button
                  type="button"
                  onClick={() => setIsActive(false)}
                  className={`cursor-pointer rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
                    !isActive
                      ? "border-destructive bg-destructive/5 text-destructive"
                      : "border-border text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Inactive
                </button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={resetForm} disabled={saving}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : dialog === "create" ? "Create" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteConfirm !== null} onOpenChange={(o) => { if (!o) setDeleteConfirm(null); }}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Delete Category</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Are you sure you want to delete <strong className="text-foreground">{deleteConfirm?.name}</strong>? This cannot be undone.
          </p>
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={() => setDeleteConfirm(null)}>
              Cancel
            </Button>
            <Button
              size="sm"
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => deleteConfirm && handleDelete(deleteConfirm.id)}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
