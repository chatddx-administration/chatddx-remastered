import type { Schemas } from "$lib/api/client";
import { worded } from "$lib/kinds";
import { displayLanguage, displayList, t, tn, tp } from "$lib/locale";

// Dependency: a case's title as src/chatddx/portal/titles.py:display_case says it.
export function caseTitle(titled: Schemas["CaseTitle"], brief = false): string {
  const n = titled.appendices.length;
  const said =
    n === 0
      ? titled.name
      : brief
        ? tn("%(case)s + %(num)s appendix", "%(case)s + %(num)s appendices", n, { case: titled.name, num: n })
        : t("%(case)s with %(appendices)s", { case: titled.name, appendices: displayList(titled.appendices) });
  return titled.earlier ? t("%(case)s (earlier)", { case: said }) : said;
}

// Dependency: a run's title as the portal's macros.html:run_title says it.
export function runTitle(titled: Schemas["Titled"]): string {
  const replaced = titled.replaced.map((r) =>
    r.title === null
      ? tp("a part replaced", "no %(part)s", { part: worded(r.part) })
      : tp("a part replaced", "%(part)s: %(title)s", { part: worded(r.part), title: r.title }),
  );
  const configuration = `\`${titled.name}\`` + (replaced.length ? ` (${replaced.join(", ")})` : "");
  const language = titled.translated ? displayLanguage(titled.translated) : null;
  const cases = titled.case
    ? language === null
      ? caseTitle(titled.case, true)
      : t("%(case)s in %(language)s", { case: caseTitle(titled.case, true), language })
    : language === null
      ? tn("%(num)s case", "%(num)s cases", titled.cases, { num: titled.cases })
      : tn("%(num)s %(language)s case", "%(num)s %(language)s cases", titled.cases, { num: titled.cases, language });
  const n = titled.seeds.length;
  const seeds = titled.greedy
    ? n === 1
      ? tp("sampling", "greedy")
      : tn("greedy, %(num)s replicate", "greedy, %(num)s replicates", n, { num: n })
    : tn("seed %(seeds)s", "seeds %(seeds)s", n, { seeds: titled.seeds.join(", ") });
  return t("%(cases)s with %(configuration)s on %(model)s (%(seeds)s)", {
    cases,
    configuration,
    model: titled.at,
    seeds,
  });
}
