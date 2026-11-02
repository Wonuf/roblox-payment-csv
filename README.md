# Roblox Payout CSV Generator

Builds the `userId,payoutInRobux` CSV that Roblox's group payout upload expects.

- Add payees by **user ID or username** (usernames are looked up on Roblox automatically)
- Pay each person a **fixed Robux amount** or a **% of available funds**
- **Drag rows (⠿)** to set payout order. People higher up get paid first. If funds run out, later people get a reduced amount or nothing.
- Untick a row to skip someone this round without deleting them
- Your list is saved automatically (`%APPDATA%\RobloxPayoutCSV\state.json`)

## Using it

**Easiest:** download `RobloxPayoutCSV.exe` from the [Releases](../../releases) page and double-click it. Your browser opens with the app. Close the black console window to quit.

> Windows SmartScreen may warn about an unsigned app. Click **More info → Run anyway**.

**From source** (needs Python 3.9+, no extra packages): double-click `run.bat`, or run `python app.py`.

## Percentage modes

- **Total available**: 10% always means 10% of the Robux you entered.
- **Remaining at their turn**: 10% means 10% of whatever is left after everyone above them has been paid.

Amounts are rounded down to whole Robux.

## Building / releasing

- Local build: `build.bat` creates `dist\RobloxPayoutCSV.exe`
- GitHub release: push a tag such as `git tag v1.0.0 && git push --tags`. GitHub Actions builds the exe and attaches it to a release.
