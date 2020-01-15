from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from exam.views import ExamListView, about, contact, careers, solutions, OurBaseView
from users.views import set_timezone
from users.views import ViewContact
from users.views import DisplayPDFView, DisplayPDFView2
from elearning import views as el_view
from django.conf.urls import handler404

from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
}


dummy_view = TemplateView.as_view(template_name='index.html')


urlpatterns = [
    path('', dummy_view, name='index'),
    path('about/', about, name='about'),
    path('solutions/', solutions, name='solutions'),
    path('careers/', careers, name='careers'),
    #path('contact/', contact, name='contact'),
    path('contact/', ViewContact.as_view(), name='contact'),
    path('terms-condition/', DisplayPDFView.as_view(), name='terms-condition'),
    path('privacy-policy/', DisplayPDFView2.as_view(), name='privacy-policy'),


    # Testing Url
    path('change_repitition_date/', el_view.repitiion_date_change, name='change_repitition_date'),

    path('set_timezone/', set_timezone, name='set_timezone'),

    path('list/', ExamListView.as_view(), name='exam-list'),
    path('ifrs-17-e-learning/', OurBaseView.as_view(), name='ourbase'),
	path('exam/', include('exam.urls')),
	path('elearning/', include('elearning.urls')),

    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap')
    path('<slug:slug>',el_view.handler404)

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
