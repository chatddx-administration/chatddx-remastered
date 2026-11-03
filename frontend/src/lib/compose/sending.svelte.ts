import type { Schemas } from "$lib/api/client";

export type Asked = Schemas["Preview"];

export class Sending {
  open = $state(false);
  language = $state<string | null>(null);
  current: () => Asked = () => ({});
  private readonly moved: (open: boolean) => void;

  constructor(moved: (open: boolean) => void) {
    this.moved = moved;
  }

  show(): void {
    if (!this.open) {
      this.open = true;
      this.moved(true);
    }
  }

  close(): void {
    if (this.open) {
      this.open = false;
      this.moved(false);
    }
  }
}
