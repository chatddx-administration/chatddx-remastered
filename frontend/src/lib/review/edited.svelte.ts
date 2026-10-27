import { replaced } from "./review";

export type Wrote = { problem: string } | { case?: string };

export type Part = {
  rank: number;
  pending: () => boolean;
  opened?: () => boolean;
  ready: () => boolean;
  save: () => Promise<Wrote>;
};

// Policy: the page's Save writes each part that holds something unsaved, by rank, and stops at
// the first refused; what was written stays written, so saving again writes what is left.
export class Edited {
  #parts = $state<Part[]>([]);
  #start: string;
  #at: string;
  #shown: (to: string) => void;
  busy = $state(false);
  problem = $state<string | null>(null);

  constructor(start: string, shown: (to: string) => void) {
    this.#start = start;
    this.#at = start;
    this.#shown = shown;
  }

  join(part: Part): void {
    this.#parts = [...this.#parts, part].sort((a, b) => a.rank - b.rank);
  }

  get pending(): boolean {
    return this.#parts.some((part) => part.pending());
  }

  get restorable(): boolean {
    return this.#parts.some((part) => part.pending() || part.opened?.());
  }

  get ready(): boolean {
    return this.#parts.every((part) => !part.pending() || part.ready());
  }

  async save(back: string): Promise<void> {
    if (this.busy) return;
    this.busy = true;
    this.problem = null;
    for (const part of this.#parts) {
      if (!part.pending()) continue;
      const got = await part.save();
      if ("problem" in got) {
        this.problem = got.problem;
        this.busy = false;
        return;
      }
      if (got.case) this.#at = got.case;
    }
    this.#shown(this.#at === this.#start ? back : replaced(back, this.#start, { [this.#start]: this.#at }));
  }
}
