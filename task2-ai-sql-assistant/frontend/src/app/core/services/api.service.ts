import { HttpClient } from "@angular/common/http";
import { Injectable, inject } from "@angular/core";
import { Observable } from "rxjs";

import { environment } from "../../../environments/environment";
import { Dataset, InsightsResult, QueryHistoryItem, QueryResult } from "../models/models";

@Injectable({ providedIn: "root" })
export class ApiService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;

  uploadDataset(file: File): Observable<Dataset> {
    const formData = new FormData();
    formData.append("file", file);
    return this.http.post<Dataset>(`${this.base}/datasets/upload`, formData);
  }

  listDatasets(): Observable<Dataset[]> {
    return this.http.get<Dataset[]>(`${this.base}/datasets`);
  }

  getDataset(id: string): Observable<Dataset> {
    return this.http.get<Dataset>(`${this.base}/datasets/${id}`);
  }

  deleteDataset(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/datasets/${id}`);
  }

  query(datasetId: string, question: string): Observable<QueryResult> {
    return this.http.post<QueryResult>(`${this.base}/datasets/${datasetId}/query`, { question });
  }

  getHistory(datasetId: string): Observable<QueryHistoryItem[]> {
    return this.http.get<QueryHistoryItem[]>(`${this.base}/datasets/${datasetId}/history`);
  }

  getInsights(datasetId: string): Observable<InsightsResult> {
    return this.http.get<InsightsResult>(`${this.base}/datasets/${datasetId}/insights`);
  }

  exportUrl(datasetId: string, question: string, format: "xlsx" | "csv" | "pdf"): string {
    return `${this.base}/datasets/${datasetId}/export?format=${format}`;
  }

  exportQueryResult(datasetId: string, question: string, format: "xlsx" | "csv" | "pdf"): Observable<Blob> {
    return this.http.post(this.exportUrl(datasetId, question, format), { question }, { responseType: "blob" });
  }
}
