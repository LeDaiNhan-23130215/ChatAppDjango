from django.utils import timezone
from learning_path.models import LearningPathItem
from common.constants import LearningPathItemStatus
from django.db import transaction

@transaction.atomic
def complete_item(item: LearningPathItem, user):
    if item.path.user != user:
        raise PermissionError("Not your learning path")

    if item.status == "COMPLETED":
        return False  # đã hoàn thành rồi

    if item.status != "UNLOCKED":
        raise ValueError("Item is not unlocked")

    # đánh dấu hoàn thành
    item.status = "COMPLETED"
    item.completed_at = timezone.now()
    item.save()

    # mở khóa item tiếp theo
    next_item = LearningPathItem.objects.filter(
        path=item.path,
        order=item.order + 1,
        status="LOCKED"
    ).order_by("order").first()

    if next_item:
        next_item.status = "UNLOCKED"
        next_item.save()

    return True

def get_learning_progress(user):
    items = LearningPathItem.objects.filter(
        path__user = user,
        path__is_active = True
    )

    total = items.count()
    if total == 0:
        return {
            "total" : 0,
            "complete": 0,
            "percent": 0
        }

    completed = items.filter(
        status = LearningPathItemStatus.COMPLETED
    ).count()

    percent = int((completed / total) * 100)

    return {
        "total": total,
        "complete": completed,
        "percent": percent 
    }