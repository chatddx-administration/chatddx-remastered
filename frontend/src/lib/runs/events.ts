export const EVENTS = [
  "run.started",
  "item.started",
  "item.delta",
  "item.tool",
  "item.ended",
  "canary.ended",
  "run.noted",
  "run.finished",
  "run.scoring",
  "score.started",
  "judge.asked",
  "judge.delta",
  "judge.answered",
  "score.item",
  "score.noted",
  "run.scored",
  "error",
  "done",
] as const;

export type Event = (typeof EVENTS)[number];

export function watch(run: string, on: (name: Event, data: unknown) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    const events = new EventSource(`/api/runs/${run}/events`);
    for (const name of EVENTS) {
      events.addEventListener(name, (e) => {
        // A lost connection is an "error" too, one without data.
        if (!(e instanceof MessageEvent)) return;
        on(name, JSON.parse((e as MessageEvent<string>).data));
        if (name === "done") {
          events.close();
          resolve();
        }
      });
    }
    events.addEventListener("error", (e) => {
      if (e instanceof MessageEvent || events.readyState !== EventSource.CLOSED) return;
      reject(new Error("the run's events stopped coming"));
    });
  });
}
