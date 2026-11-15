# Contributing

Pull requests are welcome. For larger additions, please consult with z3niith

Timetable, as of `v0.2.0`, has only been made for and tested on Windows; I am unsure of when a MacOS or Linux version may be released.

## Contribution expectations

This repo utilizes [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) to organize commits and all contributions are done through PRs. Setting a PR title to a good commit message helps out. Some examples include:
- `feat: add round clock`
- `fix: timer color`

## Development

```powershell
pip install -r requirements.txt pytest ruff
python -m pytest
ruff check .
```
The timer logic (`engine.py`, `agenda.py`) has no GUI dependency and is unit tested.

Before opening a pull request, please ensure that:
 - Timetable is able to run fully with all dependencies on your local machine
 - `python -m pytest` and `ruff check .` pass without errors

Please include a screenshot, video, or some form of demonstration of the changes being submitted, and thoroughly explain the implementations.

## Automated checks

Every pull request into `main` runs these checks on GitHub:
 - **Conventional Commit title**: the PR title must look like `feat: add round clock` or `fix(hud): timer color`
 - **Lint**: `ruff check .` reports no errors
 - **Tests**: the test suite passes on Windows with Python 3.10 and 3.12
 - **Description has a demo**: the PR description includes a screenshot, video or GIF plus a short explanation. This is skipped for `docs`, `ci`, `test`, `chore`, `build` and `style` PRs, and maintainers can add the `no-demo` label when a demo doesn't apply

By contributing, you agree that your contribution is licensed under the [MIT License](./LICENSE).
