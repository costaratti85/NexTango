# Local repo workflow

Recommended folder layout:

```text
SistemaIndustrial/
  erpnext/
  sistema_industrial_nextango/
  shared_data/
```

Do not put the SistemaIndustrial repo inside ERPNext core folders.

Before work:

```bash
git pull
python -m pytest
```

After work:

```bash
git add .
git commit -m "short useful message"
git push
```

Agents should work through branches or coordination tasks to avoid collisions.
