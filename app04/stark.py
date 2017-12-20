from stark.service import v1
from. import models

class RoleConfig(v1.StarkConfig):
    list_display = ['id','title']
v1.site.register(models.Role,RoleConfig)

class DepartmentConfig(v1.StarkConfig):
    list_display = ['id','caption']
v1.site.register(models.Department,DepartmentConfig)

class UserInfoConfig(v1.StarkConfig):
    def display_gender(self,obj=None,is_header=False):
        if is_header:
            return '性别'
        # return obj.gender
        return obj.get_gender_display       #取的是数据库中gender这个字段的数据

    def display_depart(self,obj=None,is_header=False):
        if is_header:
            return '部门'
        return obj.depart.caption

    def display_roles(self, obj=None, is_header=False):
        if is_header:
            return '角色'

        html = []
        role_list = obj.roles.all()
        for role in role_list:
            html.append(role.title)
        return ",".join(html)

    list_display = ['id','name','email',display_gender,display_depart,display_roles]
    comb_filter=[
        v1.FilterOption('gender',is_choice=True),
        v1.FilterOption('depart'),
        v1.FilterOption('roles',True)
    ]
v1.site.register(models.UserInfo,UserInfoConfig)