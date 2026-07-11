import { Component } from "@angular/core";
import { ShellComponent } from "./shared/layout/shell.component";

@Component({
  selector: "app-root",
  standalone: true,
  imports: [ShellComponent],
  template: `<app-shell></app-shell>`,
})
export class AppComponent {}
