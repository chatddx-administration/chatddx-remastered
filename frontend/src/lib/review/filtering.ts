export type Picked = { tags: string[]; languages: string[] };

export function shown(tags: string[], language: string, picked: Picked): boolean {
  return (
    picked.tags.every((tag) => tags.includes(tag)) && (!picked.languages.length || picked.languages.includes(language))
  );
}

export function flipped(held: string[], value: string): string[] {
  return held.includes(value) ? held.filter((h) => h !== value) : [...held, value];
}

export function pickedIn(search: string): Picked {
  const query = new URLSearchParams(search);
  return { tags: query.getAll("tag"), languages: query.getAll("language") };
}

export function kept(href: string, picked: Picked): string {
  const url = new URL(href, "https://review.invalid");
  url.searchParams.delete("tag");
  url.searchParams.delete("language");
  for (const tag of picked.tags) url.searchParams.append("tag", tag);
  for (const language of picked.languages) url.searchParams.append("language", language);
  return url.pathname + url.search + url.hash;
}
