import { CommonModule } from "@angular/common";
import { Component, inject, signal } from "@angular/core";
import { FormsModule } from "@angular/forms";

import { ApiService } from "../../core/services/api.service";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  toolCalls?: { tool: string }[];
}

@Component({
  selector: "app-ai-chat",
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-8 max-w-3xl mx-auto flex flex-col h-full">
      <div class="mb-6">
        <h1 class="text-2xl font-semibold text-gray-900">AI Assistant</h1>
        <p class="text-sm text-gray-500 mt-1">
          Ask questions about allocation results — answers are grounded in live database queries, not guesses.
        </p>
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

      <div class="flex-1 bg-white rounded-card shadow-sm border border-gray-100 p-5 overflow-y-auto space-y-4 mb-4">
        @for (m of messages(); track $index) {
          <div [class]="m.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
            <div
              class="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap"
              [class]="m.role === 'user' ? 'bg-accent text-white' : 'bg-gray-100 text-gray-800'"
            >
              {{ m.text }}
              @if (m.toolCalls?.length) {
                <div class="mt-2 pt-2 border-t border-black/10 text-[11px] opacity-70">
                  Tools used: {{ toolNames(m.toolCalls) }}
                </div>
              }
            </div>
          </div>
        }
        @if (loading()) {
          <p class="text-xs text-gray-400">Thinking...</p>
        }
        @if (messages().length === 0 && !loading()) {
          <p class="text-sm text-gray-400 text-center py-8">
            Try one of the sample questions above, or ask your own.
          </p>
        }
      </div>

      <form (ngSubmit)="submit()" class="flex gap-2">
        <input
          [(ngModel)]="question"
          name="question"
          placeholder="Ask about allocation results..."
          class="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
        />
        <button
          type="submit"
          [disabled]="loading() || !question.trim()"
          class="bg-accent hover:bg-accent-hover disabled:opacity-50 text-white text-sm font-medium px-5 py-2.5 rounded-lg"
        >
          Ask
        </button>
      </form>
    </div>
  `,
})
export class AiChatComponent {
  private api = inject(ApiService);

  question = "";
  loading = signal(false);
  messages = signal<ChatMessage[]>([]);

  sampleQuestions = [
    "How many students were allocated to each course?",
    "Which students did not receive their first preference?",
    "Which course had the highest rejection rate?",
    "Show category-wise allocation summary.",
  ];

  submit(): void {
    if (!this.question.trim()) return;
    this.ask(this.question);
    this.question = "";
  }

  ask(question: string): void {
    this.messages.update((m) => [...m, { role: "user", text: question }]);
    this.loading.set(true);
    this.api.askAssistant(question).subscribe({
      next: (res) => {
        this.loading.set(false);
        this.messages.update((m) => [...m, { role: "assistant", text: res.answer, toolCalls: res.tool_calls }]);
      },
      error: (e) => {
        this.loading.set(false);
        this.messages.update((m) => [...m, { role: "assistant", text: `Error: ${e.message}` }]);
      },
    });
  }

  toolNames(calls?: { tool: string }[]): string {
    return (calls ?? []).map((c) => c.tool).join(", ");
  }
}
