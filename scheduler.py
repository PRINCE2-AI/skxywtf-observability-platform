from __future__ import annotations

import logging

from observability.api import baselines, repository, runner
from observability.demo import SERVICES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("observability.scheduler")


def run_scheduled_evaluations() -> None:
    for service in SERVICES:
        result = runner.run_sample_evaluation(service, [{"score": 0.80}, {"score": 0.84}, {"score": 0.78}])
        if repository.get_baseline(service) is None:
            baselines.set_baseline(service, result)
        else:
            alerts = baselines.detect_and_store(service, result)
            logger.info("service=%s score=%s alerts=%s", service, result.scores, len(alerts))


if __name__ == "__main__":
    run_scheduled_evaluations()
