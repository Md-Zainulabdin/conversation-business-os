"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Store, KeyRound, User, AlertTriangle } from "lucide-react";

import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { PageHeader } from "@/components/shared/page-header";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

const currencies = ["PKR", "USD", "INR", "GBP", "EUR", "AED", "SAR"];

export default function SettingsPage() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const [storeName, setStoreName] = useState("");
  const [currency, setCurrency] = useState("PKR");
  const [userName, setUserName] = useState("");
  const [storeSaving, setStoreSaving] = useState(false);
  const [nameSaving, setNameSaving] = useState(false);
  const [storeMessage, setStoreMessage] = useState<string | null>(null);
  const [nameMessage, setNameMessage] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (user) {
      setStoreName(user.store_name || "");
      setCurrency(user.currency || "PKR");
      setUserName(user.name);
    }
  }, [user]);

  const handleSaveStore = async (e: React.FormEvent) => {
    e.preventDefault();
    setStoreSaving(true);
    setStoreMessage(null);
    try {
      await useAuthStore.getState().updateProfile({ store_name: storeName, currency });
      setStoreMessage("Saved.");
    } catch {
      // handled by store
    } finally {
      setStoreSaving(false);
    }
  };

  const handleSaveName = async () => {
    setNameSaving(true);
    setNameMessage(null);
    try {
      await useAuthStore.getState().updateProfile({ name: userName });
      setNameMessage("Saved.");
    } catch {
      // handled by store
    } finally {
      setNameSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordSaving(true);
    setPasswordError(null);
    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSaving(false);
      logout();
      router.push("/login");
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : "Failed to change password");
      setPasswordSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await api.delete("/auth/me");
      logout();
      router.push("/register");
    } catch {
      setDeleting(false);
      setConfirmOpen(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <PageHeader title="Settings" description="Manage your store and account." />

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="rounded-xl border border-border bg-card p-5 space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-foreground">
              <Store className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Store Details</h2>
              <p className="text-xs text-muted-foreground">Store name and default currency.</p>
            </div>
          </div>
          <form onSubmit={handleSaveStore} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="storeName">Store name</Label>
              <Input
                id="storeName"
                value={storeName}
                onChange={(e) => setStoreName(e.target.value)}
                placeholder="Your store name"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="currency">Currency</Label>
              <select
                id="currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="flex h-9 w-full items-center justify-between rounded-md border border-border bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {currencies.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-3">
              <Button type="submit" size="sm" disabled={storeSaving}>
                {storeSaving ? (
                  <>
                    <Spinner data-icon="inline-start" />
                    Saving
                  </>
                ) : (
                  "Save"
                )}
              </Button>
              {storeMessage && (
                <span className="text-xs text-emerald-600">{storeMessage}</span>
              )}
            </div>
          </form>
        </section>

        <section className="rounded-xl border border-border bg-card p-5 space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-foreground">
              <User className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Profile</h2>
              <p className="text-xs text-muted-foreground">Your display name and email.</p>
            </div>
          </div>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="userName">Name</Label>
              <Input id="userName" value={userName} onChange={(e) => setUserName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={user?.email || ""} disabled />
              <p className="text-xs text-muted-foreground">Email cannot be changed.</p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                type="button"
                size="sm"
                onClick={handleSaveName}
                disabled={nameSaving}
              >
                {nameSaving ? (
                  <>
                    <Spinner data-icon="inline-start" />
                    Saving
                  </>
                ) : (
                  "Save"
                )}
              </Button>
              {nameMessage && (
                <span className="text-xs text-emerald-600">{nameMessage}</span>
              )}
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card p-5 space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-foreground">
              <KeyRound className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Change Password</h2>
              <p className="text-xs text-muted-foreground">Keep your account secure.</p>
            </div>
          </div>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="currentPassword">Current password</Label>
              <Input
                id="currentPassword"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="newPassword">New password</Label>
              <Input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>
            {passwordError && (
              <p className="text-xs text-destructive">{passwordError}</p>
            )}
            <div className="flex items-center gap-3">
              <Button type="submit" size="sm" disabled={passwordSaving}>
                {passwordSaving && <Spinner data-icon="inline-start" />}
                Change Password
              </Button>
            </div>
          </form>
        </section>

        <section className="rounded-xl border border-destructive/40 bg-card p-5 space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Danger Zone</h2>
              <p className="text-xs text-muted-foreground">Permanently remove your account and all data.</p>
            </div>
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setConfirmOpen(true)}
          >
            Delete Account
          </Button>
        </section>
      </div>

      <Dialog open={confirmOpen} onOpenChange={() => setConfirmOpen(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Account</DialogTitle>
            <DialogDescription>
              This permanently deletes your account, products, sales, purchases,
              expenses, and customers. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setConfirmOpen(false)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="destructive" size="sm" onClick={handleDeleteAccount} disabled={deleting}>
              {deleting && <Spinner data-icon="inline-start" />}
              {deleting ? "Deleting" : "Delete Account"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}