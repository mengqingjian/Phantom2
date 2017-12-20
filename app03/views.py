from django.shortcuts import render
from app03 import pager
HOST_LIST=[]
for i in range(1,104):
    HOST_LIST.append("c%s.com"%i)
from app03.pager import Pagination
def hosts(request):
    pager_obj = Pagination(request.GET.get('page', 1), len(HOST_LIST), request.path_info)
    host_list = HOST_LIST[pager_obj.start:pager_obj.end]
    html = pager_obj.page_html()
    return render(request, 'hosts.html', {'host_list': host_list, "page_html": html})
    # try:
    #  current_page=int(request.GET.get('page',1))
    # except Exception as e:
    #     current_page=1
    #
    # per_page_count=10
    # start=(current_page-1)*per_page_count
    # end=current_page*10
    # host_list=HOST_LIST[start:end]
    # total=len(HOST_LIST)
    # max_page_html,div=divmod(total,per_page_count)
    # if div:
    #     max_page_html+=1
    # page_html_list=[]
    # for i in range(1,max_page_html+1):
    #     if i==current_page:
    #         temp='<a class="active" href="/hosts/?page%s">%s</a>'%(i,i)
    #     else:
    #         temp = '<a href="/hosts/?page%s">%s</a>' % (i, i)
    #         page_html_list.append(temp)
    # page_html=''.join(page_html_list)
    # return render(request,"hosts.html",{"host_list":host_list,"page_html":page_html})




