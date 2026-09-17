PYTHON ?= python3.12

.PHONY: validate docker
validate:
	$(PYTHON) -m unittest tests.integration.test_submission_agent tests.integration.test_input_to_finding -q

docker:
	docker build -t semanticrca .
	@test -n "$(DATASET)" || (echo "Set DATASET to the supplied bundle path"; exit 2)
	@test -n "$(OUT)" || (echo "Set OUT to an empty output path"; exit 2)
	docker run --rm -e FEATHERLESS_API_KEY -e FEATHERLESS_BASE_URL -v "$(DATASET):/data:ro" -v "$(OUT):/out" semanticrca python run.py --dataset /data --queries /data/query.csv --out /out
