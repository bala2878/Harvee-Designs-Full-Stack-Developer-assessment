import { Routes } from "@angular/router";

export const routes: Routes = [
  { path: "", redirectTo: "datasets", pathMatch: "full" },
  {
    path: "datasets",
    loadComponent: () => import("./features/upload/upload.component").then((m) => m.UploadComponent),
    title: "Datasets",
  },
  {
    path: "datasets/:id/query",
    loadComponent: () => import("./features/query/query.component").then((m) => m.QueryComponent),
    title: "Query Assistant",
  },
  { path: "**", redirectTo: "datasets" },
];
