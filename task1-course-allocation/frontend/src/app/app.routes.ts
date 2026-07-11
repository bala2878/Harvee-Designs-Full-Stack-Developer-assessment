import { Routes } from "@angular/router";

export const routes: Routes = [
  { path: "", redirectTo: "dashboard", pathMatch: "full" },
  {
    path: "dashboard",
    loadComponent: () => import("./features/dashboard/dashboard.component").then((m) => m.DashboardComponent),
    title: "Dashboard",
  },
  {
    path: "students",
    loadComponent: () => import("./features/students/students.component").then((m) => m.StudentsComponent),
    title: "Students",
  },
  {
    path: "courses",
    loadComponent: () => import("./features/courses/courses.component").then((m) => m.CoursesComponent),
    title: "Courses",
  },
  {
    path: "allocation",
    loadComponent: () =>
      import("./features/allocation/allocation.component").then((m) => m.AllocationComponent),
    title: "Allocation",
  },
  {
    path: "ai-assistant",
    loadComponent: () => import("./features/ai-chat/ai-chat.component").then((m) => m.AiChatComponent),
    title: "AI Assistant",
  },
  { path: "**", redirectTo: "dashboard" },
];
