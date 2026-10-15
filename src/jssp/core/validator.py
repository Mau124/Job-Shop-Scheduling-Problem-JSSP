from .models import (
    ValidationResult,
    JSPInstance,
    Schedule
)

'''
We must verify five things:
    1. Every operation exists exactly once
    2. No operation starts before time 0
    3. All operations exist
    4. Precedence constraints are respected
    5. Machines never execute two operations simultaneously

And optionally if we have time to implement:
    6. Durations/machines match the original instance
    7. Reported makespan is correct
'''

""" Usage example
result = solver.solve(instance)

if result.schedule:
    validation = validate_schedule(
        instance,
        result.schedule,
    )

    assert validation.valid
"""

def validate_schedule(
    instance: JSPInstance,
    schedule: Schedule
) -> ValidationResult:
    errors = []

    scheduled = {}

    # 1 and 2:
    for scheduled_op in schedule.operations:
        op = scheduled_op.operation
        key = (op.job_id, op.operation_id)

        # 1. Every operation exists exactly once
        if key in scheduled:
            errors.append(
                f"Operation {key} appears more than once"
            )

        # 2. No operation starts before time 0
        scheduled[key] = scheduled_op

        if scheduled_op.start_time < 0:
            errors.append(
                f"Operation {key} has negative start time"
            )

    # 3. All operations exist
    for job in instance.jobs:
        for op in job.operations:
            key = (op.job_id, op.operation_id)

            if key not in scheduled:
                errors.append(
                    f"Operation {key} is missing"
                )

    # 4. Precedence constraints are respected
    for job in instance.jobs:
        for i in range(len(job.operations) - 1):
            current_op = job.operations[i]
            next_op = job.operations[i + 1]

            current_key = (
                current_op.job_id,
                current_op.operation_id
            )

            next_key = (
                next_op.job_id,
                next_op.operation_id
            )

            # no need to verify non-scheduled operations
            if current_key not in scheduled \
                or next_key not in scheduled:
                continue

            current = scheduled[current_key]
            next_scheduled = scheduled[next_key]

            if next_scheduled.start_time < current.end_time:
                errors.append(
                    f"Precedence violation: "
                    f"{next_key} starts at "
                    f"{next_key.start_time}, "
                    f"but {current_key} finishes at "
                    f"{current.end_time}"
                )

    # 5. Machines never execute two operations simultaneously
    # Group operations by machine
    by_machine = {}

    for scheduled_op in schedule.operations:
        machine = scheduled_op.operation.machine_id

        by_machine.setdefault(machine, []).append(
            scheduled_op
        )

    # Check for machine overlap
    for machine, operations in by_machine.items():
        operations.sort(
            key=lambda op: op.start_time
        )

        for i in range(len(operations) - 1):
            current = operations[i]
            next_op = operations[i + 1]

            if current.end_time > next_op.start_time:

                current_key = (
                    current.operation.job_id,
                    current.operation.operation.id
                )

                next_key = (
                    next_op.operation.job_id,
                    next_op.operation.operation_id
                )

                errors.append(
                    f"Machine {machine} overlap: "
                    f"{current_key} ends at "
                    f"{current.end_time} "
                    f"but {next_key} starts at"
                    f"{next_op.start_time}"
                )

    return ValidationResult(
        valid = len(errors) == 0,
        errors = errors
    )
