<script lang="ts">
  import { onMount } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { api, type Schemas, why } from "$lib/api/client";
  import { t, tn, tp } from "$lib/locale";
  import { fieldName } from "$lib/schema/form";
  import { differs, estimated, grouped, languages, mean, named, spread } from "./breakdown";

  let { thread, version, running }: { thread: number; version: number; running: boolean } = $props();

  type Broken = Schemas["Broken"];
  type Point = Schemas["BrokenPoint"];

  let got = $state<Broken | null>(null);
  let problem = $state<string | null>(null);
  let width = $state(0);
  let held: HTMLElement;

  // Policy: read once the section is near view, as most visits to a configuration write it rather than weigh it.
  onMount(() => {
    const seen = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        seen.disconnect();
        void read();
      },
      { rootMargin: "200px" },
    );
    seen.observe(held);
    return () => seen.disconnect();
  });

  // Policy: read again so long after while its baseline is under way, as Review's faring does.
  const AGAIN = 10_000;

  async function read(): Promise<void> {
    const res = await api.GET("/api/threads/{thread}/breakdown", { params: { path: { thread } } });
    if (!res.data) {
      problem = why(res.error);
      return;
    }
    got = res.data;
    if (running) setTimeout(() => void read(), AGAIN);
  }

  const HIGH = 150;
  const LEFT = 28;
  const RIGHT = 8;
  const TOP = 8;
  const BOTTOM = 20;
  const y = (value: number): number => TOP + (1 - Math.min(1, Math.max(0, value))) * (HIGH - TOP - BOTTOM);
  const columns = $derived(got?.versions.length ?? 0);
  const step = $derived(columns ? Math.max(0, width - LEFT - RIGHT) / columns : 0);
  const x = (column: number): number => LEFT + (column + 0.5) * step;
  const groups = $derived(got === null ? [] : grouped(got));
  const latest = $derived(
    got === null
      ? null
      : got.versions
          .flatMap((v) => v.points)
          .reduce<Point | null>((a, p) => (a === null || Date.parse(p.at) > Date.parse(a.at) ? p : a), null),
  );
  const stale = $derived(got?.versions.some((v) => v.points.some((p) => p.stale)) ?? false);

  const STRIP = 22;
  const along = (value: number, wide: number): number => 6 + Math.min(1, Math.max(0, value)) * Math.max(0, wide - 12);
  let stripWidth = $state(0);

  function gathered(p: Point, view: number): string {
    const value = p.means[view];
    const said = `v${p.version} · ${new Date(p.at).toLocaleDateString()} · ${value == null ? "—" : value.toFixed(2)}`;
    return p.stale ? `${said} · ${t("not as things are now")}` : said;
  }
</script>

