# sagp_member_manager

PySide6 desktop GUI for exploring and conservatively editing the
canonical SAGP membership database produced by App 2.

## Run

```bash
python main.py output/sagp_members.db
```

If no database path is supplied, App 3 defaults to `output/sagp_members.db`.


## Current editing support

The right-hand detail panel now supports conservative edits for the first UI
slice:

- display name
- first name
- last name
- institution
- primary email
- membership status
- region
- notes

Click **Save** to persist the selected member through `SagpDatabase.update_member`.
Source appearances and membership-code history remain read-only provenance data.

## Database API layer

App 3 database access is centralized in `database_api.py`.

Use:

```python
from database_api import SagpDatabase
```

The GUI and future dashboard/report/AI layers should call named methods on
`SagpDatabase` instead of importing `sqlite3` or writing raw SQL directly.

Current primary methods:

- `get_summary()`
- `count_members()`
- `list_members(limit=None, offset=0)`
- `get_member(person_id)`
- `search_members(text, limit=None)`
- `get_source_appearances(person_id)`
- `get_membership_code_history(person_id)`
- `update_member(member)`

`database.py` remains as a compatibility wrapper with `Database = SagpDatabase`.

## Contract freeze

See `docs/SAGP_CONTRACTS.md` for the frozen App 1 -> App 2 workbook contract,
App 2 -> App 3 SQLite contract, and App 3 internal database API contract.
