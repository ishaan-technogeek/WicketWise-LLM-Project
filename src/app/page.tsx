"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

// moved to page.tsx to avoid use client issues
// export const metadata: Metadata = {
//   title: 'WicketWise',
//   description: 'Your personal AI IPL data assistant',
// };

export default function Home() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
    const { toast } = useToast();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isLogin && password !== confirmPassword) {
            toast({
                variant: "destructive",
                title: "Error",
                description: "Passwords do not match."
            });
      return;
    }

    // Simulate authentication
    if (isLogin) {
            toast({
                title: "Login Successful",
                description: `Welcome back ${email}!`
            });
      router.push("/dashboard");
    } else {
            toast({
                title: "Sign Up Successful",
                description: "Please log in with your new credentials.",
            });
      setIsLogin(true);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="w-full max-w-md space-y-4">
        <CardHeader className="space-y-2">
          <CardTitle>{isLogin ? "Login" : "Sign Up"}</CardTitle>
          <CardDescription>Enter your credentials to access WicketWise.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <Input
                  type="text"
                  placeholder="Full Name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>
            )}
            <div>
              <Input
                type="email"
                placeholder="Email/Username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {!isLogin && (
              <div>
                <Input
                  type="password"
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
            )}
            <Button type="submit" className="w-full">
              {isLogin ? "Login" : "Sign Up"}
            </Button>
          </form>
          <div className="text-sm text-muted-foreground">
            {isLogin ? (
              <>
                Don't have an account?{" "}
                <Button variant="link" onClick={() => setIsLogin(false)}>
                  Sign Up
                </Button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <Button variant="link" onClick={() => setIsLogin(true)}>
                  Login
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


