from mqtt.publishers.door_publisher import (
    publish_door_command
)


def unlock_door(device_id: str):

    publish_door_command(
        device_id,
        "unlock"
    )


def lock_door(device_id: str):

    publish_door_command(
        device_id,
        "lock"
    )