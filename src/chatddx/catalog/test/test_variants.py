from chatddx.catalog import made_for, variant_name, variants_for

QWEN = "Qwen/Qwen3-8B-AWQ"
GPT_OSS = "openai/gpt-oss-20b"


def test_a_variant_is_named_after_what_it_was_made_for() -> None:
    assert [
        variant_name("plan", language, model)
        for language, model in [(None, None), ("sv", None), (None, QWEN), ("sv", QWEN)]
    ] == ["plan", "plan (sv)", f"plan ({QWEN})", f"plan (sv, {QWEN})"]
    models = [QWEN]
    assert [made_for(variant_name("plan", "sv", m), models) for m in (None, QWEN)] == [
        ("plan", "sv", None),
        ("plan", "sv", QWEN),
    ]
    assert made_for(f"plan ({QWEN})", models) == ("plan", None, QWEN)
    for name in ("plan", "a (b) c", "plan (sv, other/model)", "plan (Swedish)"):
        assert made_for(name, models) is None


def test_a_model_may_use_the_variants_made_for_it_or_for_every_model() -> None:
    names = [
        "plan",
        "plan (en)",
        f"plan (sv, {QWEN})",
        f"plan (en, {GPT_OSS})",
        f"plan ({QWEN})",
        f"planning (en, {QWEN})",
    ]
    assert variants_for("plan", names, QWEN) == sorted(
        ["plan (en)", f"plan (sv, {QWEN})", f"plan ({QWEN})"]
    )
    assert variants_for("plan", names, None) == ["plan (en)"]
