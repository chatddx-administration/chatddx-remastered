from pathlib import Path

from chatddx_dev.index import frontend
from chatddx_dev.index.facts import Comment, Entry, Named

MODULE = """\
// Policy: the limit.
export const LIMIT = 3;

/** Heads-up: a JSDoc block. */
export class Pager {
  // Compromise: kept.
  page = 1;

  next(): void {
    this.page += 1; // Duplication: elsewhere too.
  }
}
"""

COMPONENT = """\
<script lang="ts">
  // Policy: as given.
  let { a, b } = $props();

  function go(): void {}
</script>

<!-- Heads-up: the markup's. -->
<p>{a}{b}</p>
"""


def test_a_module_s_facts_are_its_top_level_names_its_class_s_members_and_comments(
    tmp_path: Path,
) -> None:
    module = tmp_path / "pager.ts"
    _ = module.write_text(MODULE)
    [facts] = frontend.facts([module], tmp_path)
    assert facts.path == "pager.ts"
    assert facts.names == (
        Named("LIMIT", 2, 2, 0),
        Named("Pager", 5, 12, 0),
        Named("Pager.page", 7, 7, 2),
        Named("Pager.next", 9, 11, 2),
    )
    assert facts.comments == (
        Comment(1, 0, "// Policy: the limit.", True),
        Comment(4, 0, "/** Heads-up: a JSDoc block. */", True),
        Comment(6, 2, "// Compromise: kept.", True),
        Comment(10, 20, "// Duplication: elsewhere too.", False),
    )


def test_a_component_s_facts_are_its_script_s_and_its_markup_s_at_their_own_lines(
    tmp_path: Path,
) -> None:
    component = tmp_path / "Pager.svelte"
    _ = component.write_text(COMPONENT)
    [facts] = frontend.facts([component], tmp_path)
    assert facts.names == (
        Named("a", 3, 3, 2),
        Named("b", 3, 3, 2),
        Named("go", 5, 5, 2),
    )
    assert facts.comments == (
        Comment(2, 2, "// Policy: as given.", True),
        Comment(8, 0, "<!-- Heads-up: the markup's. -->", True),
    )


def test_no_file_runs_no_extractor(tmp_path: Path) -> None:
    assert frontend.facts([], tmp_path) == []


def test_a_module_s_surface_is_what_it_exports_its_class_s_public_members_among_it(
    tmp_path: Path,
) -> None:
    module = tmp_path / "pager.ts"
    _ = module.write_text(
        MODULE
        + "\n/** Each page's size. */\n"
        + "export async function size<T>(of: T[], by = 10): Promise<number> {\n"
        + "  return by;\n}\n"
        + "export type Kind = 'a' | 'b';\n"
        + "function hidden(): void {}\n"
    )
    [facts] = frontend.facts([module], tmp_path)
    assert facts.surface == (
        Entry("LIMIT", "`LIMIT`", ("`pager.ts:LIMIT`", "", "`const LIMIT = 3;`")),
        Entry(
            "Pager",
            "`Pager`",
            ("`pager.ts:Pager`", "", "Heads-up: a JSDoc block.", "", "* `page = 1`"),
        ),
        Entry("Pager.next", "`Pager.next`", ("`pager.ts:Pager.next`", "", "* ∟`void`")),
        Entry(
            "size",
            "`size` `async` `<T>`",
            (
                "`pager.ts:size`",
                "",
                "Each page's size.",
                "",
                "* `of: T[]`",
                "* `by = 10`",
                "* ∟`Promise<number>`",
            ),
        ),
        Entry("Kind", "`Kind`", ("`pager.ts:Kind`", "", "`type Kind = 'a' | 'b';`")),
    )


def test_a_component_s_surface_is_its_props_named_after_its_file(
    tmp_path: Path,
) -> None:
    component = tmp_path / "Pager.svelte"
    _ = component.write_text(
        COMPONENT.replace(
            "let { a, b } = $props();",
            "let { a, b = 2 }: { a: string; b?: number } = $props();",
        )
    )
    [facts] = frontend.facts([component], tmp_path)
    assert facts.surface == (
        Entry(
            "Pager",
            "`Pager`",
            ("`Pager.svelte:Pager`", "", "* `a: string`", "* `b?: number = 2`"),
        ),
    )
