# PolishedWorld — Alpha Runbook

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

**Not yet run — L6.1** (the tag exists only after the L5.1 merge). The sequence, in the game directory as the `evennia` user:

```
git fetch --prune
git checkout alpha-YYYYMMDD
pip install -r requirements.txt
pip show evennia          # Version: 6.1.0 — the receipt the pin exists for
evennia migrate
evennia reload
```

Backup (§6) before every deploy. A change to the connection screen and to file-help entries takes effect on `evennia reload` (seen in L4.2). Which changes need `evennia reboot` (portal-side: ports, protocols) is verified in L6.1.

---

## 8. The wipe

**Not yet run — at close-out.** The world is wiped when the alpha ends (LM10), or earlier if a change cannot be made without migrating cohort characters (LM7).

**An early wipe** is announced **at least seven days ahead**, in three places: the connection screen's line and `help alpha` (both in `world/alpha_contract.py`; a deploy, §7), and a `wall` on the day it is decided:

```
wall The world will be wiped on <date>, at least seven days from today. Everything you carry and everything you made will be gone. Read help alpha.
```

**Close-out**, in this order (LM10), each copied **off the box** before the next:

1. `activity.jsonl`;
2. the ledger: `@economy audit`'s output, pasted;
3. a `.backup` of the database (§6);
4. the report (§5) over the copied file;
5. the GameGold trigger's player count, set from that data;
6. then the wipe.

---

## 9. What not to do

- **No GameGold on the box.** The alpha's money is game coin (`help alpha`); nothing on the instance holds or moves GameGold.
- **No hand-placed money.** Money enters only by `@economy mint … confirm` (§3); a coin object made any other way is what `@economy audit` exists to catch.
- **No `git add -A`** in the game directory: add the named files only.
- **No space before the colon** in `ban` (§2): the ban is added and does not bite.
- **No `channel/boot` or `channel/ban`** (§2): they crash in 6.1.0 and change nothing.
- **No account deletion during the alpha** (§1): ban instead; a deleted account leaves its character behind.
- **No `ban/ip` over your own address** without staying logged in (§2).
- **No `evennia test` in the box's game directory** (§5).
- **Do not leave a staff character to starve.** Survival runs on staff characters too: `G0dlet` died of thirst in Limbo partway through this protocol (*"You have died."*). Feed it, or expect a corpse mid-moderation.
- **Text after the colon in `trade` is spoken aloud**: `trade G0dlet : smoke` printed `You say, "smoke"` in the room. It is an emote, not a note.
