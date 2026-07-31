from drf_spectacular.utils import OpenApiParameter, extend_schema


def user_extend_schema(tag: str):
    return extend_schema(
        tags=[tag],
        parameters=[OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun")],
    )
