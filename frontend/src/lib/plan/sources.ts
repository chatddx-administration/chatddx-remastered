const SITES: Record<string, string> = {
  uptodate: "https://www.uptodate.com",
  "bmj best practice": "https://bestpractice.bmj.com",
  bmj: "https://www.bmj.com",
  nice: "https://www.nice.org.uk",
  "nice guidelines": "https://www.nice.org.uk/guidance",
  cdc: "https://www.cdc.gov",
  who: "https://www.who.int",
  medscape: "https://www.medscape.com",
  pubmed: "https://pubmed.ncbi.nlm.nih.gov",
  cochrane: "https://www.cochranelibrary.com",
  lancet: "https://www.thelancet.com",
  nejm: "https://www.nejm.org",
  ahrq: "https://www.ahrq.gov",
  acep: "https://www.acep.org",
  esc: "https://www.escardio.org",
  aha: "https://www.heart.org",
  ers: "https://www.ersnet.org",
  ats: "https://www.thoracic.org",
};

export function siteOf(source: string): string | null {
  if (/^https?:\/\//.test(source)) return source;
  const named = source.toLowerCase().trim();
  if (!named) return null;
  const found = Object.entries(SITES).find(([key]) => named.includes(key) || key.includes(named));
  return found ? found[1] : null;
}
