<script lang="ts">
  import { onMount } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { api, type Schemas, why } from "$lib/api/client";
  import { t } from "$lib/locale";
  import { fieldName } from "$lib/schema/form";
  import { BINS, type Bin, below, binned, grouped } from "./faring";

  let { family, case: faring, schema }: { family: number; case: string; schema: string } = $props();

  type Fared = Schemas["Fared"];
  type Row = Schemas["FaredRow"];

  let got = $state<Fared | null>(null);
  let problem = $state<string | null>(null);
  let width = $state(0);
  let held: HTMLElement;

  // Policy: read once the section is near view, as most visits to a case look at its expectation alone.
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

  async function read(): Promise<void> {
    const res = await api.GET("/api/families/{family}/fared", {
      params: { path: { family }, query: { case: faring, expectation_schema: schema } },
    });
    if (res.data) got = res.data;
    else problem = why(res.error);
  }

  const PAD = 8;
  const HIGH = 32;
  const BASE = HIGH - 6;
  const x = (value: number): number => PAD + value * Math.max(0, width - 2 * PAD);
  const groups = $derived(got === null ? [] : grouped(got));
  const step = $derived(Math.max(2, (width - 2 * PAD) / BINS - 2));

  function told(bin: Bin): string {
    const names = bin.cases.slice(0, 5).map((c) => got?.cases[c]?.title ?? "");
    const more = bin.cases.length - names.length;
    return t("%(value)s: %(num)s cases, %(drawn)s of them drawn: %(names)s", {
      value: (bin.at / BINS).toFixed(2),
      num: bin.cases.length,
      drawn: bin.drawn,
      names: more > 0 ? `${names.join(", ")} …` : names.join(", "),
    });
  }
</script>

