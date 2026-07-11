import { Component } from "@angular/core";
import { RouterOutlet } from "@angular/router";

@Component({
  selector: "app-shell",
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="flex h-screen overflow-hidden">
      <aside class="w-64 shrink-0 bg-navy text-white flex flex-col">
        <div class="px-6 py-5 border-b border-white/10">
          <p class="text-lg font-semibold tracking-tight">SQL Assistant<span class="text-accent">.</span></p>
          <p class="text-xs text-white/50 mt-0.5">AI-Powered Analytics</p>
        </div>
        <div class="px-6 py-4 text-xs text-white/40 mt-auto">Harvee Designs — Assessment Build</div>
      </aside>
      <main class="flex-1 overflow-y-auto bg-[#F8F9FC]">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
})
export class ShellComponent {}
