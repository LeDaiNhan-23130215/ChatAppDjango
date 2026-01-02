from django.utils import timezone
from learning_path.models import LearningPathItem

def complete_item(item: LearningPathItem):
    if item.status == 'COMPLETED':
        return
    
    item.status = 'COMPLETED'
    item.completed_at = timezone.now()
    item.save()

    next_item = LearningPathItem.objects.filter(
        path = item.path,
        order = item.order + 1
    ).first()

    if next_item and next_item.status == 'LOCKED':
        next_item.status = 'UNLOCKED'
        next_item.save()