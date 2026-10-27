import { describe, expect, it } from "vitest";
import { Edited, type Part, type Wrote } from "./edited.svelte";

function part(rank: number, said: Wrote[], wrote: number[], ready = true): Part & { left: Wrote[] } {
  const made = {
    rank,
    left: [...said],
    pending: () => made.left.length > 0,
    ready: () => ready,
    save: async (): Promise<Wrote> => {
      wrote.push(rank);
      const got = made.left[0] ?? {};
      if (!("problem" in got)) made.left.shift();
      return got;
    },
  };
  return made;
}

describe("Edited", () => {
  it("saves what is pending by rank and shows the case the parts moved to", async () => {
    const shown: string[] = [];
    const wrote: number[] = [];
    const edited = new Edited("c1", (to) => shown.push(to));
    edited.join(part(2, [{ case: "c2" }], wrote));
    edited.join(part(0, [{}], wrote));
    edited.join(part(1, [], wrote));
    expect([edited.pending, edited.ready]).toEqual([true, true]);
    await edited.save("/review/1?tag=a&case=c1");
    expect(wrote).toEqual([0, 2]);
    expect(shown).toEqual(["/review/1?tag=a&case=c2"]);
  });

  it("stays on the case when no part moves it", async () => {
    const shown: string[] = [];
    const edited = new Edited("c1", (to) => shown.push(to));
    edited.join(part(0, [{}], []));
    await edited.save("/review/1");
    expect(shown).toEqual(["/review/1"]);
  });

  it("stops at the first refused, and saving again writes what is left", async () => {
    const shown: string[] = [];
    const wrote: number[] = [];
    const edited = new Edited("c1", (to) => shown.push(to));
    const refusing = part(1, [{ problem: "moved on" }], wrote);
    edited.join(part(0, [{ case: "c2" }], wrote));
    edited.join(refusing);
    edited.join(part(2, [{}], wrote));
    await edited.save("/review/1");
    expect([edited.problem, edited.busy, shown, wrote]).toEqual(["moved on", false, [], [0, 1]]);
    refusing.left = [{}];
    await edited.save("/review/1");
    expect([edited.problem, wrote]).toEqual([null, [0, 1, 1, 2]]);
    expect(shown).toEqual(["/review/1?case=c2"]);
  });

  it("can be restored while a part holds something unsaved or has a form open", () => {
    const edited = new Edited("c1", () => undefined);
    let open = false;
    edited.join({ ...part(0, [], []), opened: () => open });
    expect([edited.pending, edited.restorable]).toEqual([false, false]);
    open = true;
    expect([edited.pending, edited.restorable]).toEqual([false, true]);
    edited.join(part(1, [{}], []));
    open = false;
    expect([edited.pending, edited.restorable]).toEqual([true, true]);
  });

  it("isn't ready while a pending part isn't, whatever the parts with nothing to save", () => {
    const edited = new Edited("c1", () => undefined);
    edited.join(part(0, [], [], false));
    expect([edited.pending, edited.ready]).toEqual([false, true]);
    edited.join(part(1, [{}], [], false));
    expect([edited.pending, edited.ready]).toEqual([true, false]);
  });
});
