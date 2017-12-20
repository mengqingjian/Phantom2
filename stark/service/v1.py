from django.conf.urls import url
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import HttpResponse,render,redirect
from django.http import QueryDict
from django.db.models import Q
import copy

"""userconfig继承starkconfig"""

class FilterOption(object):
    def __init__(self,field_name,multi=False,condition=None,is_choice=False):
        """

               :param field_name: 字段
               :param multi:  是否多选
               :param condition: 显示数据的筛选条件
               :param is_choice: 是否是choice
        """
        self.field_name=field_name
        self.multi=multi
        self.is_choice=is_choice
        self.condition=condition
    def get_queryset(self,_field):
        if self.condition:
            return _field.rel.to.objects.filter(self.condition)
        return _field.rel.to.objects.all()

    def get_choices(self,_field):
        return _field.choices



class FilterRow(object):      #创建对象
    def __init__(self,option,data,request):
        self.data=data
        self.option=option
        self.request=request
    def __iter__(self):        #生成器也是可迭代对象的一种
        params=copy.deepcopy(self.request.GET)    #params就是request.GET这个参数
        params._mutable=True
        current_id=params.get(self.option.field_name)  #取的是当前发过来的值,这个值是字符串
        current_id_list=params.getlist(self.option.field_name)

        if self.option.field_name in params:
            origin_list=params.pop(self.option.field_name)
            url = "{0}?{1}".format(self.request.path_info, params.urlencode())
            yield mark_safe('<a href="{0}">全部</a>'.format(url))
            params.setlist(self.option.field_name,origin_list)
        else:
            url = "{0}?{1}".format(self.request.path_info, params.urlencode())
            yield mark_safe('<a class="active" href="{0}">全部</a>'.format(url))
        for val in self.data:
            if self.option.is_choice:            #这个表示的是choice选项
                pk,text=str(val[0]),val[1]       #把这个值全部转换成字符串
            else:
                pk,text=str(val.pk),str(val)     #这里如果不是choice就是一个对象，对象直接.pk就可以取出来

            #当前的URL
                  #self.request.path_info  取的是当前的路径
                  #self.request.GET 它是传过来的url
            if not self.option.multi:
                """单选"""
                params[self.option.field_name]=pk
                url = "{0}?{1}".format(self.request.path_info, params.urlencode())
                if current_id==pk:    #传过来的值和pk做判断
                    yield mark_safe("<a class='active',href='{0}'>{1}</a>".format(url,text))
                else:
                    yield mark_safe("<a href='{0}'>{1}</a>".format(url,text))
            else:
                """多选"""
                _params = copy.deepcopy(params)
                id_list = _params.getlist(self.option.field_name)
                print("urrent_id_list",current_id_list)
                print("pk",pk)
                print("id_list",id_list)
                if pk in current_id_list:
                    id_list.remove(pk)
                    print("55id_list",id_list)
                    _params.setlist(self.option.field_name, id_list)
                    url = "{0}?{1}".format(self.request.path_info,_params.urlencode())
                    print("url",url)
                    yield mark_safe("<a class='active'href='{0}'>{1}</a>".format(url, text))
                else:

                    id_list.append(pk)
                    #params被重新复制
                    _params.setlist(self.option.field_name,id_list)
                   #创建url
                    url = "{0}?{1}".format(self.request.path_info, _params.urlencode())
                    yield mark_safe("<a href='{0}'>{1}</a>".format(url,text))




class ChangeList(object):
    def __init__(self,config,queryset):
        self.config=config
        self.list_display=config.get_list_display()
        self.model_class=config.model_class
        self.request=config.request
        self.show_add_btn=config.get_show_add_btn()
        self.actions = config.get_actions()
        self.show_actions=config.get_show_actions()
        self.comb_filter=config.get_comb_filter()
        #搜索
        self.show_search_form=config.get_show_search_form()
        self.search_form_val=config.request.GET.get(config.search_key,"")


        from utile.pager import Pagination
        current_page = self.request.GET.get('page', 1)
        totale_count = queryset.count()
        pager_obj = Pagination(current_page, totale_count, self.request.path_info, self.request.GET, per_page_count=3)
        self.pager_obj=pager_obj
        self.data_list=queryset[pager_obj.start:pager_obj.end]

    def modify_actions(self):
        result=[]
        for func in self.actions:
            temp={"name":func.__name__,'text':func.short_desc}
            result.append(temp)
        return result

    def add_url(self):
        return self.config.get_add_url()

    def head_list(self):
        """
        构造表头
        :return:
        """
        result = []
        for filted_name in  self.list_display:
            if isinstance(filted_name, str):
                # 根据类和字段名称，获取字段对象的verbose_name
                verbose_name = self.model_class._meta.get_field(filted_name).verbose_name
            else:
                verbose_name = filted_name(self.config, is_header=True)  #self是startconfig中edit中self对象
            result.append(verbose_name)
        return result

    def body_list(self):
        data_list = self.data_list
        new_data_list = []
        for row in data_list:
            # row是 UserInfo中的字段
            # row.id,row.name,row.age
            temp = []
            # print("999",row)
            for field_name in self.list_display:
                if isinstance(field_name, str):
                    val = getattr(row,field_name)
                    # print("8995556",val)
                else:
                    val = field_name(self.config,row)
                temp.append(val)
            # print("+++++",temp)
            new_data_list.append(temp)
        return new_data_list

    def gen_comb_filter(self):
        """
        生成器
        :return:
        """
        from django.db.models import ForeignKey,ManyToManyField
        for option in self.comb_filter:
            _field=self.model_class._meta.get_field(option.field_name)
            if isinstance(_field,ForeignKey):
                row=FilterRow(option,option.get_queryset(_field),self.request)
            elif isinstance(_field,ManyToManyField):
                row = FilterRow(option,option.get_queryset(_field),self.request)
            else:
                row=FilterRow(option,option.get_choices(_field),self.request)
                #可迭代对象
            yield row     #返回的是可迭代对象



