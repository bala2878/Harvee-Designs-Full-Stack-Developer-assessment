import enum

class CategoryEnum(str, enum.Enum):
    GENERAL = "GENERAL"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"

class AllocationStatusEnum(str, enum.Enum):
    ALLOCATED = "ALLOCATED"
    NOT_ALLOCATED = "NOT_ALLOCATED"

class AllocationRunStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
