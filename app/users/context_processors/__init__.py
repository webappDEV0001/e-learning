
from config.common import RECAPTCHA_PUBLIC_KEY


#-------------------------------------------------------------------------------
# common
#-------------------------------------------------------------------------------
def common(request):
    """
    Provides common context data for the entire web app.
    """
    
    context = {}
    context['RECAPTCHA_PUBLIC_KEY'] = RECAPTCHA_PUBLIC_KEY

    return context
