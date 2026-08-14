# Git Collaboration & Workflow Guide: QET Platforms

This guide documents the Git commands and workflows used to develop, synchronize, and collaborate on the **QET React UI** and **QET Agents** repositories.

---

## 1. Repository Directory Structure

We collaborate across two main local directories:
1. **React UI Repository Root**: `C:/Users/AkshatSinha/Documents/avd/qet-react-ui`
   - Remote URL: `https://github.com/tcsaiqet-crypto/qet-react-ui.git`
2. **Backend Repository Root**: `C:/Users/AkshatSinha/Documents/avd/QET agents/QET agents`
   - Remote URL: `https://github.com/tcsaiqet-crypto/tcscfaqetagents.git`

---

## 2. Authentication (using GitHub PAT)

If GitHub prompts for credentials or if you are configuring a fresh local clone, use your Personal Access Token (PAT) in place of a password:
- **PAT Token**: `ghp_YOUR_PERSONAL_ACCESS_TOKEN_HERE` *(replace with your own token)*
- **Configure Remote URL with Token** (to avoid password prompts):
  ```bash
  # For qet-react-ui
  git remote set-url origin https://ghp_YOUR_PERSONAL_ACCESS_TOKEN_HERE@github.com/tcsaiqet-crypto/qet-react-ui.git

  # For tcscfaqetagents
  git remote set-url origin https://ghp_YOUR_PERSONAL_ACCESS_TOKEN_HERE@github.com/tcsaiqet-crypto/tcscfaqetagents.git
  ```

---

## 3. Daily Developer Workflows

### Phase A: Synchronize and Get Latest Changes
Before starting any new coding work, pull the latest changes from the remote `main` branch to avoid conflicts:
```bash
# 1. Switch to main branch
git checkout main

# 2. Fetch and pull latest changes
git pull origin main
```

### Phase B: Create a Feature Branch
Do NOT make commits directly on `main` when working with others. Create a dedicated feature branch:
```bash
# Create and switch to a new feature branch
git checkout -b feature/f07-requirement-testgen
```

### Phase C: Save and Commit Local Changes
As you write code, check your status and save changes incrementally:
```bash
# 1. View modified, added, or deleted files
git status

# 2. Stage files for commit
git add .

# 3. Create a commit with a descriptive message
git commit -m "feat: implement requirement test generation interface elements"
```

### Phase D: Push Feature Branch to GitHub
Push your local branch to GitHub so others can review your code:
```bash
# Push and link local branch to remote origin
git push -u origin feature/f07-requirement-testgen
```

---

## 4. Merging Changes to the `main` Branch

There are two primary methods for merging your work into `main`:

### Method 1: Creating a Pull Request (PR) on GitHub (Recommended)
1. Go to your repository on GitHub.
2. Click the **Compare & pull request** button next to your pushed branch.
3. Add a description, assign reviewers, and click **Create pull request**.
4. Once tests pass and team members approve, click **Merge pull request**.

### Method 2: Merging Locally (Fast-Track)
If you have direct access and want to merge and push locally:
```bash
# 1. Switch back to main
git checkout main

# 2. Pull latest main changes (critical to prevent out-of-sync pushes)
git pull origin main

# 3. Merge your feature branch changes
git merge feature/f07-requirement-testgen

# 4. Push merged main to GitHub
git push origin main
```

---

## 5. Branch Synchronization / Force Sync (Advanced)

If you need to force-overwrite a remote branch (e.g. updating the remote `main` with local `AkshatWork` branch content):
```bash
# Force pushes local AkshatWork branch to remote main branch (overwriting remote main)
git push origin AkshatWork:main --force
```
> [!WARNING]
> Use `--force` with caution as it overwrites remote branch history. Ensure no one else has pushed commits you don't have locally.

---

## 6. Avoiding Security Leaks (Credentials & Keys)

Never commit API keys or environment secrets to GitHub. 
1. The `.gitignore` file is pre-configured to automatically block `keys/` and `*.txt` credential files:
   ```gitignore
   # Ignore all credential files
   keys/
   *.txt
   ```
2. If you accidentally stage a secret file, unstage it immediately before committing:
   ```bash
   git rm --cached keys/my_api_key.txt
   ```
