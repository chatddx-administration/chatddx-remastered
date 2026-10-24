import type { Schemas } from "$lib/api/client";
import { worded } from "$lib/kinds";
import { languageName, t, tn, tp } from "$lib/locale";

// Dependency: a run's title as the portal's macros.html:run_title says it.
export function runTitle(titled: Schemas["Titled"]): string {
  const replaced = titled.replaced.map((r) =>
    r.title === null
      ? tp("a part replaced", "no %(part)s", { part: worded(r.part) })
      : tp("a part replaced", "%(part)s: %(title)s", { part: worded(r.part), title: r.title }),
  );
  const n = titled.seeds.length;
  const seeds = titled.greedy
    ? n === 1
      ? tp("sampling", "greedy")
      : tn("greedy, %(num)s replicate", "greedy, %(num)s replicates", n, { num: n })
    : tn("seed %(seeds)s", "seeds %(seeds)s", n, { seeds: titled.seeds.join(", ") });
  return [
    [titled.name, ...replaced].join(", "),
    titled.at,
    titled.case ?? tn("%(num)s case", "%(num)s cases", titled.cases, { num: titled.cases }),
    ...(titled.translated ? [t("translated into %(language)s", { language: languageName(titled.translated) })] : []),
    seeds,
  ].join(" · ");
}
