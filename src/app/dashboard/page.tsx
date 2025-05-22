"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from 'next/navigation';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { GenerateSummary } from "@/components/GenerateSummary";
import { HeadToHeadAnalyzer } from "@/components/HeadToHeadAnalyzer";
import { QueryAnswering } from "@/components/QueryAnswering";
import { WhatIfScenarios } from "@/components/WhatIfScenarios";
import { ContactUs } from "@/components/ContactUs";
import { AboutUs } from "@/components/AboutUs";
import { PastInsights } from "@/components/PastInsights";
import { PastQueries } from "@/components/PastQueries";
import { LogOut, Contact2, Info, ListOrdered, Search, Brain, File, Flame, Moon, Sun } from "lucide-react";
import { useTheme } from 'next-themes'
import React from "react";
import { DashboardProvider } from "@/contexts/dashboard-context";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";


const features = [
  { name: "Generate Summary", component: GenerateSummary, icon: Flame },
  { name: "Head-to-Head Analyzer", component: HeadToHeadAnalyzer, icon: Search },
  { name: "Query Answering", component: QueryAnswering, icon: ListOrdered },
  { name: "What-If Scenarios", component: WhatIfScenarios, icon: Brain },
];

const history = [
  { name: "Past Insights", component: PastInsights, icon: File },
  { name: "Past Queries", component: PastQueries, icon: ListOrdered },
];

const support = [
  { name: "Contact Us", component: ContactUs, icon: Contact2 },
  { name: "About Us", component: AboutUs, icon: Info },
];

export default function Dashboard() {
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleFeatureClick = (featureName: string) => {
    setSelectedFeature(featureName);
  };

  const handleLogout = () => {
    router.push('/');
  };

  const renderFeatureComponent = useCallback(() => {
    if (!selectedFeature) return null;

    let feature = features.find((f) => f.name === selectedFeature);
    if (!feature) feature = history.find((h) => h.name === selectedFeature);
    if (!feature) feature = support.find((s) => s.name === selectedFeature);

    if (!feature) return <div>Feature not found</div>;

    return (
      <div className="h-full">
        <feature.component />
      </div>
    );
  }, [selectedFeature]);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  return (
    <DashboardProvider>
      <SidebarProvider>
        <div className="flex min-h-screen bg-background">
          <Sidebar className="w-64 border-r flex-shrink-0 z-20 h-full fixed top-0 left-0">
            <SidebarHeader>
              <h1 className="text-2xl font-semibold p-4">WicketWise</h1>
            </SidebarHeader>
            <SidebarContent className="mt-4">
              <SidebarMenu>
                <li className="px-4 py-2 font-semibold text-sm text-muted-foreground">History</li>
                {history.map((item) => (
                  <SidebarMenuItem key={item.name}>
                    <SidebarMenuButton onClick={() => handleFeatureClick(item.name)} icon={item.icon}>
                      {item.icon && <item.icon className="mr-2 h-4 w-4" />}
                      {item.name}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
              <SidebarMenu>
                <li className="px-4 py-2 font-semibold text-sm text-muted-foreground">Features</li>
                {features.map((item) => (
                  <SidebarMenuItem key={item.name}>
                    <SidebarMenuButton onClick={() => handleFeatureClick(item.name)} icon={item.icon}>
                      {item.icon && <item.icon className="mr-2 h-4 w-4" />}
                      {item.name}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
              <SidebarMenu>
                <li className="px-4 py-2 font-semibold text-sm text-muted-foreground">Support</li>
                {support.map((item) => (
                  <SidebarMenuItem key={item.name}>
                    <SidebarMenuButton onClick={() => handleFeatureClick(item.name)} icon={item.icon}>
                      {item.icon && <item.icon className="mr-2 h-4 w-4" />}
                      {item.name}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarContent>
            <SidebarFooter>
            </SidebarFooter>
          </Sidebar>

          <div className="flex-1 flex flex-col md:ml-64">
            <header className="flex items-center justify-between p-4 border-b bg-background z-10 fixed top-0 right-0 left-64">
              <div className="flex-1 text-2xl font-semibold text-center">
                {selectedFeature || "Welcome to WicketWise"}
              </div>
              {mounted && <ThemeToggle toggleTheme={toggleTheme} />}
              <span className="mx-2"></span> {/* Added spacing here */}
              <ProfileDropdown onLogout={handleLogout} />
            </header>

            <div className="p-4 h-full mt-16">
              <main className="h-full">
                {!selectedFeature ? (
                  <div className="flex flex-col items-center justify-center h-full space-y-4">
                    <h2 className="text-3xl font-semibold">Hi User!</h2>
                    <p className="text-muted-foreground">Welcome to WicketWise – your personal IPL data assistant.</p>
                    <div className="flex space-x-4">
                      <Button onClick={() => handleFeatureClick("Generate Summary")}>Generate Summary</Button>
                      <Button onClick={() => handleFeatureClick("Head-to-Head Analyzer")}>Head-to-Head</Button>
                      <Button onClick={() => handleFeatureClick("Query Answering")}>Query Answering</Button>
                      <Button onClick={() => handleFeatureClick("What-If Scenarios")}>What-If Scenarios</Button>
                    </div>
                  </div>
                ) : (
                  renderFeatureComponent()
                )}
              </main>
            </div>
          </div>
        </div>
      </SidebarProvider>
    </DashboardProvider>
  );
}

const ProfileDropdown = ({ onLogout }: { onLogout: () => void }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState({ name: "User", email: "user@example.com" });
  const [tempProfile, setTempProfile] = useState({ ...profile });

  const handleSave = () => {
    setProfile({ ...tempProfile });
    setIsEditing(false);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarImage src="https://picsum.photos/id/11/50/50" alt={profile.name} />
            <AvatarFallback>{profile.name.charAt(0)}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuItem onClick={() => setIsEditing(true)}>
          View/Edit Profile
        </DropdownMenuItem>
        <DropdownMenuItem onClick={onLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          Logout
        </DropdownMenuItem>
      </DropdownMenuContent>

      {/* Profile Edit Dialog */}
      {isEditing && (
        <div className="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50 flex items-center justify-center">
          <Card className="max-w-md w-full p-4">
            <CardHeader>
              <CardTitle>Edit Profile</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid gap-2">
                <label htmlFor="name" className="text-right text-sm font-medium leading-none">
                  Name
                </label>
                <Input
                  type="text"
                  id="name"
                  value={tempProfile.name}
                  onChange={(e) => setTempProfile({ ...tempProfile, name: e.target.value })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div className="grid gap-2">
                <label htmlFor="email" className="text-right text-sm font-medium leading-none">
                  Email
                </label>
                <Input
                  type="email"
                  id="email"
                  value={tempProfile.email}
                  onChange={(e) => setTempProfile({ ...tempProfile, email: e.target.value })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="secondary" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSave}>Save Changes</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </DropdownMenu>
  );
};

interface ThemeToggleProps {
  toggleTheme: () => void;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ toggleTheme }) => {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <Button variant="ghost" className="h-8 w-8 p-0 rounded-full" onClick={toggleTheme}>
      {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
      <span className="sr-only">Toggle dark mode</span>
    </Button>
  );
};
