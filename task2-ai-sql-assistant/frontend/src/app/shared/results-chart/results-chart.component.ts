import { Component, ElementRef, Input, OnChanges, OnDestroy, SimpleChanges, ViewChild } from "@angular/core";
import { Chart, ChartConfiguration } from "chart.js/auto";

@Component({
  selector: "app-results-chart",
  standalone: true,
  template: `
    @if (canRenderChart) {
      <div
        class="bg-white rounded-card shadow-sm border border-gray-100 p-4"
        style="height: 340px; position: relative; width: 100%;"
      >
        <canvas #canvas></canvas>
      </div>
    } @else {
      <div class="bg-white rounded-card shadow-sm border border-gray-100 p-8 text-center text-sm text-gray-400">
        This result isn't chartable — charting needs one text/category column and one numeric column,
        with 50 rows or fewer.
      </div>
    }
  `,
})
export class ResultsChartComponent implements OnChanges, OnDestroy {
  @Input() columns: string[] = [];
  @Input() rows: Record<string, unknown>[] = [];
  @ViewChild("canvas") canvasRef?: ElementRef<HTMLCanvasElement>;

  private chartInstance?: Chart;
  canRenderChart = false;
  private labelColumn: string | null = null;
  private valueColumn: string | null = null;

  ngOnChanges(_changes: SimpleChanges): void {
    this.detectColumns();
     requestAnimationFrame(() => requestAnimationFrame(() => this.renderChart()));
  }

  ngOnDestroy(): void {
    this.chartInstance?.destroy();
  }

  private isNumericValue(v: unknown): boolean {
    if (typeof v === "number") return Number.isFinite(v);
    if (typeof v === "string" && v.trim() !== "") return !Number.isNaN(Number(v));
    return false;
  }

  private looksLikeIdColumn(name: string): boolean {
    const n = name.toLowerCase();
    return n === "id" || n.endsWith("_id") || n.endsWith("id");
  }

  private metricScore(name: string): number {
    const n = name.toLowerCase();

    const priority = [
      "revenue", "total", "amount", "sum", "sales", "value",
      "score", "marks", "average", "avg", "rate", "count", "price",
    ];
    const idx = priority.findIndex((kw) => n.includes(kw));
    if (idx !== -1) return 1000 - idx;
    if (!this.looksLikeIdColumn(n)) return 1;
    return 0; 
  }

  private detectColumns(): void {
    this.labelColumn = null;
    this.valueColumn = null;

    if (!this.rows.length || !this.columns.length) {
      this.canRenderChart = false;
      return;
    }

    const sample = this.rows[0];
    const numericColumns: string[] = [];
    const textColumns: string[] = [];

    for (const col of this.columns) {
      if (this.isNumericValue(sample[col])) {
        numericColumns.push(col);
      } else {
        textColumns.push(col);
      }
    }
    this.valueColumn =
      [...numericColumns].sort((a, b) => this.metricScore(b) - this.metricScore(a))[0] ?? null;
    this.labelColumn = textColumns[0] ?? null;

    this.canRenderChart = !!this.labelColumn && !!this.valueColumn && this.rows.length <= 50;
  }

  private renderChart(): void {
    this.chartInstance?.destroy();
    if (!this.canRenderChart || !this.canvasRef || !this.labelColumn || !this.valueColumn) return;

    const labelCol = this.labelColumn;
    const valueCol = this.valueColumn;
    const labels = this.rows.map((r) => String(r[labelCol] ?? ""));
    const data = this.rows.map((r) => Number(r[valueCol] ?? 0));

    const config: ChartConfiguration = {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: valueCol,
            data,
            backgroundColor: "#6366F1",
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    };

    this.chartInstance = new Chart(this.canvasRef.nativeElement, config);
  }
}