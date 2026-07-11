import { CommonModule } from "@angular/common";
import { Component, OnInit, inject, signal } from "@angular/core";

import { ApiService } from "../../core/services/api.service";
import { AllocationRow } from "../../core/models/models";

@Component({
  selector: "app-allocation",
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-8 max-w-6xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">Allocation Results</h1>
          <p class="text-sm text-gray-500 mt-1">{{ filtered().length }} of {{ rows().length }} students shown</p>
        </div>
        <div class="flex gap-2">
          @for (f of filters; track f.value) {
            <button
              (click)="activeFilter.set(f.value)"
              class="text-xs px-3 py-1.5 rounded-full border transition-colors"
              [class]="
                activeFilter() === f.value ? 'bg-accent text-white border-accent' : 'border-gray-200 text-gray-600'
              "
            >
              {{ f.label }}
            </button>
          }
        </div>
      </div>

      <div class="bg-white rounded-card shadow-sm border border-gray-100 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
            <tr>
              <th class="text-left px-4 py-3">Student</th>
              <th class="text-left px-4 py-3">Category</th>
              <th class="text-left px-4 py-3">Allocated Course</th>
              <th class="text-left px-4 py-3">Preference Rank</th>
              <th class="text-left px-4 py-3">Status</th>
              <th class="text-left px-4 py-3">Reason</th>
            </tr>
          </thead>
          <tbody>
            @for (r of filtered(); track r.student_id) {
              <tr class="border-t border-gray-50 hover:bg-gray-50/50">
                <td class="px-4 py-3">
                  <p class="font-medium text-gray-900">{{ r.student_name }}</p>
                  <p class="text-xs text-gray-400">{{ r.student_code }}</p>
                </td>
                <td class="px-4 py-3">{{ r.category }}</td>
                <td class="px-4 py-3">{{ r.course_name ?? "—" }}</td>
                <td class="px-4 py-3">{{ r.preference_rank_matched ?? "—" }}</td>
                <td class="px-4 py-3">
                  @if (r.status === "ALLOCATED") {
                    <span class="pill bg-status-allocated-bg text-status-allocated-text">Allocated</span>
                  } @else {
                    <span class="pill bg-status-rejected-bg text-status-rejected-text">Not Allocated</span>
                  }
                </td>
                <td class="px-4 py-3 text-xs text-gray-500">{{ r.reason }}</td>
              </tr>
            }
          </tbody>
        </table>
        @if (rows().length === 0) {
          <p class="text-sm text-gray-400 text-center py-8">
            No allocation results yet — run the allocation from the Dashboard.
          </p>
        }
      </div>
    </div>
  `,
})
export class AllocationComponent implements OnInit {
  private api = inject(ApiService);

  rows = signal<AllocationRow[]>([]);
  activeFilter = signal<"ALL" | "ALLOCATED" | "NOT_ALLOCATED">("ALL");

  filters: { label: string; value: "ALL" | "ALLOCATED" | "NOT_ALLOCATED" }[] = [
    { label: "All", value: "ALL" },
    { label: "Allocated", value: "ALLOCATED" },
    { label: "Not Allocated", value: "NOT_ALLOCATED" },
  ];

  ngOnInit(): void {
    this.api.getAllocationResults().subscribe((rows) => this.rows.set(rows));
  }

  filtered(): AllocationRow[] {
    const f = this.activeFilter();
    return f === "ALL" ? this.rows() : this.rows().filter((r) => r.status === f);
  }
}