class StarkConfig(object):
      #1.定制页面显示的列
    def checkbox(self,obj=None,is_header=False):
        if is_header:
            return '选择'
        return mark_safe('<input type="checkbox" name="pk" value="%s" />' %(obj.id,))
    def edit(self,obj=None,is_header=False):
        if is_header:
            return '编辑'

        query_str=self.request.GET.urlencode()
        if query_str:
            params=QueryDict(mutable=True)
            params[self._query_param_key]=query_str
            return mark_safe('<a href="%s?%s">编辑</a>' %(self.get_chang_url(obj.id),params.urlencode(),))
        return mark_safe('<a href="%s">编辑</a>' % (self.get_chang_url(obj.id),))
    def delete(self,obj=None,is_header=False):
        if is_header:
            return '删除'
        return mark_safe('<a href="%s">删除</a>' %(self.get_delete_url(obj.id),))
    list_display = []
    def get_list_display(self):
        data=[]
        if self.list_display:    #self.list_display就是UserInfoConfig中的list_display
            data.extend(self.list_display)
            data.append(StarkConfig.edit)
            data.append(StarkConfig.delete)
            data.insert(0,StarkConfig.checkbox)
        return data

     #2.是否显示添加按钮
    show_add_btn=True
    def get_show_add_btn(self):
        return self.show_add_btn

    #3.model_form_class
    model_form_class=None
    def get_model_form_class(self):
        if self.model_form_class:
            return self.model_form_class
        from django.forms import ModelForm
        # class add_ModeForm(ModelForm):
          # def Meta(self):
          #     model = self.model_class
          #     fields = "__all__"
        meta=type('Meta',(object,),{'model':self.model_class,'fields':"__all__"})
        add_ModeForm=type("add_ModeForm",(ModelForm,),{'Meta':meta})
        return add_ModeForm

    #4.关键字搜索

    show_search_form=False
    def get_show_search_form(self):
        return self.show_search_form
    search_fields=[]
    def get_search_fields(self):
        result=[]
        if self.search_fields:
            result.extend(self.search_fields)
        return result

    def get_search_condition(self):
        key_word = self.request.GET.get(self.search_key)
        search_fields = self.get_search_fields()
        condition = Q()
        condition.connector = "or"
        if key_word and self.get_show_search_form():
            for field_name in search_fields:
                condition.children.append((field_name, key_word))
        return condition

    #5.actions定制

    show_actions = False

    def get_show_actions(self):
        return self.show_actions

    actions = []
    def get_actions(self):
        result = []
        if self.actions:
            result.extend(self.actions)
        return result

    #6.组合搜索
    comb_filter=[]
    def get_comb_filter(self):
        result = []
        if self.comb_filter:
            result.extend(self.comb_filter)
        return result



    def __init__(self,model_class,site):
        self.model_class=model_class
        self.site=site
        self.request=None
        self._query_param_key="_listfilter"
        self.search_key="_q"


    def warp(self,view_func):
        def inner(request,*args,**kwargs):
            self.request=request
            return view_func(request,*args,**kwargs)
        return inner


    def get_urls(self):
        app_model_name=(self.model_class._meta.app_label,self.model_class._meta.model_name,)
        url_patterns=[
            url(r'^$',self.warp(self.changlist_view),name="%s_%s_changlist"%app_model_name),
            url(r'^add/$',self.warp(self.add_view),name="%s_%s_add"%app_model_name),
            url(r'^(\d+)/delete/$',self.warp( self.delete_view), name="%s_%s_delete" % app_model_name),
            url(r'^(\d+)/change/$', self.warp(self.change_view), name="%s_%s_chang" % app_model_name),
        ]

        url_patterns.extend(self.extra_url())
        return url_patterns
    def extra_url(self):
        return []

    @property
    def urls(self):
        return self.get_urls()

    def get_chang_url(self,nid):
        name="stark:%s_%s_chang"%(self.model_class._meta.app_label,self.model_class._meta.model_name)
        edit_url=reverse(name,args=(nid,))
        return edit_url
    def get_add_url(self):
        name="stark:%s_%s_add"%(self.model_class._meta.app_label,self.model_class._meta.model_name)
        edit_url=reverse(name)
        return edit_url
    def get_delete_url(self,nid):
        name="stark:%s_%s_delete"%(self.model_class._meta.app_label,self.model_class._meta.model_name)
        edit_url=reverse(name,args=(nid,))
        return edit_url
    def get_list_url(self):
        name="stark:%s_%s_changlist"%(self.model_class._meta.app_label,self.model_class._meta.model_name)
        edit_url=reverse(name)
        return edit_url

