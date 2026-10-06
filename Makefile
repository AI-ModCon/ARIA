.PHONY: validate-v3-contracts validate-v4-contracts

validate-v3-contracts:
	python3 scripts/validate_v3_contracts.py

validate-v4-contracts:
	python3 scripts/validate_v4_contracts.py
