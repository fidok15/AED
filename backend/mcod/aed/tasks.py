import logging

from django.apps import apps

from mcod.aed.aed_utils import (
    clean_up_after_main_aed_resource_creation,
    create_main_aed_file,
    create_main_aed_resource_with_dataset,
    update_or_create_aggr_aed_info_and_delete_old_main_aed,
)
from mcod.core.tasks import extended_shared_task
from mcod.resources.dga_utils import (
    FailedValidationException,
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
    try:
        logger.info("Step 1/4: Creating main AED csv file.")
        file_path, report = create_main_aed_file()

        logger.info("Step 2/4: Creating main AED resource with files.")
        resource_pk, _ = create_main_aed_resource_with_dataset(file_path=file_path)
        resource = Resource.objects.get(pk=resource_pk)

        logger.info("Step 3/4: Checking resource validations.")
        check_all_resource_validations_status(resource)

        logger.info("Step 4/4: Updating AggregatedAEDInfo and deleting old resource.")
        update_or_create_aggr_aed_info_and_delete_old_main_aed(resource, report)

        clean_up_after_main_aed_resource_creation(exception_occurred=False)

    except PendingValidationException:
        if self.request.retries == self.max_retries:
            clean_up_after_main_aed_resource_creation(exception_occurred=True)
        raise
    except FailedValidationException:
        clean_up_after_main_aed_resource_creation(exception_occurred=True)
        raise
    except Exception as exc:
        logger.error("Cleaning after main AED resource creation task due to unexpected error: %s", exc)
        clean_up_after_main_aed_resource_creation(exception_occurred=True)
        raise
