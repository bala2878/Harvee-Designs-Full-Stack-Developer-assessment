import { CommonModule } from "@angular/common";
import { Component, OnInit, inject, signal } from "@angular/core";

import { ApiService } from "../../core/services/api.service";
import { DashboardSummary } from "../../core/models/models";

@Component({
  selector: "app-dashboard",
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-8 max-w-6xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p class="text-sm text-gray-500 mt-1">Live allocation statistics across all courses.</p>
        </div>
        <button
          (click)="runAllocation()"
          [disabled]="running()"
          class="bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
        >
          {{ running() ? "Running allocation..." : "Run Allocation" }}
        </button>
      </div>

      @if (error()) {
        <div class="mb-6 rounded-card bg-status-rejected-bg text-status-rejected-text text-sm px-4 py-3">
          {{ error() }}
        </div>
      }

      @if (summary(); as s) {
        <!-- Stat cards -->
        <div class="grid grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100">
            <p class="text-xs text-gray-500 mb-1">Total Students</p>
            <p class="text-2xl font-semibold text-gray-900">{{ s.total_students }}</p>
          </div>
          <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100">
            <p class="text-xs text-gray-500 mb-1">Total Seats</p>
            <p class="text-2xl font-semibold text-gray-900">{{ s.total_seats }}</p>
          </div>
          <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100">
            <p class="text-xs text-gray-500 mb-1">Allocated</p>
            <p class="text-2xl font-semibold text-emerald-600">{{ s.total_allocated }}</p>
          </div>
          <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100">
            <p class="text-xs text-gray-500 mb-1">Not Allocated</p>
            <p class="text-2xl font-semibold text-rose-600">{{ s.total_unallocated }}</p>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4">
          <!-- Fill rate & 1st pref match -->
          <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100 col-span-1 space-y-4">
            <div>
              <p class="text-xs text-gray-500 mb-1">Overall Fill Rate</p>
              <p class="text-xl font-semibold text-gray-900">{{ s.overall_fill_rate_percent }}%</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1">1st Preference Match Rate</p>
              <p class="text-xl font-semibold text-gray-900">{{ s.first_preference_match_rate_percent }}%</p>
            </div>
          </div>

          <!-- Category-wise allocation -->
          <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100 col-span-2">
            <p class="text-xs text-gray-500 mb-3">Category-wise Allocation</p>
            <div class="space-y-2">
              @for (cat of categoryEntries(s); track cat.key) {
                <div class="flex items-center gap-3">
                  <span class="text-xs text-gray-600 w-16">{{ cat.key }}</span>
                  <div class="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div class="bg-accent h-full rounded-full" [style.width.%]="cat.percent"></div>
                  </div>
                  <span class="text-xs font-medium text-gray-700 w-8 text-right">{{ cat.value }}</span>
                </div>
              }
            </div>
          </div>
        </div>

        @if (s.latest_run) {
          <div class="mt-6 bg-white rounded-card p-5 shadow-sm border border-gray-100 text-sm text-gray-600">
            Latest run: <span class="font-medium text-gray-900">{{ s.latest_run.status }}</span> —
            {{ s.latest_run.total_allocated }} allocated / {{ s.latest_run.total_students }} students
            ({{ s.latest_run.started_at | date: "medium" }})
          </div>
        }
      } @else {
        <p class="text-sm text-gray-400">Loading dashboard...</p>
      }
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);

  summary = signal<DashboardSummary | null>(null);
  running = signal(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.api.getDashboardSummary().subscribe({
      next: (s) => this.summary.set(s),
      error: (e) => this.error.set(e.message),
    });
  }

  runAllocation(): void {
    this.running.set(true);
    this.error.set(null);
    this.api.runAllocation().subscribe({
      next: () => {
        this.running.set(false);
        this.load();
      },
      error: (e) => {
        this.running.set(false);
        this.error.set(e.message);
      },
    });
  }

  categoryEntries(s: DashboardSummary): { key: string; value: number; percent: number }[] {
    const max = Math.max(...Object.values(s.category_wise_allocation), 1);
    return Object.entries(s.category_wise_allocation).map(([key, value]) => ({
      key,
      value,
      percent: (value / max) * 100,
    }));
  }
}
