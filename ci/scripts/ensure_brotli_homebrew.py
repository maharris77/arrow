# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
from pathlib import Path
import re
import subprocess


def main():
    # Refresh formula metadata, then update only Brotli. Avoid cascading
    # upgrades of installed dependents or cleanup of unrelated packages.
    env = dict(os.environ, HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK="1",
               HOMEBREW_NO_INSTALL_CLEANUP="1")
    subprocess.run(["brew", "update"], check=True, env=env)
    env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
    listing = subprocess.run(["brew", "list", "--versions", "brotli"],
                             capture_output=True, text=True, env=env)
    installed = listing.returncode == 0 and bool(listing.stdout.strip())
    action = "upgrade" if installed else "install"
    subprocess.run(["brew", action, "--formula", "brotli"],
                   check=True, env=env)

    def prefix(formula):
        return subprocess.check_output(["brew", "--prefix", formula],
                                       text=True, env=env).strip()

    brotli_prefix = prefix("brotli")
    pkgconf = str(Path(prefix("pkgconf")) / "bin" / "pkgconf")
    # Ignore other pkg-config paths so stale runner packages cannot satisfy
    # verification. Homebrew 1.2.1 is the fixed successor to runner 1.2.0.
    pkg_dir = str(Path(brotli_prefix) / "lib" / "pkgconfig")
    pkg_env = dict(env, PKG_CONFIG_PATH="", PKG_CONFIG_LIBDIR=pkg_dir)
    for package in ["libbrotlicommon", "libbrotlidec", "libbrotlienc"]:
        version = subprocess.check_output([pkgconf, "--modversion", package],
                                          text=True, env=pkg_env).strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+", version) or \
                tuple(map(int, version.split("."))) < (1, 2, 1):
            raise RuntimeError(f"Unfixed Homebrew {package}: {version}")
        print(f"Verified Homebrew {package} {version}: {brotli_prefix}",
              flush=True)

    # cpp_build.sh forwards this to FindBrotliAlt's explicit root lookup.
    # Builds explicitly selecting BUNDLED keep the fixed bundled source.
    cmake_args = os.environ.get("ARROW_CMAKE_ARGS", "")
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as output:
        output.write(f"ARROW_CMAKE_ARGS={cmake_args} "
                     f"-DBROTLI_ROOT={brotli_prefix}\n")


if __name__ == "__main__":
    main()