<div bind:this={held}>
  <header class="mb-4 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-2">
    <h2>{t("How the case fares")}</h2>
    <ul class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground" aria-label={t("Legend")}>
      <li class="flex items-center gap-1.5">
        <svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="5" class="fill-primary" /></svg>
        {t("This case")}
      </li>
      <li class="flex items-center gap-1.5">
        <svg width="14" height="14" aria-hidden="true"
          ><rect x="3" y="3" width="8" height="10" rx="2" class="fill-muted-foreground/60" /></svg
        >
        {t("Other cases, run")}
      </li>
      {#if got?.synthetic}
        <li class="flex items-center gap-1.5">
          <svg width="14" height="14" aria-hidden="true"
            ><rect x="3" y="3" width="8" height="10" rx="2" class="fill-muted-foreground/30" /></svg
          >
          {t("Other cases, drawn")}
        </li>
      {/if}
    </ul>
  </header>
  {#if got?.synthetic}
    <p class="mb-4 text-sm text-muted-foreground">
      {t(
        "This World draws scores for every case and configuration none of your runs scored: lighter, they show how a case would sit among others, not how any did.",
      )}
    </p>
  {/if}

  {#if problem}
    <p role="alert" class="text-sm text-destructive">{problem}</p>
  {:else if got === null}
    <p role="status" class="flex items-center gap-2 text-sm text-muted-foreground">
      <LoaderCircleIcon class="size-4 animate-spin" />{t("Reading how every case fares…")}
    </p>
  {:else if !got.rows.length}
    <p class="text-sm text-muted-foreground">{t("No configuration of yours has been scored on this case yet.")}</p>
  {:else}
    <div class="space-y-8">
      {#each groups as group (group.field)}
        <section aria-label={group.field === null ? t("The whole answer") : fieldName(group.field)}>
          <h3 class="mb-3 text-sm font-semibold">
            {group.field === null ? t("The whole answer") : fieldName(group.field)}
          </h3>
          <div class="space-y-5">
            {#each group.metrics as metric (metric.at)}
              <figure>
                <figcaption class="mb-1 text-xs text-muted-foreground">{got.metrics[metric.at]?.label}</figcaption>
                <div class="grid grid-cols-[minmax(0,9rem)_minmax(0,1fr)_3.5rem] items-center gap-x-3">
                  {#each metric.rows as row (row.configuration)}
                    {@const shown = row.shown}
                    <span class="truncate text-sm">{got.configurations[row.configuration]?.name}</span>
                    {@const bins = binned(row)}
                    {@const most = Math.max(1, ...bins.map((b) => b.run + b.drawn))}
                    <div bind:clientWidth={width}>
                      <svg
                        class="block w-full"
                        height={HIGH}
                        role="img"
                        aria-label={`${got.configurations[row.configuration]?.name}: ${
                          shown
                            ? t("%(value)s, above %(share)s%% of the other cases", {
                                value: shown.value.toFixed(2),
                                share: Math.round(100 * below(row)),
                              })
                            : t("Not scored on this case")
                        }`}
                      >
                        <line
                          x1={x(0)}
                          x2={x(1)}
                          y1={BASE + 0.5}
                          y2={BASE + 0.5}
                          class="stroke-border"
                          stroke-width="1"
                        />
                        {#each bins as bin (bin.at)}
                          {@const run = ((BASE - 4) * bin.run) / most}
                          {@const drawn = ((BASE - 4) * bin.drawn) / most}
                          <g>
                            <title>{told(bin)}</title>
                            <rect
                              x={x(bin.at / BINS) - step / 2}
                              y="0"
                              width={step}
                              height={BASE}
                              class="fill-transparent"
                            />
                            {#if bin.run}
                              <rect
                                x={x(bin.at / BINS) - step / 2}
                                y={BASE - run}
                                width={step}
                                height={run}
                                rx="2"
                                class="fill-muted-foreground/60"
                              />
                            {/if}
                            {#if bin.drawn}
                              <rect
                                x={x(bin.at / BINS) - step / 2}
                                y={BASE - run - drawn - (bin.run ? 2 : 0)}
                                width={step}
                                height={drawn}
                                rx="2"
                                class="fill-muted-foreground/30"
                              />
                            {/if}
                          </g>
                        {/each}
                        {#if shown}
                          <circle
                            cx={x(shown.value)}
                            cy={BASE}
                            r="5"
                            class={shown.synthetic ? "fill-card stroke-primary" : "fill-primary stroke-card"}
                            stroke-width="2"
                          >
                            <title
                              >{t("This case: %(value)s, above %(share)s%% of the other cases", {
                                value: shown.value.toFixed(2),
                                share: Math.round(100 * below(row)),
                              })}</title
                            >
                          </circle>
                        {/if}
                      </svg>
                    </div>
                    <span class="text-right text-sm font-medium tabular-nums">
                      {#if !shown}<span class="text-muted-foreground">—</span>
                      {:else if shown.href}<a href={shown.href}>{shown.value.toFixed(2)}</a>
                      {:else}{shown.value.toFixed(2)}{/if}
                    </span>
                  {/each}
                  <span></span>
                  <div
                    class="flex justify-between px-1 text-[0.7rem] text-muted-foreground tabular-nums"
                    aria-hidden="true"
                  >
                    <span>0</span><span>0.5</span><span>1</span>
                  </div>
                  <span></span>
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
              <th class="py-1 pr-3 font-medium">{t("Configuration")}</th>
              <th class="py-1 pr-3 text-right font-medium">{t("This case")}</th>
              <th class="py-1 pr-3 text-right font-medium">{t("Above")}</th>
              <th class="py-1 text-right font-medium">{t("Other cases")}</th>
            </tr>
          </thead>
          <tbody>
            {#each got.rows as row, i (i)}
              <tr class="border-t border-border/60">
                <td class="py-1 pr-3">{got.metrics[row.metric]?.label}</td>
                <td class="py-1 pr-3">{got.configurations[row.configuration]?.name}</td>
                <td class="py-1 pr-3 text-right tabular-nums"
                  >{row.shown ? row.shown.value.toFixed(2) : "—"}{row.shown?.synthetic ? ` (${t("drawn")})` : ""}</td
                >
                <td class="py-1 pr-3 text-right tabular-nums">{row.shown ? `${Math.round(100 * below(row))}%` : "—"}</td
                >
                <td class="py-1 text-right tabular-nums">{row.cases.length}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </details>
  {/if}
</div>
