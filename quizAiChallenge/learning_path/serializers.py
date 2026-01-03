from rest_framework import serializers
from learning_path.models import LearningPath, LearningPathItem

class LearningPathItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPathItem
        fields = [
            "id",
            "order",
            "skill_code",
            "level",
            "item_type",
            "title",
            "status",
        ]

class LearningPathSerializer(serializers.ModelSerializer):
    items = LearningPathItemSerializer(many=True)

    class Meta:
        model = LearningPath
        fields = ["id", "is_active", "items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        learning_path = LearningPath.objects.create(**validated_data)
        for item_data in items_data:
            LearningPathItem.objects.create(path=learning_path, **item_data)
        return learning_path