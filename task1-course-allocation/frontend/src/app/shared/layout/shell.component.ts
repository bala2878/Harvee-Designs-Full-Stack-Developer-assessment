import { Component } from "@angular/core";
import { RouterLink, RouterLinkActive, RouterOutlet } from "@angular/router";

interface NavItem {
  label: string;
  path: string;
  icon: string; // simple inline SVG path data, kept minimal — no icon lib dependency
}

@Component({
  selector: "app-shell",
  standalone: true,
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  template: `
    <div class="flex h-screen overflow-hidden">
      <!-- Sidebar -->
      <aside class="w-64 shrink-0 bg-navy text-white flex flex-col">
        <div class="px-6 py-5 border-b border-white/10">
          <p class="text-lg font-semibold tracking-tight">Allocation<span class="text-accent">.</span></p>
          <p class="text-xs text-white/50 mt-0.5">University Course Allocation</p>
        </div>
        <nav class="flex-1 px-3 py-4 space-y-1">
          @for (item of navItems; track item.path) {
            <a
              [routerLink]="item.path"
              routerLinkActive="bg-accent/20 text-white"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/70 hover:bg-white/5 hover:text-white transition-colors"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
              {{ item.label }}
            </a>
          }
        </nav>
        <div class="px-6 py-4 border-t border-white/10 text-xs text-white/40">
          Harvee Designs — Assessment Build
        </div>
      </aside>

      <!-- Main content -->
      <main class="flex-1 overflow-y-auto bg-[#F8F9FC]">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
})
export class ShellComponent {
  navItems: NavItem[] = [
    { label: "Dashboard", path: "/dashboard", icon: "" },
    { label: "Students", path: "/students", icon: "" },
    { label: "Courses", path: "/courses", icon: "" },
    { label: "Allocation", path: "/allocation", icon: "" },
    { label: "AI Assistant", path: "/ai-assistant", icon: "" },
  ];
}
