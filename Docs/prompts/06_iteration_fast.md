# Emergency single-fix iteration prompt

Use this when you don't need a full council -- you just want one targeted fix.
~$2-5 in subagent cost. ~3 minutes wall-clock.

---

Read `Reviews/council_round4/council_review_v4.md` (or the latest council
master) and `Results/validation_report.md`.

If all 6 validations pass, propose ONE change that lifts the expected
hackathon score most per minute of work. Implement it via `StrReplace` for
`.py` files or `EditNotebook` for `.ipynb` cells. Re-execute the affected
notebooks via:

```powershell
D:\projects\Data-Storm-2026\.venv\Scripts\python.exe -m nbconvert ^
  --to notebook --execute --inplace ^
  --ExecutePreprocessor.timeout=900 ^
  --ExecutePreprocessor.kernel_name=datastorm-venv ^
  D:\projects\Data-Storm-2026\Notebooks\<file>.ipynb
```

Re-execute order based on what you touched:
- `predict.py` / `constraint_score.py` / `frontier.py` / `sfa.py` -> nb21 then nb22
- nb22 cells only -> nb22
- `gold.py` / `silver.py` / `checks.py` -> nb20 -> nb21 -> nb22

Confirm validation by reading `Results/validation_report.md`. If 6/6 PASS,
report:

1. The single change made (file + line)
2. The expected score lift (qualitative)
3. New validation 6 lines
4. New submission CSV head + row count

If anything fails after the fix, REVERT the change (StrReplace back) and
report what went wrong + the rollback diff.

## Banned

- Any git command
- Touching v1 notebooks (01, 03, 04, 10, 11)
- Touching `Results/_legacy/` or `Docs/_archive/`
- Running with the system Python 3.11 kernel; only `datastorm-venv`
