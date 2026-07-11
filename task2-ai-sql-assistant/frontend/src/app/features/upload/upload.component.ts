import { CommonModule } from "@angular/common";
import { Component, OnInit, inject, signal } from "@angular/core";
import { Router } from "@angular/router";

import { ApiService } from "../../core/services/api.service";
import { Dataset } from "../../core/models/models";

@Component({
  selector: "app-upload",
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-8 max-w-4xl mx-auto">
      <div class="mb-6">
        <h1 class="text-2xl font-semibold text-gray-900">Datasets</h1>
        <p class="text-sm text-gray-500 mt-1">
          Upload any CSV or Excel file — schema is detected automatically and a table is created for you.
        </p>
      </div>

      <div
        class="border-2 border-dashed border-gray-200 rounded-card p-10 text-center mb-6 hover:border-accent transition-colors cursor-pointer bg-white"
        (click)="fileInput.click()"
        (dragover)="$event.preventDefault()"
        (drop)="onDrop($event)"
      >
        <input #fileInput type="file" accept=".csv,.xlsx,.xls" class="hidden" (change)="onFileSelected($event)" />
        <p class="text-sm font-medium text-gray-700">Click to upload or drag and drop</p>
        <p class="text-xs text-gray-400 mt-1">CSV, XLSX, XLS — up to 25MB</p>
      </div>

      @if (uploading()) {
        <p class="text-sm text-accent mb-4">Uploading and detecting schema...</p>
      }
      @if (error()) {
        <div class="mb-6 rounded-card bg-status-error-bg text-status-error-text text-sm px-4 py-3">
          {{ error() }}
        </div>
      }

      <div class="space-y-3">
        @for (d of datasets(); track d.id) {
          <div
            class="bg-white rounded-card p-5 shadow-sm border border-gray-100 flex items-center justify-between cursor-pointer hover:border-accent transition-colors"
            (click)="openDataset(d.id)"
          >
            <div>
              <p class="font-medium text-gray-900">{{ d.name }}</p>
              <p class="text-xs text-gray-400 mt-0.5">
                {{ d.row_count }} rows · {{ d.columns_metadata.length }} columns · {{ d.file_type.toUpperCase() }}
              </p>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-xs text-accent font-medium">Query &rarr;</span>
              <button (click)="remove($event, d.id)" class="text-xs text-gray-400 hover:text-rose-600">
                Remove
              </button>
            </div>
          </div>
        }
        @if (datasets().length === 0 && !uploading()) {
          <p class="text-sm text-gray-400 text-center py-8">No datasets uploaded yet.</p>
        }
      </div>
    </div>
  `,
})
export class UploadComponent implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);

  datasets = signal<Dataset[]>([]);
  uploading = signal(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.api.listDatasets().subscribe((d) => this.datasets.set(d));
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) this.upload(input.files[0]);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    if (event.dataTransfer?.files.length) this.upload(event.dataTransfer.files[0]);
  }

  upload(file: File): void {
    this.uploading.set(true);
    this.error.set(null);
    this.api.uploadDataset(file).subscribe({
      next: (dataset) => {
        this.uploading.set(false);
        this.load();
        this.router.navigate(["/datasets", dataset.id, "query"]);
      },
      error: (e) => {
        this.uploading.set(false);
        this.error.set(e.message);
      },
    });
  }

  openDataset(id: string): void {
    this.router.navigate(["/datasets", id, "query"]);
  }

  remove(event: Event, id: string): void {
    event.stopPropagation();
    this.api.deleteDataset(id).subscribe(() => this.load());
  }
}
