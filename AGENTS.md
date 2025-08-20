# Agent Instructions

For any commits that run pre-commit hooks, ensure the R environment is set up:

1. `apt-get update && apt-get install -y r-base`
2. `R -q -e "install.packages('renv', repos='https://cloud.r-project.org')"`
3. Run pre-commit with `RENV_CONFIG_REPOS_OVERRIDE=https://cloud.r-project.org pre-commit run --files <files>`

These steps allow R-based pre-commit hooks to download dependencies from CRAN.
