# PolishedWorld — Alpha Runbook

> **Rev 5 · 2026-11-05** — §7 names the tag L6.1 deploys: **`alpha-20261105`** on `fbbe222` (the dev-board merge), which carries the report commands and the board; `alpha-20261104` predates both and is not deployed. §7 also says how the dev board moves: `docs/board.md` is read on every request, so a card moved by a deploy shows without `evennia reload`.
> **Rev 4 · 2026-11-05** — the report commands (BACKLOG *In-game bug, idea and player reports*, merged `588bc69`): §2 gains a row in *Who can do what* and a *Reports* section (what players type, the three `manage` menus as run from `warden`, how to read a report, the cached list); §7 notes that a change through the login hook reaches a connected player only at their next login; §8's close-out step 1 exports the reports before the wipe.
> **Rev 3 · 2026-11-04** — §7 names the first tag: the launch minimum is merged (`df0dc4e`) and tagged **`alpha-20261104`**, which L6.1 checks out; *the tag exists only after the L5.1 merge* is no longer true. Nothing else changes (Launch Minimum L5.2).
> **Rev 2 · 2026-11-04** — Launch Minimum decomposition Rev 2 (decision (G)): a new §9 *Automated test players* — the list LM10's filter reads, the filter verified live on the work dev DB, and `evennia --dummyrunner` ruled off the box; §8's close-out rewritten to LM10 Rev 2 (copy, filter, report, the five checks into the roadmap, wipe — Rev 1's GameGold step is gone), with a pointer per check and the incident table for check (1); §5 and §7 name the checks they hold; *What not to do* becomes §10.
> **Rev 1 · 2026-11-04** — first version (Launch Minimum L4.1). Accounts, moderation, the economy, scrolls and the log verified live on the work dev DB (Evennia 6.1.0, two extra accounts); backup verified for `.backup` and `integrity_check`; deploy, the nightly backup, the restore and the wipe are written and marked with the task that runs them.
> **Canonical:** `docs/PolishedWorld_Alpha_Runbook.md` @ G0dlet/PolishedWorld — git wins. If a project-knowledge copy's Rev is lower than the repo's, it's stale.

**What this is:** every line an admin types on the alpha instance more than once, with what it printed and what the player saw. Every output quoted below is from the live run of 2026-11-03/04 on the work dev DB (`G0dlet` as Developer, `warden` as Admin, `tester` as a player); nothing is quoted from a docstring. A section that could not be run yet says so and names the task that runs it (Launch Minimum §10, L6.1–L6.3).
**Design source:** `docs/PolishedWorld_Launch_Minimum_Decomposition.md` LM3 (no new admin commands; this runbook instead), LM7 (the cohort contract), LM10 (close-out), §8 L4.1.
**Names:** `<player>`, `<staff>` and passwords are placeholders. The dev run's values (`tester`, `Tester-Smoke-4471`, …) are dev values and are never reused on the box.

---

## 1. Accounts

Registration is closed (L1.2): no one creates their own account. Staff creates each one.

### Create

```
@py from typeclasses.accounts import Account; a, e = Account.create(username="<player>", password="<one-time password>"); self.msg(str((a, e)))
```

```
(tester(account#4), [])
```

For a staff account add `permissions=["Admin"]` → `(warden(account#3), [])`. A player gets `Player`, the default.

A weak password is refused and nothing is created:

```
(None, ['This password is too short. It must contain at least 8 characters.', 'This password is too common.', 'This password is entirely numeric.'])
```

**Why `Account.create` and not `create.create_account`:** the raw manager call skips password validation, does not join the default channels, and creates no character (`accounts/accounts.py:999`). An account made with it is not on *Public*, so `pub` does nothing for the player, and chargen is never armed.

What `Account.create` does, seen live:

- the character is created at once, with the account's name, and stands as a **stone statue** in Limbo until the first login;
- the first login runs chargen (*"Your character is made. You follow the weaver's trade; the world is yours to make something of."*);
- the account is on *Public*: `pub hello` → `[Public] tester: hello`.

`@accounts` lists the last accounts created (Admin).

### The one-time password

Send it out of band, never in-game. On first login the player changes it:

```
password <one-time password> = <own password>
```

```
Password changed.
```

### Reset (Admin)

```
userpassword <player> = <new one-time password>
```

Staff sees `tester - new password set to 'Tester-Reset-6623'.` The player, if online, sees **the new password in clear**: `warden has changed your password to 'Tester-Reset-6623'.` Treat it as a one-time password too; the player runs `password` again.

### Delete (Developer) — prefer a ban

`@accounts` is Admin-locked, but deletion checks Developer inside the command. From `warden` (Admin):

```
@accounts/delete scratch
You are not allowed to delete accounts.
```

From a Developer:

```
@accounts/delete scratch : smoke
It is often better to block access to an account rather than to delete it. Are you sure you want to permanently delete account 'scratch' yes/[no]?
yes
Informing and disconnecting account ...
Account scratch was successfully deleted.
```

**The character is not deleted.** It stays, as a statue, with whatever it carries:

```
@find scratch
One Match(#1-#170):
   stone statue of scratch(#169) - typeclasses.characters.Character
@destroy #169
Are you sure you want to destroy stone statue of scratch [yes]/no?
yes
scratch was destroyed.
```

During the alpha, **ban, do not delete** (§2): a ban is undone with one line; a deletion is not, and leaves an orphan behind.

---

## 2. Moderation

### Who can do what

| Line | Lock | Seen live |
| --- | --- | --- |
| `boot`, `wall`, `userpassword`, `@accounts` | Admin | run from `warden` |
| `ban`, `unban`, `@accounts/delete`, `@economy` | Developer | from `warden`: `Command 'ban tester' is not available. Maybe you meant "rest", "eat" or "barter"?` · `Command '@economy' is not available. Maybe you meant "@open", "@copy" or "ooc"?` · `You are not allowed to delete accounts.` |
| `channel/boot`, `channel/ban` | channel `control` (Admin) | **broken in 6.1.0** — see below |
| `manage bugs`, `manage ideas`, `manage reports` | Admin (and each report's `read:pperm(Admin)`) | run from `warden`, 2026-11-05 — see *Reports* below |

Not run in this protocol: `emit` (Builder), `perm` (Developer), `force` (Builder).

### The colon rule

Write **`<name>:<reason>` with no space before the colon.** In Evennia 6.1.0 `boot` and `@accounts/delete` strip the name, but `ban` and `channel/boot|ban` do not, and a trailing space makes a ban that never matches (below).

### `wall` — tell everyone (Admin)

```
wall Smoke test, please ignore.
Announcing to all connected sessions ...
```

Every connected session, staff included, sees `warden shouts "Smoke test, please ignore."`

### `boot` — disconnect a session (Admin)

```
boot <player>:<reason>
```

The player sees, and is disconnected:

```
You have been disconnected by warden.

Reason given: smoke
Connection closed by foreign host.
```

The room sees `tester's body slowly turns to weathered stone, their final pose frozen in place.` A boot does **not** stop the player logging straight back in; for that, ban.

### `ban` — refuse the account at login (Developer)

```
ban <player>:<reason>
Are you sure you want to Name-ban 'tester' [Y]/N?
Y
Name-ban 'tester' was added. Use unban to reinstate.
```

**A ban does not disconnect anyone.** Boot right after: `boot <player>`. At the next login the player sees:

```
You have been banned and cannot continue from here.
If you feel this ban is in error, please email an admin.
```

(The second line is Evennia's text; the cohort reaches staff the way `help alpha` says.)

**The trap — read the name inside the quotes before answering `Y`.** With a space before the colon:

```
ban tester : smoke
Are you sure you want to Name-ban 'tester ' [Y]/N?
Y
Name-ban 'tester ' was added. Use unban to reinstate.
```

The stored name is `tester ` with a trailing space, the login check compares it to `tester`, and **the player logged straight back in** (`commands/default/admin.py`, `rsplit` without a strip; `accounts/accounts.py:659`). The `bans` table does not show the space, so the confirmation prompt is the only place it is visible. Answer `N` and retype it.

### `bans` and `unban` (Developer)

```
bans
Active bans:
+----+---------+--------------------------+--------+
| id | name/ip | date                     | reason |
+----+---------+--------------------------+--------+
| 1  | tester  | Wed Nov  4 17:52:23 2026 | smoke  |
| 2  | tester  | Wed Nov  4 17:53:34 2026 | smoke  |
+----+---------+--------------------------+--------+
unban 1
Are you sure you want to unban 1: 'tester' [Y]/N?
Y
Cleared ban 1: 'tester'
```

Numbers shift down after each unban: to clear several, repeat `unban 1` and read `bans` again until `No active bans were found.`

### `ban/ip` — refuse an address or a subnet (Developer)

```
ban/ip 127.0.0.*
Are you sure you want to IP-ban '127.0.0.*' [Y]/N?
Y
IP-ban '127.0.0.*' was added. Use unban to reinstate.
```

The banned address sees the same refusal at login. Sessions already connected are not touched (in the run, `G0dlet` and `warden` on `127.0.0.1` stayed in and lifted it with `unban 1`).

- **A subnet that covers your own address locks out your next login.** Stay logged in until it is lifted. If you are locked out anyway (not run; `server/models.py`, `ServerConfig.conf`):

  ```
  evennia shell
  >>> from evennia.server.models import ServerConfig
  >>> ServerConfig.objects.conf("server_bans", [])
  >>> exit()
  ```

  This clears **every** ban; re-add the ones you meant to keep.
- **Each refused login counts against the login throttle** for that address, five per five minutes (`accounts/accounts.py:747`, `LOGIN_THROTTLE`). A player who keeps retrying while banned locks the address out for five minutes after the ban is lifted.

### `channel/boot` and `channel/ban` — do not use (Evennia 6.1.0 bug)

```
channel/boot Public = tester:smoke
Are you sure you want to boot user tester from channel(s) Public (make sure name/channels are correct. Also note that your reason will be echoed to the channel). [Y]/N?
Y
Error in ask_yes_no. Choice not confirmed (report to admin)
...
AttributeError: 'str' object has no attribute 'value'
```

`boot_user` reads `nick.value[3]` from `nicks.get(..., return_tuple=True)`, which returns the nick's value, not the Attribute (`commands/default/comms.py:629–633`); every account made with `Account.create` has a channel nick (`pub`), so it fails for every player. `channel/ban` calls `boot_user` first (`comms.py:663`) and fails the same way. The crash comes before `channel.disconnect()`, so **nothing changes**: in the run the player's `pub hello` still printed `[Public] tester: hello` afterwards. The line is unchanged on Evennia's `main` as of 2026-11-04.

Misuse of *Public* is handled at account level: `boot`, then `ban` if it continues. (BACKLOG entry *Channel boot/ban crash upstream*, filed at the launch-minimum close-out.)

### Reports — `bug`, `idea`, `report` (players) and `manage` (Admin)

Players file with `bug <message>`, `bug <thing> = <message>`, `idea <message>` (`ideas` lists their own) and `report <player> = <message>`; `help alpha` tells them so. The commands work everywhere, OOC and inside character creation included, but a player gets them **at their next login**: `evennia reload` does not run the login hook (§7).

Staff read them in a menu, one per type:

```
manage bugs
manage ideas
manage reports        # the PLAYER reports, not all of them
```

Pick a number to open a report; its detail line reads *<time> by <account>(account N) about <target>*, where a logged-out character's name shows as *stone statue of <name>*. Mark it *in progress*, *rejected* or *closed*; `q` leaves. The tag line also shows `report`, the tag every report is filed with — it is not a status. A list is read when the menu opens: a report filed while it is open appears after `q` and `manage <type>` again. Seen from `warden` on the work dev DB, 2026-11-05.

Reports are rows in the database and the wipe deletes them; close-out step 1 (§8) exports them first.

---

## 3. The economy (Developer)

```
@economy

Economy
==================================================
  Treasury:            99 Gold, 98 Silver, 15 Copper (temple treasury)
  Minted (total):      100 Gold
  Burned (total):      nothing
  In circulation:      100 Gold
  Reserve obligation:  100.0000 GameGold
==================================================
  Run @economy audit to verify the invariant.
```

```
@economy audit

Economy audit
  Wallets:        1 Silver, 85 Copper  (2 holders)
  Treasury:       99 Gold, 98 Silver, 15 Copper
  Total held:     100 Gold
  Minted:         100 Gold
  Burned:         nothing
  Expected:       100 Gold
  Result:         OK (delta 0)
  Every unit of money traces to a recorded mint.
```

Run `@economy audit` after anything unusual, and at close-out (§8). Anything but `OK (delta 0)` means money appeared or vanished outside a recorded mint or burn; stop and read the activity log (§5) before doing anything else.

**Minting** (not run here): `@economy mint <amount> <denomination>` previews; nothing is created until the same line is repeated with `confirm`. It mints into the Treasury, never into a character. **Never mint before the contract names the amount** — the Treasury on the box is seeded by L6.3's runbook, and that is the only mint the alpha plans.

---

## 4. Scrolls

Fifteen scrolls lie in the Old Temple (`alpha.room.temple`), one per recipe the professions do not grant (L3.3). A scroll is used up when a player learns from it:

```
learn scroll of tent
You study the scroll of tent and commit the tent recipe to memory. Its work done, the scroll crumbles away.
```

`seed_world()` does **not** put it back: placed scrolls are recorded in the ledger `ServerConfig` `seed.scrolls_placed`, and a learned scroll stays learned. To put one back, by hand:

```
@py from world.seeding import reseed_scroll; self.msg(str(reseed_scroll("<recipe>")))
scroll of tent
```

It spawns only if no scroll of that recipe exists anywhere, in the temple or in someone's pack; otherwise it creates nothing and prints `None` (the same line run twice: `scroll of tent`, then `None`). It deletes nothing.

A recipe without a scroll row raises, and lists the names that have one:

```
ValueError: no seeded scroll for recipe 'nosuch' -- world/seed_data.py SCROLLS names: linen shirt, leather boots, hood, scrollcase, bandolier, breeches, sack, backpack, shoes, robe, reversible clothes, linen cuirass, saddlebag, bone armour, tent
```

Before the world is seeded it raises `RuntimeError: seed_world: seeded room 'alpha.room.temple' not found` (from `world/seeding.py:140`; not producible on a seeded DB).

---

## 5. The log

Every economic act is one JSON line in `server/logs/activity.jsonl`, written by the code that performs it (L2.1–L2.2). The report reads it offline; it needs no running server:

```
python -m world.activity_report server/logs/activity.jsonl
```

The run's report after the protocol (64 lines before; the 62 in game-year 229 are test fixtures on the dev DB):

```
activity report: server/logs/activity.jsonl
lines 66 · malformed 0

per kind
  craft      36
  dismantle  4
  improve    12
  knowledge  11
  trade      1
  work       2

per game-month
  0001-02  knowledge 2 · trade 1 · work 1
  0229-02  craft 36 · dismantle 4 · improve 12 · knowledge 9 · work 1

price list (copper; one item against coin only)
  length of twine      0001-02  n=1  min 5  median 5  max 5
  trades: 1 priced · 0 mixed
...
census: 6 of 10 kinds seen; missing: consume, crumble, gather, repair; unknown: -
```

The two lines the protocol added (`tail -2 server/logs/activity.jsonl`):

```
{"ts": "2026-11-04T18:20:06.910+00:00", "gt": {"year": 1, "month": 2, "day": 27, "hour": 5}, "kind": "knowledge", "actor": ["#168", "tester"], "room": "#120", "verb": "learn", "recipe": "tent", "medium": "scroll", "carrier": "#163"}
{"ts": "2026-11-04T18:24:36.497+00:00", "gt": {"year": 1, "month": 2, "day": 27, "hour": 6}, "kind": "trade", "actor": ["#168", "tester"], "room": "#120", "part_a": ["#168", "tester"], "part_b": ["#1", "G0dlet"], "a_items": ["length of twine"], "b_items": [], "a_copper": 0, "b_copper": 5}
```

- A death writes no line; the corpse writes `crumble` when it falls apart.
- Read the report before and after, not its absolute counts, wherever tests have ever run against that game directory.
- **Never run `evennia test` in the box's game directory**: test runs write fixture lines (actor `#6 Char`, game-year 229) into the same file.
- Server errors are not in this file. `evennia -log` tails `server/logs/server.log` and `portal.log`; the traceback of §2's channel crash was there, stamped `2026-11-04 18:07:48 [!!]`.
- **LM10 check (4)** is read there, in `server/logs/`, not here: by close-out every traceback since the instance opened has a fix on `main` or an entry in `docs/BACKLOG.md`.
- At close-out the report runs over a **filtered copy** (§9), never over the box's file: automated test players' lines are not data about players.

---

## 6. Backup and restore

Verified on the dev DB, with the server running:

```
sqlite3 --version
3.54.0 2026-10-09 …
sqlite3 server/evennia.db3 ".backup $HOME/evennia-pre-L4.1.db3"
sqlite3 $HOME/evennia-pre-L4.1.db3 "PRAGMA integrity_check"
ok
```

`.backup` is safe on a live database; a plain `cp` of `evennia.db3` is not. Without the `sqlite3` CLI (not run; the dev machine had it), Python's module does the same:

```
python -c "import sqlite3,os; s=sqlite3.connect('server/evennia.db3'); d=sqlite3.connect(os.path.expanduser('~/evennia-backup.db3')); s.backup(d); d.close(); print('done')"
```

**Not yet run — L6.2:** the nightly `systemd` timer (the `.backup` above into `/var/backups/pw/evennia-$(date +%F).db3`, then `activity.jsonl` and `server/logs/*.log` into the same directory), the off-box copy keeping fourteen days, and the **restore rehearsal**: stop, restore yesterday's file into a scratch copy of the game directory, start, log in, stop. L6.2 fills this section with its receipts.

---

## 7. Deploy

**Not yet run — L6.1.** The tag L6.1 deploys is **`alpha-20261105`** (on `fbbe222`, the dev-board merge). `alpha-20261104` (on `df0dc4e`, the launch-minimum merge) predates the report commands and the dev board, and is not deployed. Later deploys use a later `alpha-YYYYMMDD` on `main`. The sequence, in the game directory as the `evennia` user:

```
git fetch --prune
git checkout alpha-YYYYMMDD
pip install -r requirements.txt
pip show evennia          # Version: 6.1.0 — the receipt the pin exists for
evennia migrate
evennia reload
```

Backup (§6) before every deploy. A change to the connection screen and to file-help entries takes effect on `evennia reload` (seen in L4.2). **A change that arrives through the login hook reaches a connected player only at their next login**: `evennia reload` does not run `at_post_login` (seen for the report commands, 2026-11-05). After such a deploy, say so: `wall Log out and in once to get the new commands.` Which changes need `evennia reboot` (portal-side: ports, protocols) is verified in L6.1.

**The dev board** (`/board/`) is `docs/board.md`, read on every request: a deploy whose tag moves a card shows it at once, with no `evennia reload`. A missing or unreadable file shows *Board unavailable*, never an error page. Cards move on `main` at epic start and close-out, with the roadmap (seen on the work dev DB, 2026-11-05; Testing Ref §20).

**LM10 check (3)** needs at least one tagged deploy applied to the **running** instance by this sequence, without a wipe — L6.1's first deploy onto an empty box does not count. When it happens, its receipt goes here: the tag, the date, and `pip show evennia`'s version line.

---

## 8. The wipe

**Not yet run — at close-out.** The world is wiped when the alpha ends (LM10), or earlier if a change cannot be made without migrating cohort characters (LM7).

**An early wipe** is announced **at least seven days ahead**, in three places: the connection screen's line and `help alpha` (both in `world/alpha_contract.py`; a deploy, §7), and a `wall` on the day it is decided:

```
wall The world will be wiped on <date>, at least seven days from today. Everything you carry and everything you made will be gone. Read help alpha.
```

### The five checks, and where each receipt is kept

The alpha closes when LM10's time has run **and** its five checks hold; the roadmap's alpha entry carries the numbers. Each check is read from a file or a receipt:

| LM10 check | Receipt kept in |
| --- | --- |
| (1) no lost state | the incident table below, written as it happens |
| (2) a live restore | §6: L6.2's rehearsal repeated on the box while the alpha runs |
| (3) a live deploy | §7: one tagged deploy onto the running instance, without a wipe |
| (4) tracebacks accounted for | `server/logs/` (§5): each one fixed on `main` or entered in `docs/BACKLOG.md` |
| (5) onboarding unaided | a non-staff human's first `craft` line in the **filtered** log (§9), and that player's own answer that staff did not help beyond `help` — the log cannot say it |

### Incidents (check 1)

An incident is a player losing something the game's own rules did not take. Death, decay and a trade are rules; a crash, a bad deploy, or a restore that rolls a player back are not. One row each, the day it happens:

| Date | Who lost what | Cause | Put back? | Fix on `main` or BACKLOG entry |
| --- | --- | --- | --- | --- |
| — | none yet | | | |

### Close-out, in this order (LM10)

1. Copy **off the box**: `activity.jsonl`; the ledger (`@economy audit`'s output, pasted); the reports, exported first as Developer with `@py from world.report_export import export_reports; self.msg(str(export_reports()))` → `server/logs/reports-<UTC stamp>.jsonl`, one JSON line per report with type, date, sender, target, status and text (§2, *Reports*); a `.backup` of the database (§6).
2. Filter the automated test players out of the copied log (§9).
3. Run the report (§5) over the filtered copy.
4. Write checks (1)–(5), each with its receipt, into the roadmap's alpha entry.
5. Then the wipe.

There is no GameGold step: the alpha no longer sets the GameGold trigger (LM10 Rev 2; roadmap (G4)).

---

## 9. Automated test players

Automated test players are allowed (LM10). They are accounts made exactly like a player's (§1: `Account.create`, `Player`), and their characters go through chargen like anyone's. What drives them is not on the box — the instance runs no code for them — and they are taken out of every reading of the log, offline, by the filter below.

### The list

Every automated account gets a row here **the day it is created, before its first login**, so no line it writes is ever unlisted. The filter reads the character column; the account column is for §2 (`boot` and `ban` act on the account).

| Account | Account dbref | Character dbref | Created |
| --- | --- | --- | --- |
| *(none yet on the box)* | | | |

Both dbrefs come from the creation receipts (§1): `Account.create` prints the account (`(tester(account#4), [])`), and `@find <account name>` prints the character, a statue until the first login (`stone statue of scratch(#169)`). The dev run's values — `tester`, `account#4`, `#168` — belong to a human-driven test account, listed only to verify the filter.

### The filter

A line is dropped when **any party** in it is listed: the actor, either side of a trade (`part_a`, `part_b`), or the other side of a lesson (`counterpart`). A trade between a human and an automated player goes too — its price is not a human's price. The rule reads every `[dbref, key]` pair in the line instead of naming fields, so a party field added later is covered without an edit. `room` is a bare dbref, not a pair, and is never matched. A line that is not JSON passes through untouched, so the report still counts it as malformed.

Run it **off the box**, over the copy (§8), with each listed character dbref as one argument. Quote each dbref: zsh reads an unquoted `#168` as a comment, and the filter then drops nothing.

```
python3 -c 'import json, sys
bots = set(sys.argv[2:])
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    try:
        ev = json.loads(line)
    except ValueError:
        sys.stdout.write(line)
        continue
    if isinstance(ev, dict) and any(
        isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and v[0] in bots
        for v in ev.values()
    ):
        continue
    sys.stdout.write(line)' activity.jsonl '<character dbref>' … > activity-filtered.jsonl
```

Receipt, the work dev log on 2026-11-04, with `#168` listed (the program text exactly as above):

```
wc -l < /tmp/act.jsonl
66
grep -c '"#168"' /tmp/act.jsonl
2
python3 -c 'import json, sys
bots = set(sys.argv[2:])
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    try:
        ev = json.loads(line)
    except ValueError:
        sys.stdout.write(line)
        continue
    if isinstance(ev, dict) and any(
        isinstance(v, list) and len(v) == 2 and isinstance(v[0], str) and v[0] in bots
        for v in ev.values()
    ):
        continue
    sys.stdout.write(line)' /tmp/act.jsonl '#168' > /tmp/act-filtered.jsonl
wc -l < /tmp/act-filtered.jsonl
64
grep -c '"#168"' /tmp/act-filtered.jsonl
0
python -m world.activity_report /tmp/act-filtered.jsonl
activity report: /tmp/act-filtered.jsonl
lines 64 · malformed 0

per kind
  craft      36
  dismantle  4
  improve    12
  knowledge  10
  work       2

per game-month
  0001-02  knowledge 1 · work 1
  0229-02  craft 36 · dismantle 4 · improve 12 · knowledge 9 · work 1

price list (copper; one item against coin only)
  (none)
  trades: 0 priced · 0 mixed
...
census: 5 of 10 kinds seen; missing: consume, crumble, gather, repair, trade; unknown: -
```

The two lines dropped are §5's two protocol lines — the `grep` (text) and the filter (structure) agree on them independently. Against §5's report of the same file: `trade` 1 → 0 and its price row gone (the trade had `#168` as `part_a`), `knowledge` 11 → 10, malformed 0 in both. Read the census twice at close-out: a kind missing only from the filtered report was seen only by automated players.

### Never `evennia --dummyrunner` on the box

Evennia's load tester is not an automated test player. It logs in with `create` (`evennia/server/profiling/dummyrunner_settings.py:123, 137` at `v6.1.0`), the door L1.2 closed, and the settings mixin it needs makes every new account a Developer (`settings_mixin.py:20`) and lifts the creation throttle (`:22–23`) and the login throttle (`:24`): on the box that is a hole, not a test. It runs only against a scratch copy of the game directory.

---

## 10. What not to do

- **No GameGold on the box.** The alpha's money is game coin (`help alpha`); nothing on the instance holds or moves GameGold.
- **No hand-placed money.** Money enters only by `@economy mint … confirm` (§3); a coin object made any other way is what `@economy audit` exists to catch.
- **No `git add -A`** in the game directory: add the named files only.
- **No space before the colon** in `ban` (§2): the ban is added and does not bite.
- **No `channel/boot` or `channel/ban`** (§2): they crash in 6.1.0 and change nothing.
- **No account deletion during the alpha** (§1): ban instead; a deleted account leaves its character behind.
- **No `ban/ip` over your own address** without staying logged in (§2).
- **No `evennia test` in the box's game directory** (§5).
- **No `evennia --dummyrunner` against the box** (§9): it grants Developer to every account it makes.
- **No automated account without its row in §9's list** before its first login: its lines would count as a player's.
- **Do not leave a staff character to starve.** Survival runs on staff characters too: `G0dlet` died of thirst in Limbo partway through this protocol (*"You have died."*). Feed it, or expect a corpse mid-moderation.
- **Text after the colon in `trade` is spoken aloud**: `trade G0dlet : smoke` printed `You say, "smoke"` in the room. It is an emote, not a note.
