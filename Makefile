SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

PYTHON ?= python3
PROJECT_PYTHONPATH ?= .
PYTEST ?= $(PYTHON) -m pytest
ACTIVE_IGNORE ?=
LINE_EXTS := -name '*.py' -o -name '*.md' -o -name '*.tex' -o -name '*.cu' -o -name '*.cuh'

.PHONY: help status test cert sage-smoke sage-doctest hygiene verify omegaa-collect tables notebooks

help:
	@printf '%s\n' \
	  'Veyra command runner' \
	  '' \
	  'Core verification:' \
	  '  make test          Run the public pytest suite' \
	  '  make cert          Run executable Veyra certificate suite' \
	  '  make sage-smoke    Run Sage facade smoke checks' \
	  '  make sage-doctest  Run veyra_sage doctests' \
	  '  make hygiene       Check active file line hygiene' \
	  '  make verify        Run test + cert + Sage + hygiene' \
	  '' \
	  'Experimental (not part of make verify):' \
	  '  make omegaa-collect  Collect isolated Omega-A tests without running them' \
	  '' \
	  'Artifacts:' \
	  '  make tables        Regenerate processed table artifacts' \
	  '  make notebooks     Regenerate Sage-lab notebook artifacts' \
	  '' \
	  'Inspection:' \
	  '  make status        Show git branch/status'

status:
	@echo '[1/1] Git working-tree status'
	@git status --short --branch

test:
	@echo '[1/1] Running public pytest suite'
	@PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTEST) -q $(ACTIVE_IGNORE)

cert:
	@echo '[1/1] Running executable certificate suite'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/certify_veyra.py

sage-smoke:
	@echo '[1/1] Running Sage facade smoke checks'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/sage_smoke.py

sage-doctest:
	@echo '[1/1] Running veyra_sage doctests'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/sage_doctest.py

hygiene:
	@echo '[1/3] Checking stable source/doc files are <=300 LOC'
	@violations=$$(find . -type f \
		-not -path './.git/*' \
		-not -path './.venv/*' \
		-not -path './node_modules/*' \
		-not -path './experimental/*' \
		-not -path '*/__pycache__/*' \
		\( $(LINE_EXTS) \) -print0 | xargs -0 -r wc -l | awk '$$2 != "total" && $$1 > 300 {print}'); \
	if [[ -n "$$violations" ]]; then \
		printf '%s\n' "$$violations"; \
		exit 1; \
	fi; \
	echo '[ok] no stable source/doc file exceeds 300 LOC'
	@echo '[2/3] Checking experimental source/doc files are <=1000 LOC'
	@violations=$$(find experimental -type f \
		-not -path '*/__pycache__/*' \
		\( $(LINE_EXTS) \) -print0 | xargs -0 -r wc -l | awk '$$2 != "total" && $$1 > 1000 {print}'); \
	if [[ -n "$$violations" ]]; then \
		printf '%s\n' "$$violations"; \
		exit 1; \
	fi; \
	echo '[ok] no experimental source/doc file exceeds 1000 LOC'
	@echo '[3/3] Checking Python cache files remain ignored'
	@git check-ignore -q .pytest_cache/ && git check-ignore -q src/core/__pycache__/ && echo '[ok] cache ignore rules active'

omegaa-collect:
	@echo '[1/1] Collecting isolated Omega-A tests (experimental; not stable verification)'
	@cd experimental/omegaa && PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. $(PYTEST) -p no:cacheprovider --collect-only -q tests

verify:
	@echo '[1/5] Pytest'
	@$(MAKE) --no-print-directory test
	@echo '[2/5] Certificates'
	@$(MAKE) --no-print-directory cert
	@echo '[3/5] Sage smoke'
	@$(MAKE) --no-print-directory sage-smoke
	@echo '[4/5] Sage doctest'
	@$(MAKE) --no-print-directory sage-doctest
	@echo '[5/5] Hygiene'
	@$(MAKE) --no-print-directory hygiene
	@echo '[done] Veyra verification complete'

tables:
	@echo '[1/1] Regenerating processed table artifacts'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/generate_tables.py

notebooks:
	@echo '[1/1] Regenerating Sage-lab notebook artifacts'
	@PYTHONPATH='$(PROJECT_PYTHONPATH)' $(PYTHON) scripts/generate_notebooks.py
