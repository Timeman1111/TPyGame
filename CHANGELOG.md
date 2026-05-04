# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.6] - 2026-05-04

### Added
- Property-based accessors to various rendering components for consistency. ([d66e86b](https://github.com/Timeman1111/TPyGame/commit/d66e86b))
- Tracking of created files and `__repr__` method to `FileManager` class. ([47426bb](https://github.com/Timeman1111/TPyGame/commit/47426bb))

### Changed
- Refactored frame comparison logic and parallel processing for better efficiency and modularity. ([d66e86b](https://github.com/Timeman1111/TPyGame/commit/d66e86b))
- Comprehensive docstring updates across the project, including module-level, class, and function documentation. ([47426bb](https://github.com/Timeman1111/TPyGame/commit/47426bb), [883b9a1](https://github.com/Timeman1111/TPyGame/commit/883b9a1), [4fe2879](https://github.com/Timeman1111/TPyGame/commit/4fe2879))
- Reorganized `scripts` directory structure by moving graphics-related scripts to `scripts/graphics/`. ([47426bb](https://github.com/Timeman1111/TPyGame/commit/47426bb), [883b9a1](https://github.com/Timeman1111/TPyGame/commit/883b9a1))
- Improved `.gitignore` to broader exclude environment and IDE-specific files. ([42fd318](https://github.com/Timeman1111/TPyGame/commit/42fd318), [883b9a1](https://github.com/Timeman1111/TPyGame/commit/883b9a1))

### Removed
- `.idea` directory and `src/TPyGame.egg-info` from the repository. ([a504070](https://github.com/Timeman1111/TPyGame/commit/a504070), [9afbdf2](https://github.com/Timeman1111/TPyGame/commit/9afbdf2))

## [0.0.5] - 2026-05-04

### Added
- `draw_circle` method to `Screen` class, supporting both filled and outlined circles. ([1fed154](https://github.com/Timeman1111/TPyGame/commit/1fed154))
- Image scaling functionality to allow resizing of frames. ([44f8911](https://github.com/Timeman1111/TPyGame/commit/44f8911))
- `bouncing_circles.py` script demonstrating the new `draw_circle` method. ([6629a5c](https://github.com/Timeman1111/TPyGame/commit/6629a5c))
- `profile_video.py` script for performance profiling of video rendering. ([80471ce](https://github.com/Timeman1111/TPyGame/commit/80471ce))

### Changed
- Extensive revamp of `README.md` with detailed usage, features, and project structure. ([34752f2](https://github.com/Timeman1111/TPyGame/commit/34752f2))
- Improved frame comparison logic for more efficient rendering updates. ([44f8911](https://github.com/Timeman1111/TPyGame/commit/44f8911))
- Adjusted LRU cache size in `term_utils.py` to optimize resource usage. ([80471ce](https://github.com/Timeman1111/TPyGame/commit/80471ce))

[0.0.6]: https://github.com/Timeman1111/TPyGame/compare/v0.0.5...v0.0.6
[0.0.5]: https://github.com/Timeman1111/TPyGame/compare/v0.0.4...v0.0.5