<div bind:this={held}>
  <header class="mb-4 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-2">
    <div class="flex flex-wrap items-baseline gap-x-2">
      <h2>{t("Baseline")}</h2>
      {#if got}
        <span class="inline-flex rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">{got.tag}</span>
        <span class="text-sm text-muted-foreground"
          >{tn("%(num)s case", "%(num)s cases", got.cases, { num: got.cases })}</span
        >
      {/if}
    </div>
    <ul class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground" aria-label={t("Legend")}>
      <li class="flex items-center gap-1.5">
        <svg width="14" height="14" aria-hidden="true"
          ><line x1="7" x2="7" y1="1" y2="13" class="stroke-primary" stroke-width="2" /><circle
            cx="7"
            cy="7"
            r="4"
            class="fill-primary stroke-card"
            stroke-width="2"
          /></svg
        >
        {t("Mean")} ±95%
      </li>
      <li class="flex items-center gap-1.5">
        <svg width="14" height="14" aria-hidden="true"
          ><circle cx="7" cy="7" r="3" class="fill-muted-foreground/60" /></svg
        >
        {t("Runs")}
      </li>
      {#if stale}
        <li class="flex items-center gap-1.5">
          <svg width="14" height="14" aria-hidden="true"
            ><circle cx="7" cy="7" r="3.5" class="fill-muted-foreground/60 stroke-warning" stroke-width="1.5" /></svg
          >
          {t("not as things are now")}
        </li>
      {/if}
    </ul>
  </header>

  {#if problem}
    <p role="alert" class="text-sm text-destructive">{problem}</p>
  {:else if got === null}
    <p role="status" aria-busy="true" class="text-muted-foreground">
      <LoaderCircleIcon class="size-4 animate-spin" />
    </p>
  {:else if !got.versions.length}
    <p class="text-sm text-muted-foreground">{t("None.")}</p>
  {:else}
    <div class="space-y-8">
      {#each groups as group (group.field)}
        <section aria-label={group.field === null ? t("The whole answer") : fieldName(group.field)}>
          <h3 class="mb-3 text-sm font-semibold">
            {group.field === null ? t("The whole answer") : fieldName(group.field)}
          </h3>
          <div class="space-y-6">
            {#each group.views as view (view)}
              {@const peers = got.peers.filter((p) => p.means[view] !== null && p.means[view] !== undefined)}
              <figure>
                <figcaption class="mb-1 text-xs text-muted-foreground">{got.views[view]?.label}</figcaption>
                <div class="grid gap-x-8 gap-y-4 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
                  <div bind:clientWidth={width}>
                    <svg
                      class="block w-full"
                      height={HIGH}
                      role="img"
                      aria-label={got.versions.map((v) => estimated(v, view)).join(". ")}
                    >
                      {#each [0, 0.5, 1] as tick (tick)}
                        <line
                          x1={LEFT}
                          x2={width - RIGHT}
                          y1={y(tick) + 0.5}
                          y2={y(tick) + 0.5}
                          class="stroke-border"
                          stroke-width="1"
                          stroke-dasharray={tick === 0.5 ? "2 3" : undefined}
                        />
                        <text
                          x={LEFT - 6}
                          y={y(tick) + 3.5}
                          text-anchor="end"
                          class="fill-muted-foreground text-[0.7rem] tabular-nums">{tick}</text
                        >
                      {/each}
                      {#each got.versions as v, column (v.digest)}
                        {#if v.versions.includes(version)}
                          <rect
                            x={x(column) - step / 2 + 2}
                            y={TOP - 4}
                            width={Math.max(0, step - 4)}
                            height={HIGH - TOP - BOTTOM + 8}
                            rx="4"
                            class="fill-muted/60"
                          />
                        {/if}
                      {/each}
                      {#each got.versions as v, column (v.digest)}
                        {@const before = column > 0 ? got.versions[column - 1]?.estimates[view] : null}
                        {@const now = v.estimates[view]}
                        {#if before && now}
                          <line
                            x1={x(column - 1)}
                            x2={x(column)}
                            y1={y(before.mean)}
                            y2={y(now.mean)}
                            class="stroke-primary/40"
                            stroke-width="1.5"
                          />
                        {/if}
                      {/each}
                      {#each got.versions as v, column (v.digest)}
                        {@const e = v.estimates[view]}
                        {@const offsets = spread(v.points)}
                        <g>
                          <title>{estimated(v, view)}</title>
                          <rect
                            x={x(column) - step / 2}
                            y="0"
                            width={step}
                            height={HIGH - BOTTOM}
                            class="fill-transparent"
                          />
                          {#each v.points as p, i (p.started)}
                            {@const value = p.means[view]}
                            {#if value !== null && value !== undefined}
                              <a href={`/runs/${p.started}`}>
                                <title>{gathered(p, view)}</title>
                                <circle
                                  cx={x(column) + (offsets[i] ?? 0) * step * 0.5}
                                  cy={y(value)}
                                  r="3"
                                  class={p.stale
                                    ? "fill-muted-foreground/60 stroke-warning hover:fill-muted-foreground"
                                    : "fill-muted-foreground/60 hover:fill-muted-foreground"}
                                  stroke-width={p.stale ? 1.5 : 0}
                                />
                              </a>
                            {/if}
                          {/each}
                          {#if e}
                            {#if e.half !== null}
                              <line
                                x1={x(column)}
                                x2={x(column)}
                                y1={y(e.mean - e.half)}
                                y2={y(e.mean + e.half)}
                                class="stroke-primary"
                                stroke-width="2"
                                stroke-linecap="round"
                              />
                            {/if}
                            <circle
                              cx={x(column)}
                              cy={y(e.mean)}
                              r="5"
                              class="fill-primary stroke-card"
                              stroke-width="2"
                            />
                          {/if}
                        </g>
                        <text
                          x={x(column)}
                          y={HIGH - 5}
                          text-anchor="middle"
                          class={v.versions.includes(version)
                            ? "fill-foreground text-[0.7rem] font-semibold"
                            : "fill-muted-foreground text-[0.7rem]"}>{named(v)}</text
                        >
                      {/each}
                    </svg>
                  </div>

                  <div>
                    {#if peers.length && latest}
                      <div
                        class="grid grid-cols-[minmax(0,8rem)_minmax(0,1fr)_2.5rem] items-center gap-x-3 gap-y-1"
                        role="group"
                        aria-label={t("Configurations")}
                      >
                        {#each [{ name: got.name, value: latest.means[view] ?? null, own: true, id: 0 }, ...peers.map( (p) => ({ name: p.name, value: p.means[view] ?? null, own: false, id: p.id }) )] as row (row.id)}
                          <span class="truncate text-sm" class:font-medium={row.own}>{row.name}</span>
                          <div bind:clientWidth={stripWidth}>
                            <svg
                              class="block w-full"
                              height={STRIP}
                              role="img"
                              aria-label={row.value === null || row.value === undefined
                                ? `${row.name}: —`
                                : `${row.name}: ${row.value.toFixed(2)}`}
                            >
                              <line
                                x1={along(0, stripWidth)}
                                x2={along(1, stripWidth)}
                                y1={STRIP / 2 + 0.5}
                                y2={STRIP / 2 + 0.5}
                                class="stroke-border"
                                stroke-width="1"
                              />
                              {#if row.value !== null && row.value !== undefined}
                                <circle
                                  cx={along(row.value, stripWidth)}
                                  cy={STRIP / 2}
                                  r={row.own ? 5 : 4}
                                  class={row.own ? "fill-primary stroke-card" : "fill-muted-foreground/70 stroke-card"}
                                  stroke-width="2"
                                />
                              {/if}
                            </svg>
                          </div>
                          <span class="text-right text-sm tabular-nums" class:font-medium={row.own}
                            >{row.value === null || row.value === undefined ? "—" : row.value.toFixed(2)}</span
                          >
                        {/each}
                      </div>
                    {/if}
                  </div>
                </div>
              </figure>
            {/each}
          </div>
        </section>
      {/each}
    </div>

    <details class="mt-8 text-sm">
      <summary class="cursor-pointer text-muted-foreground">{t("The numbers")}</summary>
      <div class="mt-2 overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-left text-[0.7rem] tracking-wide text-muted-foreground uppercase">
              <th class="py-1 pr-3 font-medium">{t("View")}</th>
              <th class="py-1 pr-3 font-medium">{t("Versions")}</th>
              <th class="py-1 pr-3 text-right font-medium">{t("Mean")}</th>
              <th class="py-1 pr-3 text-right font-medium">±95%</th>
              <th class="py-1 pr-3 text-right font-medium">{t("Replicates")}</th>
              <th class="py-1 text-right font-medium">Δ</th>
            </tr>
          </thead>
          <tbody>
            {#each got.views as view, at (at)}
              {#each got.versions as v (v.digest)}
                {@const e = v.estimates[at]}
                {@const d = v.paired[at]}
                <tr class="border-t border-border/60">
                  <td class="py-1 pr-3">{view.label}</td>
                  <td class="py-1 pr-3">{named(v)}</td>
                  <td class="py-1 pr-3 text-right tabular-nums">{e ? e.mean.toFixed(2) : "—"}</td>
                  <td class="py-1 pr-3 text-right tabular-nums">{e && e.half !== null ? e.half.toFixed(2) : "—"}</td>
                  <td class="py-1 pr-3 text-right tabular-nums">{e ? e.n : 0}</td>
                  <td class="py-1 text-right text-muted-foreground tabular-nums">{d ? differs(d) : "—"}</td>
                </tr>
              {/each}
            {/each}
          </tbody>
        </table>
        <table class="mt-6 w-full">
          <thead>
            <tr class="text-left text-[0.7rem] tracking-wide text-muted-foreground uppercase">
              <th class="py-1 pr-3 font-medium">{t("Versions")}</th>
              <th class="py-1 pr-3 text-right font-medium">{t("Repeats")}</th>
              <th class="py-1 pr-3 text-right font-medium">{tp("job", "failed")}</th>
              <th class="py-1 pr-3 text-right font-medium">{t("Tokens")}</th>
              <th class="py-1 font-medium">{t("Languages")}</th>
            </tr>
          </thead>
          <tbody>
            {#each got.versions as v (v.digest)}
              {@const off = mean(v.points.map((p) => mean(p.spread)))}
              {@const alike = v.points.reduce((n, p) => n + p.alike, 0)}
              {@const compared = v.points.reduce((n, p) => n + p.compared, 0)}
              {@const tokens = mean(v.points.map((p) => p.tokens))}
              {@const seconds = v.points.reduce((n, p) => n + p.seconds, 0) / v.points.length}
              {@const last = v.points.at(-1)}
              <tr class="border-t border-border/60" class:font-medium={v.versions.includes(version)}>
                <td class="py-1 pr-3">{named(v)}</td>
                <td class="py-1 pr-3 text-right tabular-nums"
                  >{off === null ? "—" : `±${off.toFixed(2)}`} · {compared ? `≡ ${alike}/${compared}` : "—"}</td
                >
                <td class="py-1 pr-3 text-right tabular-nums"
                  >{`${Math.round((100 * v.points.reduce((n, p) => n + p.failed, 0)) / v.points.length)}%`}</td
                >
                <td class="py-1 pr-3 text-right tabular-nums"
                  >{tokens === null ? "—" : Math.round(tokens)} · {seconds.toFixed(1)} s</td
                >
                <td class="py-1 text-muted-foreground">{last ? languages(last) : ""}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </details>
  {/if}
</div>
