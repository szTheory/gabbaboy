# Per-area CTest fragments for Phase 16 (D-02a).
#
# tests/CMakeLists.txt includes this file once, before gabbaboy_verify_registered_tests() and before
# gbb_scale_sanitizer_test_timeouts(), so every add_test() made here is counted in the inventory and gets
# the shared sanitizer timeout scaling. Later plans append one include() line each for their fragment;
# plan 16-01 adds none. Every test name registered by a fragment must also be listed in
# tests/expected-tests.txt.
