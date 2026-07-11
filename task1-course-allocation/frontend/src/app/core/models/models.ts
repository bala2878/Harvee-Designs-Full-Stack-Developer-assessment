export type Category = "GENERAL" | "OBC" | "SC" | "ST";
export type AllocationStatus = "ALLOCATED" | "NOT_ALLOCATED";
export type AllocationRunStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface PreferenceIn {
  course_id: string;
  priority: number;
}

export interface Student {
  id: string;
  student_code: string;
  name: string;
  email: string;
  marks: number;
  category: Category;
  application_date: string;
  created_at: string;
}

export interface StudentDetail extends Student {
  preferences: PreferenceIn[];
  allocated_course_name: string | null;
  allocation_status: AllocationStatus | null;
}

export interface StudentCreate {
  name: string;
  email: string;
  marks: number;
  category: Category;
  application_date?: string;
  preferences: PreferenceIn[];
}

export interface SeatReservation {
  category: Category;
  reserved_seats: number;
}

export interface Course {
  id: string;
  name: string;
  code: string;
  total_seats: number;
  created_at: string;
}

export interface CourseStats extends Course {
  seats_filled: number;
  seats_available: number;
  category_wise_allocations: Record<string, number>;
  rejection_rate_percent: number;
}

export interface CourseCreate {
  name: string;
  code: string;
  total_seats: number;
  reservations: SeatReservation[];
}

export interface AllocationRow {
  student_id: string;
  student_name: string;
  student_code: string;
  category: Category;
  course_id: string | null;
  course_name: string | null;
  status: AllocationStatus;
  preference_rank_matched: number | null;
  reason: string | null;
}

export interface AllocationRun {
  id: string;
  status: AllocationRunStatus;
  total_students: number;
  total_allocated: number;
  total_unallocated: number;
  triggered_by: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface DashboardSummary {
  total_students: number;
  total_courses: number;
  total_seats: number;
  total_allocated: number;
  total_unallocated: number;
  overall_fill_rate_percent: number;
  category_wise_allocation: Record<string, number>;
  first_preference_match_rate_percent: number;
  latest_run: AllocationRun | null;
}

export interface AiToolCall {
  tool: string;
  input: Record<string, unknown>;
  result: unknown;
}

export interface AiAskResponse {
  answer: string;
  tool_calls: AiToolCall[];
}
