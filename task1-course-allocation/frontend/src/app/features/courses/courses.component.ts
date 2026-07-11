import { CommonModule } from "@angular/common";
import { Component, OnInit, inject, signal } from "@angular/core";
import { FormsModule } from "@angular/forms";

import { ApiService } from "../../core/services/api.service";
import { Category, Course, CourseStats } from "../../core/models/models";

@Component({
  selector: "app-courses",
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-8 max-w-6xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">Courses</h1>
          <p class="text-sm text-gray-500 mt-1">{{ courses().length }} courses configured</p>
        </div>
        <button
          (click)="showForm.set(!showForm())"
          class="bg-accent hover:bg-accent-hover text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
        >
          {{ showForm() ? "Cancel" : "+ Add Course" }}
        </button>
      </div>

      @if (showForm()) {
        <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100 mb-6 space-y-4">
          <div class="grid grid-cols-3 gap-4">
            <input [(ngModel)]="form.name" placeholder="Course name" class="input" />
            <input [(ngModel)]="form.code" placeholder="Code (e.g. CSE)" class="input" />
            <input [(ngModel)]="form.total_seats" type="number" placeholder="Total seats" class="input" />
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-2">Reserved seats by category (optional — remainder is General)</p>
            <div class="grid grid-cols-3 gap-3">
              @for (cat of reservableCategories; track cat) {
                <div class="flex items-center gap-2">
                  <span class="text-xs text-gray-600 w-14">{{ cat }}</span>
                  <input type="number" [(ngModel)]="reservations[cat]" class="input" placeholder="0" />
                </div>
              }
            </div>
          </div>
          @if (formError()) {
            <p class="text-xs text-rose-600">{{ formError() }}</p>
          }
          <button
            (click)="submit()"
            class="bg-accent hover:bg-accent-hover text-white text-sm font-medium px-4 py-2 rounded-lg"
          >
            Create Course
          </button>
        </div>
      }

      <div class="grid grid-cols-2 gap-4">
        @for (c of coursesWithStats(); track c.id) {
          <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100">
            <div class="flex items-start justify-between mb-3">
              <div>
                <p class="font-semibold text-gray-900">{{ c.name }}</p>
                <p class="text-xs text-gray-400">{{ c.code }}</p>
              </div>
              <button (click)="remove(c.id)" class="text-xs text-gray-400 hover:text-rose-600">Remove</button>
            </div>
            @if (c.stats; as stats) {
              <div class="grid grid-cols-3 gap-3 text-center mb-3">
                <div>
                  <p class="text-lg font-semibold text-gray-900">{{ stats.seats_filled }}/{{ c.total_seats }}</p>
                  <p class="text-[11px] text-gray-400">Filled</p>
                </div>
                <div>
                  <p class="text-lg font-semibold text-emerald-600">{{ stats.seats_available }}</p>
                  <p class="text-[11px] text-gray-400">Available</p>
                </div>
                <div>
                  <p class="text-lg font-semibold text-rose-600">{{ stats.rejection_rate_percent }}%</p>
                  <p class="text-[11px] text-gray-400">Rejection Rate</p>
                </div>
              </div>
              <div class="flex flex-wrap gap-1.5">
                @for (cat of objectEntries(stats.category_wise_allocations); track cat.key) {
                  <span class="pill bg-accent-light text-accent">{{ cat.key }}: {{ cat.value }}</span>
                }
              </div>
            } @else {
              <p class="text-xs text-gray-400">Loading stats...</p>
            }
          </div>
        }
      </div>
    </div>
  `,
  styles: [
    `
      .input {
        @apply border border-gray-200 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-accent/30;
      }
    `,
  ],
})
export class CoursesComponent implements OnInit {
  private api = inject(ApiService);

  courses = signal<Course[]>([]);
  statsMap = signal<Record<string, CourseStats>>({});
  showForm = signal(false);
  formError = signal<string | null>(null);

  reservableCategories: Category[] = ["OBC", "SC", "ST"];
  reservations: Record<string, number> = { OBC: 0, SC: 0, ST: 0 };
  form = { name: "", code: "", total_seats: 0 };

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.api.listCourses().subscribe((courses) => {
      this.courses.set(courses);
      courses.forEach((c) => {
        this.api.getCourseStats(c.id).subscribe((stats) => {
          this.statsMap.update((m) => ({ ...m, [c.id]: stats }));
        });
      });
    });
  }

  coursesWithStats() {
    return this.courses().map((c) => ({ ...c, stats: this.statsMap()[c.id] }));
  }

  objectEntries(obj: Record<string, number>) {
    return Object.entries(obj).map(([key, value]) => ({ key, value }));
  }

  submit(): void {
    this.formError.set(null);
    if (!this.form.name || !this.form.code || !this.form.total_seats) {
      this.formError.set("Name, code, and total seats are required.");
      return;
    }
    const reservations = this.reservableCategories
      .filter((cat) => this.reservations[cat] > 0)
      .map((cat) => ({ category: cat, reserved_seats: Number(this.reservations[cat]) }));

    this.api
      .createCourse({
        name: this.form.name,
        code: this.form.code,
        total_seats: Number(this.form.total_seats),
        reservations,
      })
      .subscribe({
        next: () => {
          this.showForm.set(false);
          this.form = { name: "", code: "", total_seats: 0 };
          this.reservations = { OBC: 0, SC: 0, ST: 0 };
          this.load();
        },
        error: (e) => this.formError.set(e.message),
      });
  }

  remove(id: string): void {
    this.api.deleteCourse(id).subscribe(() => this.load());
  }
}
