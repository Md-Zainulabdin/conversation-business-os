"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/store/auth";

const registerSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Invalid email"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type RegisterData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser, loading, error, clearError } = useAuthStore();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterData) => {
    await registerUser(data);
    if (!useAuthStore.getState().error) {
      router.push("/login");
    }
  };

  return (
    <div className="w-full max-w-sm">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Create account</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">Enter your details to get started</p>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div className="space-y-1.5">
          <Label htmlFor="name" className="text-sm font-medium">Name</Label>
          <Input
            id="name"
            placeholder="John Doe"
            {...register("name")}
          />
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="email" className="text-sm font-medium">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="name@example.com"
            {...register("email")}
          />
          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password" className="text-sm font-medium">Password</Label>
          <Input
            id="password"
            type="password"
            placeholder="Create a password"
            {...register("password")}
          />
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>
        {error && (
          <div className="rounded-md border border-destructive/20 bg-destructive/5 px-3 py-2 text-sm text-destructive">{error}</div>
        )}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating account..." : "Create account"}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <button type="button" className="font-medium text-primary hover:text-primary/80" onClick={() => { clearError(); router.push("/login"); }}>
            Sign in
          </button>
        </p>
      </form>
    </div>
  );
}
