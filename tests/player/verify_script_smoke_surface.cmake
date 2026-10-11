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

message(STATUS "script-smoke-surface ok")
