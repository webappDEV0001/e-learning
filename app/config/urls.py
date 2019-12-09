from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from exam.views import ExamListView, about, contact, careers, solutions, OurBaseView
from users.views import set_timezone
from users.views import ViewContact
from users.views import DisplayPDFView

dummy_view = TemplateView.as_view(template_name='index.html')

urlpatterns = [
    path('', dummy_view, name='index'),
    path('about/', about, name='about'),
    path('solutions/', solutions, name='solutions'),
    path('careers/', careers, name='careers'),
    #path('contact/', contact, name='contact'),
    path('contact/', ViewContact.as_view(), name='contact'),
    path('terms-condition/', DisplayPDFView.as_view(), name='terms-condition'),


    path('set_timezone/', set_timezone, name='set_timezone'),

    path('list/', ExamListView.as_view(), name='exam-list'),
    path('ourbase/', OurBaseView.as_view(), name='ourbase'),
	path('exam/', include('exam.urls')),
	path('elearning/', include('elearning.urls')),

    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#just test  for live git access
