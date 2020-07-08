import rest_framework.authtoken.views
from rest_framework.response import Response

from .models import PluralityAuthToken


class ObtainPluralityAuthToken(rest_framework.authtoken.views.ObtainAuthToken):
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        # Unlike the super class, always creates
        # a new token
        token = PluralityAuthToken.objects.create(user=user)
        return Response(
            {
                "token": token.key,
                "maintenance_organization": str(
                    user.organization.organization.municipality.id
                ),
                "login_identifier": token.id,
            }
        )


obtain_auth_token = ObtainPluralityAuthToken.as_view()
