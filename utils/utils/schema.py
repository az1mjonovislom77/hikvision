from drf_spectacular.utils import extend_schema, OpenApiParameter


def user_extend_schema(tag: str):
    return extend_schema(
        tags=[tag],
        parameters=[
            OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun"),
            OpenApiParameter(name="branch_id", type=int, required=True, description="Branch ID (majburiy)")
        ]
    )
