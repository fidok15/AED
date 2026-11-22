import logging

from django.apps import apps

from mcod.aed.aed_utils import (
    acquire_run_lock,
    clean_up_after_main_aed_resource_creation,
    create_main_aed_file,
    create_main_aed_resource_with_dataset,
    get_owner_organization,
    keep_last_list_after_failed_sources,
    release_run_lock,
    update_or_create_aggr_aed_info_and_delete_old_main_aed,
)
from mcod.core.tasks import extended_shared_task
from mcod.resources.dga_utils import (
    PendingValidationException,
    check_all_resource_validations_status,
)

logger = logging.getLogger("mcod")


@extended_shared_task(
    max_retries=5,
    atomic=False,
    retry_countdown=20,
    retry_on_errors=(PendingValidationException,),
    bind=True,
    name="mcod.aed.tasks.create_main_aed_resource_task",
)
def create_main_aed_resource_task(self) -> None:
    """As create_main_dga_resource_task: 1. national list file from all AED lists, 2. resource (and dataset)
    with map markers, 3. the portal's validations, 4. AggregatedAEDInfo and deletion of the old resource.
    On failure the objects created by this run are deleted."""
    Resource = apps.get_model("resources", "Resource")
    run_id = self.request.id or "manual"  # Celery keeps the task id across retries
    if not acquire_run_lock(run_id):
        logger.warning("Main AED merge already running; this run (%s) ends without changes.", run_id)
        return "locked"
    done = True
    try:
        get_owner_organization()  # configuration error before any list is read

        logger.info("Step 1/4: Creating main AED csv file.")
        file_path, report = create_main_aed_file(run_id)
        if keep_last_list_after_failed_sources(report):
            clean_up_after_main_aed_resource_creation(exception_occurred=False, run_id=run_id)
            return "kept"

        logger.info("Step 2/4: Creating main AED resource with files.")
        resource_pk, _ = create_main_aed_resource_with_dataset(file_path=file_path, run_id=run_id)
        resource = Resource.objects.get(pk=resource_pk)

        logger.info("Step 3/4: Checking resource validations.")
        check_all_resource_validations_status(resource)

        logger.info("Step 4/4: Updating AggregatedAEDInfo and deleting old resource.")
        update_or_create_aggr_aed_info_and_delete_old_main_aed(resource, report)

        clean_up_after_main_aed_resource_creation(exception_occurred=False, run_id=run_id)

    except PendingValidationException:
        if self.request.retries >= self.max_retries:
            clean_up_after_main_aed_resource_creation(exception_occurred=True, run_id=run_id)
        else:
            done = False  # the retry keeps the lock
        raise
    except Exception as exc:
        logger.error("Cleaning after main AED resource creation task due to error: %s", exc)
        clean_up_after_main_aed_resource_creation(exception_occurred=True, run_id=run_id)
        raise
    finally:
        if done:
            release_run_lock(run_id)
