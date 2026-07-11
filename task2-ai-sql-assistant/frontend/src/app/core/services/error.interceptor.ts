import { HttpErrorResponse, HttpInterceptorFn } from "@angular/common/http";
import { catchError, throwError } from "rxjs";

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      const detail = error.error?.detail;
const message = Array.isArray(detail)
  ? detail.map((d: any) => d.msg).join(", ")
  : detail ?? error.message ?? "Unexpected error";
      console.error(`[API error] ${req.method} ${req.url} -> ${error.status}: ${message}`);
      return throwError(() => new Error(message));
    })
  );
};
