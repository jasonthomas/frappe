'''
Created on Dec 9, 2013

.. moduleauthor:: Joao Baptista <joaonrb@gmail.com>

'''

from django.views.generic.base import View, TemplateResponseMixin
from django.shortcuts import render_to_response, RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ffos.models import FFOSUser, FFOSApp
from ffos.recommender.controller import SimpleController
from ffos.recommender.filters import RepetitionFilter, RegionReRanker, \
    LocaleFilter, CategoryReRanker

controller = SimpleController()
controller.registerFilter(
    RepetitionFilter(),
    LocaleFilter()
)
controller.registerReranker(
    RegionReRanker(),
    CategoryReRanker(n=12)
)
class Landing(View, TemplateResponseMixin):

    template_name = "landing.html"

    http_method_names = [
        'get',
#        'post',
#        'put',
#        'patch',
#        'delete',
#        'head',
#        'options',
#        'trace'
        ]

    #def get_context_data(self,request,**kwargs):
    #    context = RequestContext(request)
    #    context.update({'settings': settings})
    #    return context

    def get(self,request,page=1,**kwargs):
        '''

        '''
        page = int(page)
        p = page-1
        users_list = FFOSUser.objects.all()
        paginator = Paginator(users_list, 15) # Show 15 users per page
        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            users = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            users = paginator.page(paginator.num_pages)
        min, max = 2-(paginator.num_pages-p) if p+3 > paginator.num_pages \
            else 0,2-p if p < 3 else 0
        min, max = p-(2+min) if p-(2+min) >= 0 else 0,p+3+max
        page_list = paginator.page_range[min:max]
        context = RequestContext(request)
        context.update({"users": users,'page_list': page_list})
        return render_to_response(self.template_name, context)

class Recommend(View, TemplateResponseMixin):

    template_name = "recommend.html"

    http_method_names = [
        'get',
#        'post',
#        'put',
#        'patch',
#        'delete',
#        'head',
#        'options',
#        'trace'
        ]

    def get(self,request,user,**kwargs):
        '''

        '''
        rec = controller.get_recommendation(user=user,n=80)
        context = RequestContext(request)
        apps = {o.pk: o for o in FFOSApp.objects.filter(pk__in=rec)
            .select_related()}
        reg, regions = {}, FFOSApp.objects.filter(pk__in=rec).values_list(
            'pk', 'regions__name')
        for pk, name in regions:
            reg[pk] = reg[pk]+[name] if pk in reg else [name]
        context.update({"ffosuser": user,'recommended': [(apps[i],reg[i])
            for i in rec]})
        return render_to_response(self.template_name, context)