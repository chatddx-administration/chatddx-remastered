import { afterEach, describe, expect, it, vi } from "vitest";
import { watch } from "./events";

class Source extends EventTarget {
  static readonly CLOSED = 2;
  static made: Source[] = [];
  readyState = 0;

  constructor(readonly url: string) {
    super();
    Source.made.push(this);
  }

  close() {
    this.readyState = Source.CLOSED;
  }

  say(name: string, data: unknown) {
    this.dispatchEvent(new MessageEvent(name, { data: JSON.stringify(data) }));
  }
}

afterEach(() => {
  vi.unstubAllGlobals();
  Source.made = [];
});

describe("watching a run", () => {
  it("passes the API's errors on, and lets the source reconnect after a lost connection", async () => {
    vi.stubGlobal("EventSource", Source);
    const told: [string, unknown][] = [];
    const watched = watch("r", (name, data) => told.push([name, data]));
    const [source] = Source.made;
    expect(source?.url).toBe("/api/runs/r/events");

    source?.dispatchEvent(new Event("error"));
    source?.say("error", { detail: "run r failed: boom" });
    source?.say("done", { halted: null });
    await watched;

    expect(told).toEqual([
      ["error", { detail: "run r failed: boom" }],
      ["done", { halted: null }],
    ]);
    expect(source?.readyState).toBe(Source.CLOSED);
  });

  it("gives up once the source has closed", async () => {
    vi.stubGlobal("EventSource", Source);
    const watched = watch("r", () => {});
    const [source] = Source.made;
    source?.close();
    source?.dispatchEvent(new Event("error"));
    await expect(watched).rejects.toThrow("the run's events stopped coming");
  });
});
