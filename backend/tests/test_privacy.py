from intelligence_os.privacy import external_memory_allowed, external_memories


def test_external_memory_policy_defaults_to_opt_in_behavior():
    private = {"allow_external_llm": 0}
    opted = {"allow_external_llm": 1}
    assert external_memory_allowed(private, "opt_in") is False
    assert external_memory_allowed(opted, "opt_in") is True
    assert external_memory_allowed(opted, "off") is False
    assert external_memory_allowed(private, "all") is True
    assert external_memories([private, opted], "opt_in") == [opted]


def test_invalid_external_mode_falls_back_to_opt_in():
    assert external_memory_allowed({"allow_external_llm": 0}, "nonsense") is False
    assert external_memory_allowed({"allow_external_llm": 1}, "nonsense") is True


def test_google_and_sensitive_memory_stay_local_even_in_all_mode():
    google = {"source_type": "gmail", "sensitivity": "sensitive", "allow_external_llm": 1}
    drive = {"source_type": "google_drive", "sensitivity": "personal", "allow_external_llm": 1}
    sensitive = {"source_type": "browser", "sensitivity": "sensitive", "allow_external_llm": 1}
    assert external_memory_allowed(google, "all") is False
    assert external_memory_allowed(drive, "all") is False
    assert external_memory_allowed(sensitive, "all") is False
