#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SDL_VERSION="3.4.18"
SDL_SHA256="9c75cf16330322c217dedd2e0609f1124f1b54b8633e763467b4684d0f4334a3"
SDL_URL="https://github.com/libsdl-org/SDL/releases/download/release-${SDL_VERSION}/SDL3-${SDL_VERSION}.tar.gz"
BUILD_ROOT="${ROOT_DIR}/build/phase3-player"
SDL_ARCHIVE="${BUILD_ROOT}/SDL3-${SDL_VERSION}.tar.gz"
SDL_SOURCE="${BUILD_ROOT}/SDL3-${SDL_VERSION}"
SDL_BUILD="${BUILD_ROOT}/SDL3-build"
SDL_PREFIX="${BUILD_ROOT}/prefix"
APP_BUILD="${BUILD_ROOT}/gabbaboy"

for tool in cmake ninja curl shasum tar; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Required tool is missing: %s\n' "${tool}" >&2
    exit 1
  fi
done

mkdir -p "${BUILD_ROOT}"
if [[ ! -f "${SDL_ARCHIVE}" ]] ||
   ! printf '%s  %s\n' "${SDL_SHA256}" "${SDL_ARCHIVE}" | shasum -a 256 --check --status; then
  rm -f "${SDL_ARCHIVE}" "${SDL_ARCHIVE}.partial"
  curl --fail --location --retry 3 --silent --show-error \
    --output "${SDL_ARCHIVE}.partial" "${SDL_URL}"
  printf '%s  %s\n' "${SDL_SHA256}" "${SDL_ARCHIVE}.partial" | shasum -a 256 --check
  mv "${SDL_ARCHIVE}.partial" "${SDL_ARCHIVE}"
fi
printf '%s  %s\n' "${SDL_SHA256}" "${SDL_ARCHIVE}" | shasum -a 256 --check

if [[ ! -f "${SDL_SOURCE}/CMakeLists.txt" ]]; then
  rm -rf "${SDL_SOURCE}"
  mkdir -p "${SDL_SOURCE}"
  tar -xzf "${SDL_ARCHIVE}" --strip-components=1 -C "${SDL_SOURCE}"
fi

cmake --log-level=WARNING -S "${SDL_SOURCE}" -B "${SDL_BUILD}" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="${SDL_PREFIX}" \
  -DSDL_SHARED=ON \
  -DSDL_STATIC=OFF \
  -DSDL_TEST_LIBRARY=OFF \
  -DSDL_TESTS=OFF \
  -DSDL_INSTALL_TESTS=OFF \
  -DSDL_INSTALL_DOCS=OFF
cmake --build "${SDL_BUILD}" --parallel
cmake --install "${SDL_BUILD}" >/dev/null

if [[ ! -s "${SDL_SOURCE}/LICENSE.txt" ]]; then
  printf 'Official SDL source archive has no LICENSE.txt\n' >&2
  exit 1
fi
cp "${SDL_SOURCE}/LICENSE.txt" "${BUILD_ROOT}/SDL3-LICENSE.txt"

cmake --log-level=WARNING -S "${ROOT_DIR}" -B "${APP_BUILD}" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="${SDL_PREFIX}" \
  -DGABBABOY_BUILD_PLAYER=ON \
  -DBUILD_TESTING=ON
cmake --build "${APP_BUILD}" --parallel
ctest --test-dir "${APP_BUILD}" --output-on-failure --no-tests=error -R '^player_'

SDL_LICENSE_SHA256="$(shasum -a 256 "${BUILD_ROOT}/SDL3-LICENSE.txt" | awk '{print $1}')"
SOURCE_REVISION="$(git -C "${ROOT_DIR}" rev-parse HEAD)"
cat >"${BUILD_ROOT}/receipt.txt" <<EOF
SDL version: ${SDL_VERSION}
SDL official source URL: ${SDL_URL}
SDL source archive SHA-256: ${SDL_SHA256}
SDL license SHA-256: ${SDL_LICENSE_SHA256}
Project source revision: ${SOURCE_REVISION}
Player CTest selection: player_*
EOF
printf 'Player verification passed for SDL %s; source digest %s; license digest %s\n' \
  "${SDL_VERSION}" "${SDL_SHA256}" "${SDL_LICENSE_SHA256}"
