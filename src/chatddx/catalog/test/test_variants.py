from chatddx.catalog import language_of, made_in, variant_name, variants_for


def test_a_variant_is_named_after_the_language_it_was_made_in() -> None:
    assert [variant_name("plan", language) for language in (None, "sv")] == [
        "plan",
        "plan (sv)",
    ]
    assert made_in("plan (sv)") == ("plan", "sv")
    for name in ("plan", "a (b) c", "plan (Swedish)", "plan (sv, other/model)"):
        assert made_in(name) == (name, None)


def test_a_name_finds_its_variants_in_a_language_or_in_any() -> None:
    names = ["plan", "plan (en)", "plan (sv)", "planning (en)"]
    assert variants_for("plan", names) == ["plan (en)", "plan (sv)"]
    assert variants_for("plan", names, "sv") == ["plan (sv)"]
    assert language_of("plan sv") == ("plan", "sv")
    assert language_of("plan (sv)") == ("plan", "sv")
    assert language_of("plan") == ("plan", None)
