import { HttpClient } from "@angular/common/http";
import { Injectable, inject } from "@angular/core";
import { Observable } from "rxjs";

import { environment } from "../../../environments/environment";
import {
  AiAskResponse,
  AllocationRow,
  AllocationRun,
  Course,
  CourseCreate,
  CourseStats,
  DashboardSummary,
  Student,
  StudentCreate,
  StudentDetail,
} from "../models/models";

@Injectable({ providedIn: "root" })
export class ApiService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;

  // --- Students ---
  listStudents(category?: string): Observable<Student[]> {
    const params: Record<string, string> = {};
    if (category) params["category"] = category;
    return this.http.get<Student[]>(`${this.base}/students`, { params });
  }
  getStudent(id: string): Observable<StudentDetail> {
    return this.http.get<StudentDetail>(`${this.base}/students/${id}`);
  }
  createStudent(payload: StudentCreate): Observable<StudentDetail> {
    return this.http.post<StudentDetail>(`${this.base}/students`, payload);
  }
  deleteStudent(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/students/${id}`);
  }

  // --- Courses ---
  listCourses(): Observable<Course[]> {
    return this.http.get<Course[]>(`${this.base}/courses`);
  }
  getCourseStats(id: string): Observable<CourseStats> {
    return this.http.get<CourseStats>(`${this.base}/courses/${id}/stats`);
  }
  createCourse(payload: CourseCreate): Observable<Course> {
    return this.http.post<Course>(`${this.base}/courses`, payload);
  }
  deleteCourse(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/courses/${id}`);
  }

  // --- Allocation ---
  runAllocation(): Observable<AllocationRun> {
    return this.http.post<AllocationRun>(`${this.base}/allocation/run`, {});
  }
  getAllocationResults(status?: string): Observable<AllocationRow[]> {
    const params: Record<string, string> = {};
    if (status) params["status"] = status;
    return this.http.get<AllocationRow[]>(`${this.base}/allocation/results`, { params });
  }
  listAllocationRuns(): Observable<AllocationRun[]> {
    return this.http.get<AllocationRun[]>(`${this.base}/allocation/runs`);
  }

  // --- Dashboard ---
  getDashboardSummary(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(`${this.base}/dashboard/summary`);
  }

  // --- AI Assistant ---
  askAssistant(question: string): Observable<AiAskResponse> {
    return this.http.post<AiAskResponse>(`${this.base}/ai-assistant/ask`, { question });
  }
}
