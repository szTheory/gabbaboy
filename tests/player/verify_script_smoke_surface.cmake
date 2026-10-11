# D-38 attack-surface check for the scripted player smoke (cmake -P).
#
# Inputs (passed with -D): GBB_SMOKE_C, GBB_SMOKE_H, GBB_PLAYER_MAIN.
#
# The --input-script diagnostic is a developer tool. It must stay free of environment
# activation, network or telemetry access, writes to files and the player's battery/save
# persistence, so a future change cannot quietly widen what a replayed script can reach.
# Failure message: "script-smoke-surface: <token> in <file>"; success: "script-smoke-surface ok".
foreach(required GBB_SMOKE_C GBB_SMOKE_H GBB_PLAYER_MAIN)
  if(NOT DEFINED ${required} OR NOT EXISTS "${${required}}")
    message(FATAL_ERROR "script-smoke-surface: input ${required} is missing or unreadable")
  endif()
endforeach()

# Plain substrings. The persistence names come from src/player/session.h.
set(forbidden_tokens
  # environment access
  getenv SDL_getenv SDL_GetEnvironment
  # network and telemetry access
  socket "connect(" getaddrinfo gethostbyname SDL_OpenURL curl "http:" "https:"
  # file writes other than the literal read-only fopen below
  freopen O_WRONLY O_RDWR O_CREAT
  # the player's battery and save persistence
  player_session_load_battery player_session_save_battery player_session_lock_battery
  player_session_unlock_battery player_session_remove_battery_file
  player_session_replace_rom attempt_battery_save)

foreach(module_file IN ITEMS "${GBB_SMOKE_C}" "${GBB_SMOKE_H}")
  file(READ "${module_file}" content)
  get_filename_component(display_name "${module_file}" NAME)
  foreach(token IN LISTS forbidden_tokens)
    string(FIND "${content}" "${token}" position)
    if(NOT position EQUAL -1)
      message(FATAL_ERROR "script-smoke-surface: ${token} in ${display_name}")
    endif()
  endforeach()
  # A write-mode fopen: the last argument is a literal mode containing w, a or +.
  if(content MATCHES "fopen[ \t]*\\([^;]*,[ \t]*\"[rwabx+]*[wa+][rwabx+]*\"[ \t]*\\)")
    message(FATAL_ERROR "script-smoke-surface: write-mode fopen in ${display_name}")
  endif()
  # A mode that is not a literal cannot be shown read-only.
  if(content MATCHES "fopen[ \t]*\\([^;]*[^\" \t]\\)")
    message(FATAL_ERROR "script-smoke-surface: non-literal fopen mode in ${display_name}")
  endif()
endforeach()

# main.c may read other environment variables, but never one that activates the diagnostic.
file(READ "${GBB_PLAYER_MAIN}" main_content)
if(main_content MATCHES "(SDL_)?[Gg]et[Ee]nv(ironmentVariable)?[ \t]*\\([^)]*SCRIPT")
  message(FATAL_ERROR "script-smoke-surface: environment read naming SCRIPT in main.c")
endif()

# The player-side half of the diagnostic (script_scancode, script_deliver, script_progress and
# run_script_smoke) lives in main.c. Scan that bounded slice with the same forbidden tokens.
# run_script_smoke legitimately loads the ROM through player_session_replace_rom, so that one name
# is allowed there; it must still disable the final battery save before the load can fill the
# save identity.
set(slice_begin "static bool script_scancode(")
set(slice_end "static void destroy_player(player *app) {")
string(FIND "${main_content}" "${slice_begin}" slice_start)
string(FIND "${main_content}" "${slice_end}" slice_stop)
if(slice_start EQUAL -1 OR slice_stop EQUAL -1 OR NOT slice_start LESS slice_stop)
  message(FATAL_ERROR "script-smoke-surface: script section markers not found in main.c")
endif()
math(EXPR slice_length "${slice_stop} - ${slice_start}")
string(SUBSTRING "${main_content}" ${slice_start} ${slice_length} slice)
set(main_tokens ${forbidden_tokens})
list(REMOVE_ITEM main_tokens player_session_replace_rom)
foreach(token IN LISTS main_tokens)
  string(FIND "${slice}" "${token}" position)
  if(NOT position EQUAL -1)
    message(FATAL_ERROR "script-smoke-surface: ${token} in main.c script section")
  endif()
endforeach()
if(slice MATCHES "fopen[ \t]*\\(")
  message(FATAL_ERROR "script-smoke-surface: fopen in main.c script section")
endif()
string(FIND "${slice}" "app->skip_final_save = true;" skip_position)
string(FIND "${slice}" "player_session_replace_rom(" load_position)
if(skip_position EQUAL -1 OR load_position EQUAL -1 OR NOT skip_position LESS load_position)
  message(FATAL_ERROR
    "script-smoke-surface: skip_final_save must be set before the ROM load in main.c script section")
endif()

message(STATUS "script-smoke-surface ok")
