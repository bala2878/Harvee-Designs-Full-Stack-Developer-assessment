import { CommonModule } from "@angular/common";
import { Component, OnInit, inject, signal } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { ActivatedRoute, RouterLink } from "@angular/router";

import { ApiService } from "../../core/services/api.service";
import { Dataset, InsightsResult, QueryHistoryItem, QueryResult } from "../../core/models/models";
import { ResultsChartComponent } from "../../shared/results-chart/results-chart.component";

type Tab = "results" | "history" | "insights";
type ResultView = "table" | "chart";

@Component({
  selector: "app-query",
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, ResultsChartComponent],
  template: `
    @if (dataset(); as ds) {
    <div class="p-8 max-w-5xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <a routerLink="/datasets" class="text-xs text-gray-400 hover:text-accent">&larr; All datasets</a>
          <h1 class="text-2xl font-semibold text-gray-900 mt-1">{{ ds.name }}</h1>
          <p class="text-sm text-gray-500 mt-1">
            {{ ds.row_count }} rows ·
            {{ columnNamesList(ds) }}
          </p>
        </div>
      </div>

      <div class="flex flex-wrap gap-2 mb-4">
        @for (q of sampleQuestions; track q) {
          <button
            (click)="ask(q)"
            class="text-xs px-3 py-1.5 rounded-full border border-gray-200 text-gray-600 hover:border-accent hover:text-accent transition-colors"
          >
            {{ q }}
          </button>
        }
      </div>

      <form (ngSubmit)="submit()" class="flex gap-2 mb-6">
        <input
          [(ngModel)]="question"
          name="question"
          placeholder="Ask a question about this dataset..."
          class="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
        />
        <button
          type="submit"
          [disabled]="loading() || !question.trim()"
          class="bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm font-medium px-5 py-2.5 rounded-lg"
        >
          {{ loading() ? "Running..." : "Ask" }}
        </button>
      </form>

      @if (error()) {
        <div class="mb-6 rounded-card bg-status-error-bg text-status-error-text text-sm px-4 py-3">
          {{ error() }}
        </div>
      }

      <div class="flex gap-2 mb-4 border-b border-gray-200">
        @for (t of tabs; track t.value) {
          <button
            (click)="activeTab.set(t.value); onTabChange(t.value)"
            class="text-sm px-3 py-2 border-b-2 transition-colors"
            [class]="activeTab() === t.value ? 'border-accent text-accent font-medium' : 'border-transparent text-gray-500'"
          >
            {{ t.label }}
          </button>
        }
      </div>

      @if (activeTab() === 'results') {
        @if (result(); as r) {
          <div class="bg-white rounded-card shadow-sm border border-gray-100 p-4 mb-4">
            <p class="text-xs text-gray-400 mb-1">Generated SQL</p>
            <code class="text-xs text-gray-700 break-all">{{ r.generated_sql }}</code>
            <p class="text-xs text-gray-400 mt-2">{{ r.row_count }} rows · {{ r.execution_ms }}ms</p>
          </div>

          <div class="flex items-center justify-between mb-3">
            <div class="flex gap-1.5 bg-gray-100 rounded-lg p-1">
              <button
                (click)="resultView.set('table')"
                class="text-xs px-3 py-1 rounded-md transition-colors"
                [class]="resultView() === 'table' ? 'bg-white shadow-sm text-gray-900 font-medium' : 'text-gray-500'"
              >
                Table
              </button>
              <button
                (click)="resultView.set('chart')"
                class="text-xs px-3 py-1 rounded-md transition-colors"
                [class]="resultView() === 'chart' ? 'bg-white shadow-sm text-gray-900 font-medium' : 'text-gray-500'"
              >
                Chart
              </button>
            </div>
            <div class="flex gap-2">
              <button (click)="exportResult('csv')" class="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:border-accent">
                Export CSV
              </button>
              <button (click)="exportResult('xlsx')" class="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:border-accent">
                Export Excel
              </button>
              <button (click)="exportResult('pdf')" class="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:border-accent">
                Export PDF
              </button>
            </div>
          </div>

          @if (resultView() === 'chart') {
            <app-results-chart [columns]="r.columns" [rows]="r.rows"></app-results-chart>
          } @else {
            <div class="bg-white rounded-card shadow-sm border border-gray-100 overflow-x-auto">
              <table class="w-full text-sm">
                <thead class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                  <tr>
                    @for (c of r.columns; track c) {
                      <th class="text-left px-4 py-3 whitespace-nowrap">{{ c }}</th>
                    }
                  </tr>
                </thead>
                <tbody>
                  @for (row of r.rows; track $index) {
                    <tr class="border-t border-gray-50">
                      @for (c of r.columns; track c) {
                        <td class="px-4 py-2.5 whitespace-nowrap text-gray-700">{{ row[c] }}</td>
                      }
                    </tr>
                  }
                </tbody>
              </table>
              @if (r.rows.length === 0) {
                <p class="text-sm text-gray-400 text-center py-8">No rows matched.</p>
              }
            </div>
          }
        } @else {
          <p class="text-sm text-gray-400 text-center py-12">Ask a question to see results here.</p>
        }
      }

      @if (activeTab() === 'history') {
        <div class="space-y-2">
          @for (h of history(); track h.id) {
            <div
              class="bg-white rounded-card p-4 shadow-sm border border-gray-100 cursor-pointer hover:border-accent transition-colors"
              (click)="ask(h.question)"
            >
              <div class="flex items-center justify-between">
                <p class="text-sm text-gray-900">{{ h.question }}</p>
                @if (h.success) {
                  <span class="pill bg-status-success-bg text-status-success-text">{{ h.row_count_returned }} rows</span>
                } @else {
                  <span class="pill bg-status-error-bg text-status-error-text">Failed</span>
                }
              </div>
              <p class="text-xs text-gray-400 mt-1">{{ h.created_at | date: "medium" }} · {{ h.execution_ms }}ms</p>
            </div>
          }
          @if (history().length === 0) {
            <p class="text-sm text-gray-400 text-center py-8">No queries yet.</p>
          }
        </div>
      }

      @if (activeTab() === 'insights') {
        @if (insightsLoading()) {
          <p class="text-sm text-gray-400">Generating insights...</p>
        } @else {
          @if (insights(); as ins) {
            <div class="bg-white rounded-card p-5 shadow-sm border border-gray-100 text-sm text-gray-700 whitespace-pre-wrap">
              {{ ins.insights }}
            </div>
          }
        }
      }
    </div>
    }
  `,
})
export class QueryComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  dataset = signal<Dataset | null>(null);
  result = signal<QueryResult | null>(null);
  resultView = signal<ResultView>("table");
  history = signal<QueryHistoryItem[]>([]);
  insights = signal<InsightsResult | null>(null);
  insightsLoading = signal(false);
  loading = signal(false);
  error = signal<string | null>(null);
  activeTab = signal<Tab>("results");

  question = "";
  sampleQuestions = [
    "Show top 10 by revenue",
    "Find duplicate records",
    "Which month generated the highest sales?",
    "Show records with missing values",
  ];
  tabs: { label: string; value: Tab }[] = [
    { label: "Results", value: "results" },
    { label: "History", value: "history" },
    { label: "AI Insights", value: "insights" },
  ];

  private datasetId = "";

  ngOnInit(): void {
    this.datasetId = this.route.snapshot.paramMap.get("id")!;
    this.api.getDataset(this.datasetId).subscribe((d) => this.dataset.set(d));
    this.loadHistory();
  }

  onTabChange(tab: Tab): void {
    if (tab === "history") this.loadHistory();
    if (tab === "insights" && !this.insights()) this.loadInsights();
  }

  loadHistory(): void {
    this.api.getHistory(this.datasetId).subscribe((h) => this.history.set(h));
  }

  loadInsights(): void {
    this.insightsLoading.set(true);
    this.api.getInsights(this.datasetId).subscribe({
      next: (ins) => {
        this.insights.set(ins);
        this.insightsLoading.set(false);
      },
      error: () => this.insightsLoading.set(false),
    });
  }

  submit(): void {
    if (!this.question.trim()) return;
    this.ask(this.question);
  }

  ask(question: string): void {
    this.question = question;
    this.loading.set(true);
    this.error.set(null);
    this.activeTab.set("results");
    this.resultView.set("table");
    this.api.query(this.datasetId, question).subscribe({
      next: (r) => {
        this.result.set(r);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(e.message);
        this.loading.set(false);
      },
    });
  }

  exportResult(format: "xlsx" | "csv" | "pdf"): void {
    const r = this.result();
    if (!r) return;
    this.api.exportQueryResult(this.datasetId, r.question, format).subscribe((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `query_result.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    });
  }

  columnNamesList(ds: Dataset): string {
    return ds.columns_metadata.map((c) => c.column_name).join(", ");
  }
}