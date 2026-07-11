export interface ColumnMetadata {
  original_name: string;
  column_name: string;
  data_type: string;
}

export interface Dataset {
  id: string;
  name: string;
  original_filename: string;
  file_type: string;
  row_count: number;
  columns_metadata: ColumnMetadata[];
  created_at: string;
}

export interface QueryResult {
  question: string;
  generated_sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  execution_ms: number;
}

export interface QueryHistoryItem {
  id: string;
  question: string;
  generated_sql: string;
  row_count_returned: number | null;
  success: boolean;
  error_message: string | null;
  execution_ms: number | null;
  created_at: string;
}

export interface InsightsResult {
  dataset_id: string;
  insights: string;
}
