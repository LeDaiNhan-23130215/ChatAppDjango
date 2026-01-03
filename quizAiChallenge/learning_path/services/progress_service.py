from django.utils import timezone
from learning_path.models import LearningPathItem
from django.db import transaction

@transaction.atomic
def complete_item(item: LearningPathItem, user):
    if item.path.user != user:
        raise PermissionError("Not your learning path")

    if item.status != "UNLOCKED":
        raise ValueError("Item is not unlocked")

    if item.status == 'COMPLETED':
        return False
    
    if item.status == 'UNLOCKED':
        return False
    
    item.status = 'COMPLETED'
    item.completed_at = timezone.now()
    item.save()

    next_item = LearningPathItem.objects.filter(
        path = item.path,
        order = item.order + 1,
        status='LOCKED'
    ).order_by('order').first()

    if next_item:
        next_item.status = 'UNLOCKED'
        next_item.save()
    
    return True