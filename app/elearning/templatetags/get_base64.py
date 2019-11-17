import base64

from django.template.defaulttags import register
import requests



#-------------------------------------------------------------------------------
# get
#-------------------------------------------------------------------------------
@register.filter(name='get64')
def get_base64(url):
    """
    Method returning base64 image data instead of URL
    shared certificate images temporarily
    https://ibb.co/zJHhyLF - https://i.ibb.co/16JfDpM/logo.png
    https://ibb.co/C9yVwQr - https://i.ibb.co/n1yQwjW/user-image.png
    https://ibb.co/c6hvDcQ - https://i.ibb.co/bs53zgX/user-logo-img.png
    https://ibb.co/g6tJPr9 - https://i.ibb.co/vDLkQcq/body-bg.jpg
    """
    if not url.startswith("http"):
        url = "{}{}".format("http://127.0.0.1:8000", url)

    response = requests.get(url)
    uri = ("data:" +
           response.headers['Content-Type'] + ";" +
           "base64," + base64.b64encode(response.content).decode("utf-8"))

    return uri
