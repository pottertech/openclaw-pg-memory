# 🚀 pg-memory Release Checklist

**Purpose:** Prevent forgotten steps during version releases  
**Last Updated:** 2026-03-05 (v3.1.0 release)  
**Status:** ⛔ MANDATORY — Follow for EVERY release

---

## 📋 Pre-Release Checklist

### Code & Version
- [ ] Update version in `scripts/pg_memory.py` (internal version string)
- [ ] Update version in root `README.md` ⚠️ **CRITICAL — OFTEN FORGOTTEN**
- [ ] Update version in `docs/README.md`
- [ ] Update version in all `docs/*.md` files
- [ ] Update version in `tests/*.py` files
- [ ] Run tests to verify functionality

### Documentation
- [ ] Create `docs/RELEASE-vX.X.0.md` with release notes
- [ ] Update `CHANGELOG.md` with new version entry
- [ ] Update `docs/COMMANDS.md` if new commands added
- [ ] Update `docs/FEATURES.md` if new features added

### Git Operations
- [ ] Commit all changes with descriptive message
- [ ] Create annotated git tag: `git tag -a vX.X.0 -m "Release notes"`
- [ ] Push to main: `git push origin main`
- [ ] Push tag: `git push origin vX.X.0`

### Verification (POST-PUSH)
- [ ] ✅ Check root README.md on GitHub main page
- [ ] ✅ Check docs/README.md renders correctly
- [ ] ✅ Verify tag appears in releases tab
- [ ] ✅ Test installation from fresh clone

---

## ⚠️ Common Mistakes (Learn from History)

### ❌ v3.0.0 Release (2026-03-05)
**Mistake:** Forgot to update root `README.md`  
**Fix:** Had to update after user notification

### ❌ v3.1.0 Release (2026-03-05)
**Mistake:** Forgot to update root `README.md` AGAIN  
**Fix:** Updated after user notification + created this checklist

---

## 🎯 Quick Release Commands

```bash
# 1. Update all version strings (run from repo root)
find . -name "*.md" -not -path "./.git/*" -exec sed -i '' 's/v3\.0\.0/v3.1.0/g' {} \;
find . -name "*.py" -not -path "./.git/*" -exec sed -i '' 's/3\.0\.0/3.1.0/g' {} \;

# ⚠️ MANUALLY CHECK ROOT README.md (most forgotten step!)
head -5 README.md

# 2. Commit and tag
git add .
git commit -m "chore: Bump version to 3.1.0"
git tag -a v3.1.0 -m "Release notes"
git push origin main
git push origin v3.1.0

# 3. Verify on GitHub
echo "https://github.com/pottertech/openclaw-pg-memory"
```

---

## 📌 Memory Aid

**"README First!"** — Always update root README.md FIRST before anything else.

**Mnemonic:** 
- **R**oot README = **R**epo front page
- **R**epo front page = **R**elease visibility
- No **R**oot README update = **R**elease looks wrong

---

## 🔗 Related Files

- `docs/RELEASE-v3.1.0.md` — Latest release notes
- `CHANGELOG.md` — Version history
- `docs/README.md` — Documentation index (different from root README!)

---

*Last lesson learned: 2026-03-05 (v3.1.0 release)*  
*Next release: Follow this checklist!*
