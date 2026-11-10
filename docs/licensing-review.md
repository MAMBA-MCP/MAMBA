# MAMBA licensing review

**Keep MIT for the original MAMBA code and documentation that the project has authority to license.** The dependency licenses and the current ArduPilot integration do not require relicensing that work. The vendored Dronecode schema carries its own MIT copyright notice. A distribution that includes third-party dependencies must also satisfy their terms.

Reviewed November 9, 2026, against GitHub `main` at [`d9f68b8e910941b3beb2a3ced0cf3d2e496a9c50`](https://github.com/MAMBA-MCP/MAMBA/tree/d9f68b8e910941b3beb2a3ced0cf3d2e496a9c50). GitHub's release and tag endpoints returned empty lists. The tracked tree uses `uv` to fetch dependencies and sets `package = false`. It contains no packaged dependencies, firmware, container build, or simulator models. The registry review covers 94 locked third-party packages, including conditional dependencies and selected extras. I checked exact-version registry metadata and verified the lockfile SHA-256 for 117 wheels, including all seven MAVSDK wheels. I also inspected selected source distributions, build inputs, and separate upstream licenses. This is a source-release decision and a redistribution review of the known inputs. A finished binary or image requires an inventory of its actual contents, including static native libraries and base-system packages. [Project license](https://github.com/MAMBA-MCP/MAMBA/blob/d9f68b8e910941b3beb2a3ced0cf3d2e496a9c50/LICENSE) · [Manifest](https://github.com/MAMBA-MCP/MAMBA/blob/d9f68b8e910941b3beb2a3ced0cf3d2e496a9c50/pyproject.toml) · [Lockfile](https://github.com/MAMBA-MCP/MAMBA/blob/d9f68b8e910941b3beb2a3ced0cf3d2e496a9c50/uv.lock)

## Current source distribution

- **MAMBA originals.** Preserve the root MIT copyright and permission notice in copies or substantial portions of MAMBA. The notice names MAMBA-MCP. Verify that the contributors and any institution or sponsor with applicable ownership or approval rights have authorized MIT publication. Confirm the same authority for the tracked capstone proposal and its embedded artwork, or state separate terms for material governed by other rights. Repository metadata does not establish those permissions. [MIT text](https://opensource.org/license/mit)
- **Dronecode MAVLink-M schema.** Both committed files, `military.xml` and its adjacent `LICENSE`, match the pinned upstream files by SHA-256. Keep Dronecode's copyright and MIT text with copies of the XML, including separately shipped schema fragments containing substantial material. The runtime helper extracts a fragment, and the optional wire test generates a decoder locally. If those outputs are later published, review the output, retain applicable Dronecode attribution, and carry the generator's MIT exception notice where it applies. Standard `common.xml` is not vendored here. [Vendored manifest](https://github.com/MAMBA-MCP/MAMBA/blob/d9f68b8e910941b3beb2a3ced0cf3d2e496a9c50/third_party/mavlink-m/manifest.json) · [Pinned Dronecode license](https://raw.githubusercontent.com/Dronecode/mavlink-military/23cec36751681aa281c1e5ca6b222a07c6c0c002/LICENSE) · [pymavlink 2.4.49 COPYING](https://github.com/ArduPilot/pymavlink/blob/v2.4.49/COPYING)
- **Separately installed Python dependencies.** Publishing dependency references in `pyproject.toml` and `uv.lock` does not distribute the referenced wheels. Runtime uses FastMCP 2.14.7 (Apache-2.0) and native MAVSDK 4.0.6 (BSD-3-Clause), with the MIT-licensed MCP SDK and Pydantic in the runtime graph. pytest is development-only. The optional simulation group adds pymavlink and its dependencies. Independently downloading these packages for local use does not require republishing MAMBA under their licenses. [FastMCP 2.14.7](https://pypi.org/project/fastmcp/2.14.7/) · [MAVSDK 4.0.6](https://pypi.org/project/mavsdk/4.0.6/) · [MCP 1.30.0](https://pypi.org/project/mcp/1.30.0/)
- **ArduPilot.** The validated tests launch an independently built ArduCopter SITL executable and communicate over MAVLink on loopback. MAMBA's companion application can retain MIT in this arrangement. ArduPilot firmware, SITL, and MAVProxy are GPLv3. If conveyed later, comply for each GPL component, including the license and notices, corresponding source by a permitted GPLv3 §6 method for object code, and installation information when §6 requires it for a User Product. Reassess if GPL code is copied into MAMBA or the integration is changed to form a combined program. [SITL evidence](https://github.com/MAMBA-MCP/MAMBA/blob/d9f68b8e910941b3beb2a3ced0cf3d2e496a9c50/docs/testing/mamba-26-27-sitl.md) · [ArduPilot license and companion-computer guidance](https://ardupilot.org/dev/docs/license-gplv3.html) · [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)
- **Other tooling and planned assets.** CPython uses the PSF license and ships additional component terms. `uv` offers MIT or Apache-2.0. The existing setup calls for installing both separately. Gazebo Sim is Apache-2.0, and the ArduPilot Gazebo plugin repository carries LGPL-3.0. Check the particular models, worlds, meshes, textures and plugins if they are selected for distribution. Redis 8.1.0 in the lockfile is the MIT-licensed Python client. The graph also includes MIT-licensed `burner-redis`, an independent Redis-compatible implementation, and BSD-licensed `fakeredis`. A separate Redis server would have its own version-specific terms. [CPython license](https://docs.python.org/3/license.html) · [uv license](https://github.com/astral-sh/uv#license) · [Gazebo Sim](https://github.com/gazebosim/gz-sim) · [ArduPilot Gazebo](https://github.com/ArduPilot/ardupilot_gazebo) · [Redis server license](https://github.com/redis/redis/blob/unstable/LICENSE.txt)

## If MAMBA distributes a bundle

1. **Carry the exact license and attribution files.** Preserve MIT, BSD and ISC notices, conditions and disclaimers where required. Honor BSD-3-Clause's non-endorsement condition. For Apache-2.0 components, provide the license text, mark modified files, retain relevant notices in distributed derivative source, and carry applicable upstream NOTICE attributions. For example, `prometheus-client` declares Apache-2.0 **and** BSD-2-Clause and includes a NOTICE. Preserve both sets of terms. For an **or** expression, record which license the distribution relies on. PSF-2.0 components require preserving the agreement and copyright notice, and a brief summary of changes for a distributed derivative. [Apache-2.0 §4](https://www.apache.org/licenses/LICENSE-2.0) · [BSD-3-Clause](https://opensource.org/license/bsd-3-clause) · [PSF terms](https://docs.python.org/3/license.html) · [Prometheus client 0.26.0](https://pypi.org/project/prometheus-client/0.26.0/)
2. **Handle file-level copyleft.** `certifi` 2026.10.23 is MPL-2.0. Preserve its notices and keep the covered files, including any distributed modifications, under MPL. When conveying executable form, inform recipients how to obtain the corresponding covered source. Separate MAMBA files can retain MIT. [certifi 2026.10.23](https://pypi.org/project/certifi/2026.10.23/) · [MPL §§3.1–3.4](https://www.mozilla.org/en-US/MPL/2.0/)
3. **Handle library copyleft in the Windows and simulation builds.** `pywin32` 312 carries mixed component terms. Its Windows wheel includes `adodbapi` with LGPL 2.1 text, BSD-style code, PSF material and additional notices. Preserve those terms and the covered source as required. `pymavlink` 2.4.49 declares LGPLv3 and ships a generator output exception. The exception applies as stated to output, while the tool and covered library code retain their terms. The `lxml` distribution also identifies native components, including LGPL-2.1 libiconv where bundled, as well as a GPL test runner in source and additional file-specific notices. For any LGPL binaries or combined work conveyed, supply the applicable licenses, notices, and covered library source as required. Use a mechanism that permits recipient replacement or relinking under the applicable version and permits reverse engineering for debugging modifications where required. An ordinary, independently replaceable Python package is a different distribution from a frozen executable. [pywin32 312](https://pypi.org/project/pywin32/312/) · [adodbapi terms](https://github.com/mhammond/pywin32/blob/b312/adodbapi/license.txt) · [pymavlink 2.4.49](https://github.com/ArduPilot/pymavlink/blob/v2.4.49/COPYING) · [lxml 6.1.3 notices](https://github.com/lxml/lxml/blob/lxml-6.1.3-1/LICENSES.txt) · [LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html) · [LGPLv3](https://www.gnu.org/licenses/lgpl-3.0.html)
4. **Fill gaps in upstream wheel notices.** None of the seven locked MAVSDK wheels contained a separate LICENSE, COPYING or NOTICE file. Obtain the tagged BSD-3-Clause text and preserve its copyright, conditions, and disclaimer in redistribution materials. Use the tagged build configuration to account for native inputs such as MAVLink generated code, Asio, fmt, libevents, PicoSHA2, TinyXML2, libmavlike, nlohmann JSON, liblzma, and platform-specific curl, OpenSSL, compression and compiler runtime code. Establish which inputs actually went into each shipped binary. The native Python binding calls the C/C++ library, and the legacy gRPC wrapper is a different package. The two `py-key-value` wheels and the dnspython wheel also lack standalone license files. Retrieve the tagged license texts and preserve the file-level notices. [MAVSDK v4.0.6 license](https://raw.githubusercontent.com/mavlink/MAVSDK/v4.0.6/LICENSE.md) · [Native build inputs](https://raw.githubusercontent.com/mavlink/MAVSDK/v4.0.6/cpp/third_party/CMakeLists.txt) · [Native binding migration guide](https://mavsdk.mavlink.io/v4/en/python/migration.html) · [py-key-value 0.3.0 source](https://github.com/strawgate/py-key-value/tree/6736113ce6c80ef736368680e2c3dafc96a09f9b) · [dnspython 2.9.0 ISC text](https://raw.githubusercontent.com/rthalley/dnspython/v2.9.0/LICENSE)
5. **Review the assembled payload per platform.** Include native libraries embedded inside the shipped wheels, including OpenSSL in `cryptography`, Lua in `burner-redis`, Lua and LuaJIT in `lupa`, and Rust dependencies or C libraries in native wheels. Carry vendored notices in pure-Python wheels too, including `rich-rst`, `typer`, and `markdown-it-py`. If the release includes CPython, `uv`, an OS/base image, firmware, or simulation assets, count those separately. Verify the shipped notice set and applicable source and relinking materials against the final image or installer. The sample wheel review does not resolve every native build variant, Rust crate, OS package, or compiler runtime. [cryptography static linking](https://cryptography.io/en/48.0.0/statements/state-of-openssl/) · [OpenSSL licensing by version](https://openssl-library.org/source/license/index.html) · [Lupa source](https://github.com/scoder/lupa) · [burner-redis 0.1.7](https://pypi.org/project/burner-redis/0.1.7/)

## Locked Python dependency register

The license column records the principal package terms, with material secondary terms noted above and in the table. Runtime is the union across supported platform and Python markers, so a particular installation may contain fewer packages. Development and simulation indicate packages added by those groups. Each link opens the exact publisher release used as evidence. Wheel counts refer to hash-verified files inspected for this review.


| Package | Version | Scope | Principal terms | Wheels checked | Notes |
|---|---|---|---|---:|---|
| [annotated-doc](https://pypi.org/project/annotated-doc/0.0.5/) | 0.0.5 | Runtime | MIT | 1 |  |
| [annotated-types](https://pypi.org/project/annotated-types/0.8.0/) | 0.8.0 | Runtime | MIT | 1 |  |
| [anyio](https://pypi.org/project/anyio/4.15.1/) | 4.15.1 | Runtime | MIT | 1 |  |
| [async-timeout](https://pypi.org/project/async-timeout/5.0.1/) | 5.0.1 | Runtime | Apache-2.0 | 1 |  |
| [attrs](https://pypi.org/project/attrs/26.1.0/) | 26.1.0 | Runtime | MIT | 1 |  |
| [authlib](https://pypi.org/project/authlib/1.9.1/) | 1.9.1 | Runtime | BSD-3-Clause | 1 |  |
| [backports-tarfile](https://pypi.org/project/backports-tarfile/1.2.0/) | 1.2.0 | Runtime | MIT | 1 |  |
| [beartype](https://pypi.org/project/beartype/0.23.1/) | 0.23.1 | Runtime | MIT | 1 |  |
| [burner-redis](https://pypi.org/project/burner-redis/0.1.7/) | 0.1.7 | Runtime | MIT | 1 | Vendored Lua and Rust dependencies. |
| [cachetools](https://pypi.org/project/cachetools/7.2.6/) | 7.2.6 | Runtime | MIT | 1 |  |
| [certifi](https://pypi.org/project/certifi/2026.10.23/) | 2026.10.23 | Runtime | MPL-2.0 | 1 | Covered files retain MPL. |
| [cffi](https://pypi.org/project/cffi/2.1.1/) | 2.1.1 | Runtime | MIT-0 | 3 | Check libffi for the selected build. |
| [click](https://pypi.org/project/click/8.5.0/) | 8.5.0 | Runtime | BSD-3-Clause | 1 |  |
| [cloudpickle](https://pypi.org/project/cloudpickle/3.1.2/) | 3.1.2 | Runtime | BSD-3-Clause | 1 |  |
| [colorama](https://pypi.org/project/colorama/0.4.6/) | 0.4.6 | Runtime | BSD-3-Clause | 1 |  |
| [cronsim](https://pypi.org/project/cronsim/2.7/) | 2.7 | Runtime | BSD-3-Clause | 1 |  |
| [cryptography](https://pypi.org/project/cryptography/50.0.2/) | 50.0.2 | Runtime | Apache-2.0 OR BSD-3-Clause | 3 | Account for statically linked OpenSSL and Rust dependencies. |
| [cyclopts](https://pypi.org/project/cyclopts/5.3.1/) | 5.3.1 | Runtime | Apache-2.0 | 1 |  |
| [diskcache](https://pypi.org/project/diskcache/5.6.3/) | 5.6.3 | Runtime | Apache-2.0 | 1 |  |
| [dnspython](https://pypi.org/project/dnspython/2.9.0/) | 2.9.0 | Runtime | ISC | 1 | Standalone license absent in the sampled wheel. |
| [docstring-parser](https://pypi.org/project/docstring-parser/0.18.0/) | 0.18.0 | Runtime | MIT | 1 |  |
| [email-validator](https://pypi.org/project/email-validator/2.3.0/) | 2.3.0 | Runtime | Unlicense | 1 |  |
| [exceptiongroup](https://pypi.org/project/exceptiongroup/1.3.1/) | 1.3.1 | Runtime | MIT | 1 |  |
| [fakeredis](https://pypi.org/project/fakeredis/2.34.1/) | 2.34.1 | Runtime | BSD-3-Clause | 1 |  |
| [fastcrc](https://pypi.org/project/fastcrc/0.5.0/) | 0.5.0 | Simulation | MIT | 3 | Check Rust dependencies. |
| [fastmcp](https://pypi.org/project/fastmcp/2.14.7/) | 2.14.7 | Runtime | Apache-2.0 | 1 |  |
| [h11](https://pypi.org/project/h11/0.16.0/) | 0.16.0 | Runtime | MIT | 1 |  |
| [httpcore](https://pypi.org/project/httpcore/1.0.9/) | 1.0.9 | Runtime | BSD-3-Clause | 1 |  |
| [httpx](https://pypi.org/project/httpx/0.28.1/) | 0.28.1 | Runtime | BSD-3-Clause | 1 |  |
| [httpx-sse](https://pypi.org/project/httpx-sse/0.4.3/) | 0.4.3 | Runtime | MIT | 1 |  |
| [idna](https://pypi.org/project/idna/3.20/) | 3.20 | Runtime | BSD-3-Clause | 1 |  |
| [importlib-metadata](https://pypi.org/project/importlib-metadata/10.1.0/) | 10.1.0 | Runtime | Apache-2.0 | 1 |  |
| [iniconfig](https://pypi.org/project/iniconfig/2.3.1/) | 2.3.1 | Development | MIT | 1 |  |
| [jaraco-classes](https://pypi.org/project/jaraco-classes/3.4.0/) | 3.4.0 | Runtime | MIT | 1 |  |
| [jaraco-context](https://pypi.org/project/jaraco-context/6.1.2/) | 6.1.2 | Runtime | MIT | 1 |  |
| [jaraco-functools](https://pypi.org/project/jaraco-functools/4.6.0/) | 4.6.0 | Runtime | MIT | 1 |  |
| [jeepney](https://pypi.org/project/jeepney/0.9.0/) | 0.9.0 | Runtime | MIT | 1 |  |
| [joserfc](https://pypi.org/project/joserfc/1.7.7/) | 1.7.7 | Runtime | BSD-3-Clause | 1 |  |
| [jsonref](https://pypi.org/project/jsonref/1.1.0/) | 1.1.0 | Runtime | MIT | 1 |  |
| [jsonschema](https://pypi.org/project/jsonschema/4.26.0/) | 4.26.0 | Runtime | MIT | 1 |  |
| [jsonschema-path](https://pypi.org/project/jsonschema-path/0.5.0/) | 0.5.0 | Runtime | Apache-2.0 | 1 |  |
| [jsonschema-specifications](https://pypi.org/project/jsonschema-specifications/2025.9.1/) | 2025.9.1 | Runtime | MIT | 1 |  |
| [keyring](https://pypi.org/project/keyring/25.7.0/) | 25.7.0 | Runtime | MIT | 1 |  |
| [lupa](https://pypi.org/project/lupa/2.8/) | 2.8 | Runtime | MIT-style | 3 | Includes Lua and LuaJIT. |
| [lxml](https://pypi.org/project/lxml/6.1.3/) | 6.1.3 | Simulation | BSD-3-Clause | 2 | See component terms, including libiconv when present. |
| [markdown-it-py](https://pypi.org/project/markdown-it-py/4.2.0/) | 4.2.0 | Runtime | MIT | 1 | Separate markdown-it notice included. |
| [mavsdk](https://pypi.org/project/mavsdk/4.0.6/) | 4.0.6 | Runtime | BSD-3-Clause | 7 | All seven wheels lack a standalone license file. Native inputs require separate accounting. |
| [mcp](https://pypi.org/project/mcp/1.30.0/) | 1.30.0 | Runtime | MIT | 1 |  |
| [mdurl](https://pypi.org/project/mdurl/0.1.2/) | 0.1.2 | Runtime | MIT | 1 |  |
| [more-itertools](https://pypi.org/project/more-itertools/11.2.1/) | 11.2.1 | Runtime | MIT | 1 |  |
| [openapi-pydantic](https://pypi.org/project/openapi-pydantic/0.6.0/) | 0.6.0 | Runtime | MIT | 1 |  |
| [opentelemetry-api](https://pypi.org/project/opentelemetry-api/1.45.1/) | 1.45.1 | Runtime | Apache-2.0 | 1 |  |
| [packaging](https://pypi.org/project/packaging/26.3/) | 26.3 | Runtime | Apache-2.0 OR BSD-2-Clause | 1 |  |
| [pathable](https://pypi.org/project/pathable/0.6.0/) | 0.6.0 | Runtime | Apache-2.0 | 1 |  |
| [pathvalidate](https://pypi.org/project/pathvalidate/3.3.1/) | 3.3.1 | Runtime | MIT | 1 |  |
| [platformdirs](https://pypi.org/project/platformdirs/4.13.5/) | 4.13.5 | Runtime | MIT | 1 |  |
| [pluggy](https://pypi.org/project/pluggy/1.7.0/) | 1.7.0 | Development | MIT | 1 |  |
| [prometheus-client](https://pypi.org/project/prometheus-client/0.26.0/) | 0.26.0 | Runtime | Apache-2.0 AND BSD-2-Clause | 1 | Both licenses apply. Preserve NOTICE. |
| [py-key-value-aio](https://pypi.org/project/py-key-value-aio/0.3.0/) | 0.3.0 | Runtime | Apache-2.0 | 1 | Standalone license absent. Tagged source has Apache-2.0. |
| [py-key-value-shared](https://pypi.org/project/py-key-value-shared/0.3.0/) | 0.3.0 | Runtime | Apache-2.0 | 1 | Standalone license absent. Tagged source has Apache-2.0. |
| [pycparser](https://pypi.org/project/pycparser/3.11/) | 3.11 | Runtime | BSD-3-Clause | 1 |  |
| [pydantic](https://pypi.org/project/pydantic/2.14.1/) | 2.14.1 | Runtime | MIT | 1 |  |
| [pydantic-core](https://pypi.org/project/pydantic-core/2.50.1/) | 2.50.1 | Runtime | MIT | 3 | Check Rust dependencies. |
| [pydantic-settings](https://pypi.org/project/pydantic-settings/2.16.1/) | 2.16.1 | Runtime | MIT | 1 |  |
| [pydocket](https://pypi.org/project/pydocket/0.27.0/) | 0.27.0 | Runtime | MIT | 1 |  |
| [pygments](https://pypi.org/project/pygments/2.21.0/) | 2.21.0 | Runtime | BSD-2-Clause | 1 |  |
| [pyjwt](https://pypi.org/project/pyjwt/2.15.1/) | 2.15.1 | Runtime | MIT | 1 |  |
| [pymavlink](https://pypi.org/project/pymavlink/2.4.49/) | 2.4.49 | Simulation | LGPL-3.0 with generator output exception | 3 |  |
| [pyperclip](https://pypi.org/project/pyperclip/1.11.0/) | 1.11.0 | Runtime | BSD-3-Clause | 1 |  |
| [pytest](https://pypi.org/project/pytest/9.1.1/) | 9.1.1 | Development | MIT | 1 |  |
| [python-dotenv](https://pypi.org/project/python-dotenv/1.2.4/) | 1.2.4 | Runtime | BSD-3-Clause | 1 |  |
| [python-json-logger](https://pypi.org/project/python-json-logger/4.2.0/) | 4.2.0 | Runtime | BSD-2-Clause | 1 |  |
| [python-multipart](https://pypi.org/project/python-multipart/0.0.32/) | 0.0.32 | Runtime | Apache-2.0 | 1 |  |
| [pywin32](https://pypi.org/project/pywin32/312/) | 312 | Runtime | Mixed (registry says PSF) | 1 | Windows-only. Includes LGPL-2.1 adodbapi, BSD-style and PSF components, and other notices. |
| [pywin32-ctypes](https://pypi.org/project/pywin32-ctypes/0.2.3/) | 0.2.3 | Runtime | BSD-3-Clause | 1 |  |
| [pyyaml](https://pypi.org/project/pyyaml/6.0.3/) | 6.0.3 | Runtime | MIT | 3 | Check LibYAML attribution where linked. |
| [redis](https://pypi.org/project/redis/8.1.0/) | 8.1.0 | Runtime | MIT | 1 | Python client. |
| [referencing](https://pypi.org/project/referencing/0.37.0/) | 0.37.0 | Runtime | MIT | 1 |  |
| [rich](https://pypi.org/project/rich/15.0.0/) | 15.0.0 | Runtime | MIT | 1 |  |
| [rich-rst](https://pypi.org/project/rich-rst/2.2.0/) | 2.2.0 | Runtime | MIT | 1 | Separate vendored notices included. |
| [rpds-py](https://pypi.org/project/rpds-py/2026.9.1/) | 2026.9.1 | Runtime | MIT | 3 | Check Rust dependencies. |
| [secretstorage](https://pypi.org/project/secretstorage/3.5.0/) | 3.5.0 | Runtime | BSD-3-Clause | 1 |  |
| [shellingham](https://pypi.org/project/shellingham/1.5.4/) | 1.5.4 | Runtime | ISC | 1 |  |
| [sortedcontainers](https://pypi.org/project/sortedcontainers/2.4.0/) | 2.4.0 | Runtime | Apache-2.0 | 1 |  |
| [sse-starlette](https://pypi.org/project/sse-starlette/3.5.0/) | 3.5.0 | Runtime | BSD-3-Clause | 1 |  |
| [starlette](https://pypi.org/project/starlette/1.9.0/) | 1.9.0 | Runtime | BSD-3-Clause | 1 |  |
| [typer](https://pypi.org/project/typer/0.27.3/) | 0.27.3 | Runtime | MIT | 1 | Includes separate vendored Click notice. |
| [typing-extensions](https://pypi.org/project/typing-extensions/4.16.0/) | 4.16.0 | Runtime | PSF-2.0 | 1 |  |
| [typing-inspection](https://pypi.org/project/typing-inspection/0.4.4/) | 0.4.4 | Runtime | MIT | 1 |  |
| [tzdata](https://pypi.org/project/tzdata/2026.5/) | 2026.5 | Runtime | Apache-2.0 | 1 | Preserve wrapper and underlying database notices. |
| [uncalled-for](https://pypi.org/project/uncalled-for/0.4.1/) | 0.4.1 | Runtime | MIT | 1 |  |
| [uvicorn](https://pypi.org/project/uvicorn/0.54.0/) | 0.54.0 | Runtime | BSD-3-Clause | 1 |  |
| [websockets](https://pypi.org/project/websockets/17.3/) | 17.3 | Runtime | BSD-3-Clause | 1 |  |
| [zipp](https://pypi.org/project/zipp/4.1.2/) | 4.1.2 | Runtime | MIT | 1 |  |
