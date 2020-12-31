from allauth.account.adapter import DefaultAccountAdapter


class MyAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_redirect_url(self, request):
        path = "/payment"
        return path.format(username=request.user.username)
