"""Configuration constants for Slurm Swiss Knife."""

VERBS = {
    "show": ["ls", "list", "get"],
    "update": ["set", "modify", "edit"],
    "create": ["add", "create", "new"],
    "delete": ["remove", "delete", "rm"],
}

ROUTES = {
    "get-set": {
        "partitions": {
            "name": "name",
            "state": "state",
            "nodes": "nodes",
            "accounts": "accounts",
            "hidden": "hidden",
        },
        "nodes": {
            "name": "name",
            "state": "state",
            "partitions": "partitions",
            "users": "users",
            "account": "account",
        },
        "jobs": {
            "state": "state",
            "user": "user",
            "account": "account",
            "partition": "partition",
            "reservation": "reservation",
        },
        "users": {
            "name": "name",
            "account": "account",
            "state": "state",
            "qos": "qos",
            "reservation": "reservation",
            "nodes": "nodes",
            "partition": "partition",
        },
        "qos": {
            "name": "name",
            "default": "default",
            "accounts": "accounts",
            "partition": "partition",
            "users": "users",
        },
        "accounts": {
            "name": "name",
            "users": "users",
            "partitions": "partitions",
            "qos": "qos",
        },
        "associations": {
            "account": "account",
            "user": "user",
            "cluster": "cluster",
            "partition": "partition",
            "qos": "qos",
        },
        "reservations": {
            "name": "name",
            "users": "users",
            "partitions": "partitions",
        },
        "coordinators": {"user": "user", "accounts": "account"},
        "events": {
            "cluster": "cluster",
            "node": "node",
            "state": "state",
            "user": "user",
            "reason": "reason",
        },
        "config": {},
    },
    "create": {
        "partitions": {},
        "nodes": {},
        "users": {},
        "qos": {},
        "accounts": {},
        "associations": {},
        "reservations": {},
        "coordinators": {},
    },
}
