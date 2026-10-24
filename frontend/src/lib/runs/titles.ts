import type { Schemas } from "$lib/api/client";
import { worded } from "$lib/kinds";
import { languageName, listed, t, tn, tp } from "$lib/locale";

// Dependency: a case's title as src/chatddx/portal/titles.py:said_case says it.
export function caseTitle(titled: Schemas["CaseTitle"], brief = false): string {
  const n = titled.appendices.length;
  const said =
    n === 0
      ? titled.name
      : brief
        ? tn("%(case)s + %(num)s appendix", "%(case)s + %(num)s appendices", n, { case: titled.name, num: n })
        : t("%(case)s with %(appendices)s", { case: titled.name, appendices: listed(titled.appendices) });
  return titled.earlier ? t("%(case)s (earlier)", { case: said }) : said;
}

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
    titled.case ? caseTitle(titled.case, true) : tn("%(num)s case", "%(num)s cases", titled.cases, { num: titled.cases }),
    ...(titled.translated ? [t("translated into %(language)s", { language: languageName(titled.translated) })] : []),
    seeds,
  ].join(" · ");
}
