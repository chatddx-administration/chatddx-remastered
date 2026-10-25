import { t } from "$lib/locale";

const GROUPS: { name: string; patterns: RegExp[] }[] = [
  {
    name: t("Complete blood count"),
    patterns: [
      /^cbc$/i,
      /^fbc$/i,
      /^hb$/i,
      /hemoglobin/i,
      /haemoglobin/i,
      /wbc/i,
      /platelet/i,
      /leukocyt/i,
      /erythrocyt/i,
      /hematocrit/i,
      /haematocrit/i,
      /^mcv$/i,
      /^mch$/i,
      /diff/i,
    ],
  },
  {
    name: t("Electrolytes"),
    patterns: [
      /sodium/i,
      /potassium/i,
      /calcium/i,
      /magnesium/i,
      /chloride/i,
      /phosphate/i,
      /^na\+?$/i,
      /^k\+?$/i,
      /^ca\+?$/i,
      /^mg\+?$/i,
      /electrolyte/i,
    ],
  },
  { name: t("Renal function"), patterns: [/creatinine/i, /urea/i, /bun/i, /egfr/i, /cystatin/i] },
  {
    name: t("Liver function"),
    patterns: [/^alt$/i, /^ast$/i, /^alp$/i, /^ggt$/i, /bilirubin/i, /^ldh$/i, /albumin/i, /\blft\b/i, /liver/i],
  },
  { name: t("Inflammatory markers"), patterns: [/^crp$/i, /procalcitonin/i, /^pct$/i, /^esr$/i, /sed.*rate/i] },
  {
    name: t("Coagulation"),
    patterns: [/^pt$/i, /^inr$/i, /^aptt$/i, /^ptt$/i, /fibrinogen/i, /d-dimer/i, /coagulat/i],
  },
  {
    name: t("Cardiac markers"),
    patterns: [/troponin/i, /^tnt$/i, /^tni$/i, /^bnp$/i, /nt-probnp/i, /ck-mb/i, /myoglobin/i],
  },
  { name: t("Glucose/Metabolism"), patterns: [/glucose/i, /hba1c/i, /lactate/i, /blood sugar/i] },
  {
    name: t("Blood gas"),
    patterns: [/blood gas/i, /\babg\b/i, /\bvbg\b/i, /^ph$/i, /pco2/i, /po2/i, /\bbe\b/i, /bicarbonate/i],
  },
  { name: t("Thyroid"), patterns: [/^tsh$/i, /^t3$/i, /^t4$/i, /free.*t4/i, /thyroid/i] },
];

export function groupLabs(investigations: string[]): { grouped: [string, string[]][]; ungrouped: string[] } {
  const grouped = new Map<string, string[]>();
  const ungrouped: string[] = [];
  for (const item of investigations) {
    const group = GROUPS.find((g) => g.patterns.some((p) => p.test(item)));
    if (group) grouped.set(group.name, [...(grouped.get(group.name) ?? []), item]);
    else ungrouped.push(item);
  }
  return { grouped: [...grouped], ungrouped };
}
