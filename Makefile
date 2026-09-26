.PHONY: qa qa-static qa-live
qa:
	bash qa/run-all.sh
qa-static:
	bash qa/run-all.sh --static
qa-live:
	NEODON_LIVE=1 bash qa/run-all.sh --live
