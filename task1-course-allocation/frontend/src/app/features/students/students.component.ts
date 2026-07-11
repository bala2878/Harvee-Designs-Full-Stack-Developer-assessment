import { CommonModule } from "@angular/common";
import { Component, OnInit, inject, signal } from "@angular/core";
import { FormsModule } from "@angular/forms";

import { ApiService } from "../../core/services/api.service";
import { Category, Course, Student } from "../../core/models/models";

@Component({
  selector: "app-students",
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-8 max-w-6xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">Students</h1>
          <p class="text-sm text-gray-500 mt-1">{{ students().length }} registered</p>
        </div>
        <button
          (click)="showForm.set(!showForm())"
          class="bg-accent hover:bg-accent-hover text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
        >
          {{ showForm() ? "Cancel" : "+ Register Student" }}
        </button>
      </div>

      @if (showForm()) {
        <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100 mb-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <input [(ngModel)]="form.name" placeholder="Full name" class="input" />
            <input [(ngModel)]="form.email" placeholder="Email" class="input" />
            <input [(ngModel)]="form.marks" type="number" placeholder="Marks (0-100)" class="input" />
            <select [(ngModel)]="form.category" class="input">
              <option value="GENERAL">General</option>
              <option value="OBC">OBC</option>
              <option value="SC">SC</option>
              <option value="ST">ST</option>
            </select>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-2">Preferred courses (in priority order)</p>
            <div class="flex flex-wrap gap-2">
              @for (c of courses(); track c.id) {
                <button
                  type="button"
                  (click)="togglePreference(c.id)"
                  class="text-xs px-3 py-1.5 rounded-full border transition-colors"
                  [class]="isSelected(c.id) ? 'bg-accent text-white border-accent' : 'border-gray-200 text-gray-600'"
                >
                  {{ preferenceRank(c.id) ? preferenceRank(c.id) + '. ' : '' }}{{ c.name }}
                </button>
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
            Register
          </button>
        </div>
      }

      <div class="bg-white rounded-card shadow-sm border border-gray-100 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
            <tr>
              <th class="text-left px-4 py-3">Code</th>
              <th class="text-left px-4 py-3">Name</th>
              <th class="text-left px-4 py-3">Marks</th>
              <th class="text-left px-4 py-3">Category</th>
              <th class="text-left px-4 py-3">Applied</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            @for (s of students(); track s.id) {
              <tr class="border-t border-gray-50 hover:bg-gray-50/50">
                <td class="px-4 py-3 text-gray-500">{{ s.student_code }}</td>
                <td class="px-4 py-3 font-medium text-gray-900">{{ s.name }}</td>
                <td class="px-4 py-3">{{ s.marks }}</td>
                <td class="px-4 py-3">
                  <span class="pill bg-accent-light text-accent">{{ s.category }}</span>
                </td>
                <td class="px-4 py-3 text-gray-500">{{ s.application_date }}</td>
                <td class="px-4 py-3 text-right">
                  <button (click)="remove(s.id)" class="text-xs text-gray-400 hover:text-rose-600">Remove</button>
                </td>
              </tr>
            }
          </tbody>
        </table>
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
export class StudentsComponent implements OnInit {
  private api = inject(ApiService);

  students = signal<Student[]>([]);
  courses = signal<Course[]>([]);
  showForm = signal(false);
  formError = signal<string | null>(null);

  form = { name: "", email: "", marks: 0, category: "GENERAL" as Category };
  selectedPreferences: string[] = []; // ordered course ids, index+1 = priority

  ngOnInit(): void {
    this.load();
    this.api.listCourses().subscribe((c) => this.courses.set(c));
  }

  load(): void {
    this.api.listStudents().subscribe((s) => this.students.set(s));
  }

  togglePreference(courseId: string): void {
    const idx = this.selectedPreferences.indexOf(courseId);
    if (idx >= 0) {
      this.selectedPreferences.splice(idx, 1);
    } else {
      this.selectedPreferences.push(courseId);
    }
  }

  isSelected(courseId: string): boolean {
    return this.selectedPreferences.includes(courseId);
  }

  preferenceRank(courseId: string): number {
    return this.selectedPreferences.indexOf(courseId) + 1;
  }

  submit(): void {
    this.formError.set(null);
    if (!this.form.name || !this.form.email || this.selectedPreferences.length === 0) {
      this.formError.set("Name, email, and at least one preferred course are required.");
      return;
    }
    this.api
      .createStudent({
        name: this.form.name,
        email: this.form.email,
        marks: Number(this.form.marks),
        category: this.form.category,
        preferences: this.selectedPreferences.map((course_id, i) => ({ course_id, priority: i + 1 })),
      })
      .subscribe({
        next: () => {
          this.showForm.set(false);
          this.form = { name: "", email: "", marks: 0, category: "GENERAL" };
          this.selectedPreferences = [];
          this.load();
        },
        error: (e) => this.formError.set(e.message),
      });
  }

  remove(id: string): void {
    this.api.deleteStudent(id).subscribe(() => this.load());
  }
}