#########################处理请求的方式##############################
    def changlist_view(self,request,*args,**kwargs):

        if request.method=="POST" and self.get_show_actions():
            func_name_str=request.POST.get('list_action')
            action_func=getattr(self,func_name_str)
            ret=action_func(request)
            if ret:
                return ret

        comb_conditions={}
        option_list=self.get_comb_filter()
        for key in request.GET.keys():
            value_list=request.GET.getlist(key)
            flag=False
            for option in option_list:
                if option.field_name==key:
                    flag=True
                    break
            if flag:
                comb_conditions["%s__in" %key]=value_list
        queryset = self.model_class.objects.filter(self.get_search_condition()).filter(**comb_conditions).distinct()
        c1=ChangeList(self,queryset)      #self是当前的对象
        # print("55555",c1.data_list)
        return render(request,'stark/changelist.html',{"c1":c1})


        # head_list = []
        # for filted_name in self.get_list_display():
        #     if isinstance(filted_name, str):
        #         # 根据类和字段名称，获取字段对象的verbose_name
        #         verbose_name = self.model_class._meta.get_field(filted_name).verbose_name
        #     else:
        #         verbose_name = filted_name(self, is_header=True)
        #     head_list.append(verbose_name)
        #
        #
        #
        # #处理分页
        # from utile.pager import Pagination
        # current_page=request.GET.get('page', 1)
        # totale_count=self.model_class.objects.all().count()
        # pager_obj = Pagination(current_page,totale_count, request.path_info, request.GET,per_page_count=3)
        #
        #
        #
        # #处理表中数据
        # data_list = self.model_class.objects.all()[pager_obj.start:pager_obj.end]
        # new_data_list = []
        # for row in data_list:
        #     # row是 UserInfo(id=2,name='alex2',age=181)
        #     # row.id,row.name,row.age
        #     temp = []
        #     for field_name in self.get_list_display():
        #         if isinstance(field_name, str):
        #             val = getattr(row,field_name)
        #         else:
        #             val = field_name(self,row)
        #         temp.append(val)
        #     new_data_list.append(temp)
        #
        # return render(request, 'stark/changelist.html', {'data_list': new_data_list, 'head_list': head_list,'pager_obj':pager_obj,'add_url':self.get_add_url(),'show_add_btn':self.get_show_add_btn(),})


    #添加的数据及页面，用modelform
    def add_view(self, request, *args, **kwargs):
        model_form_class=self.get_model_form_class()
        if request.method=="GET":
            form=model_form_class()
            return render(request,"stark/add_view.html",{'form':form})
        else:
            form=model_form_class(request.POST)
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            return render(request, "stark/add_view.html", {'form': form})
    #修改数据及页面
    def change_view(self, request, nid, *args, **kwargs):
        obj=self.model_class.objects.filter(pk=nid).first()
        if not obj:
            redirect(self.get_list_url())
        model_form_class=self.get_model_form_class()
        if request.method=="GET":
            form=model_form_class(instance=obj)
            return render(request,"stark/change_view.html",{'form':form})
        else:
            form=model_form_class(instance=obj,data=request.POST)
            if form.is_valid():
                form.save()
                list_query_str=request.GET.get(self._query_param_key)
                list_url="%s?%s" %(self.get_list_url(),list_query_str,)
                return  redirect(list_url)
            return render(request, "stark/change_view.html", {'form': form})
    def delete_view(self, request, nid):
        # return HttpResponse(123)
        self.model_class.objects.filter(pk=nid).delete()
        return redirect(self.get_list_url())
class StarkSite(object):
    def __init__(self):
        self._registry = {}
    def register(self,model_class,stark_config_class=None):
        if not stark_config_class:
            stark_config_class=StarkConfig
        self._registry[model_class]=stark_config_class(model_class,self)

    def get_urls(self):
        url_pattern=[]

        for model_class,stark_config_obj in self._registry.items():
            """为每一个类，创建了4个url"""
            app_name=model_class._meta.app_label
            model_name=model_class._meta.model_name

            curd_url=url(r'^%s/%s/'%(app_name,model_name,),(stark_config_obj.urls,None,None))
            url_pattern.append(curd_url)
        return url_pattern
    @property
    def urls(self):
        return(self.get_urls(),None,'stark')


site=StarkSite()
