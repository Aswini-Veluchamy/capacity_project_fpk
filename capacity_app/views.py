from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import CapacityData, HistoryData, ProjectPlannerData, MilestoneData, ProjectPlannerHistoryData, FinanceProcurementApprovalData
from datetime import datetime
import time
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.models import Q


def send_mail(subj, msg):
    import smtplib

    sender = 'ecpadmin@us-east-1.tcsecp.com'
    receivers = ['aswini.vel@tcs.com']

    SUBJECT = subj
    TEXT = msg
    message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)

    smtpObj = smtplib.SMTP('172.25.240.25', 25)
    smtpObj.sendmail(sender, receivers, message)

    print("Successfully sent email")


# Create your views here.
@csrf_exempt
def user_login(request):
    context = {}
    user_group = ""
    if request.method == "POST":
        '''getting user data from form'''
        username = request.POST['username']
        password = request.POST['password']
        ''' verifying user with the database'''
        user1 = authenticate(request, username=username, password=password)

        if user1:

            login(request, user1)
            email = user1.email
            group = request.user.groups.all()

            projects = [i.name for i in group if i.name not in ["User_Group_Project_Planner", 'User_Group_Finance',
                                                                'User_Group_procurement', "admin", "member"]]

            user_groups = [i.name for i in group if i.name in ["User_Group_Project_Planner", 'User_Group_Finance',
                                                               'User_Group_procurement', "admin", "member"]]

            request.session["user_group"] = [user_groups, projects, username, email]

            if 'User_Group_Project_Planner' in user_groups:
                return HttpResponseRedirect(reverse("project_create_request"))

            elif 'User_Group_Finance' in user_groups:
                return HttpResponseRedirect(reverse("financial_approval"))

            elif 'User_Group_procurement' in user_groups:
                return HttpResponseRedirect(reverse("procurement_approval"))

            elif 'admin' in user_groups:
                return HttpResponseRedirect(reverse("admin_view_request"))

            '''redirecting to dashboard page'''
            return HttpResponseRedirect(reverse("dashboard"))

        else:
            ''' user provide wrong credentials sending error msg'''
            context["error"] = "Provide Valid Credentials"
            return render(request, "capacity_app/login1.html", context)

    else:
        return render(request, "capacity_app/login1.html")


def user_logout(request):
    logout(request)
    try:
        del request.session["user_group"]
    except:
        pass
    return HttpResponseRedirect(reverse('login'))


@csrf_exempt
@login_required
def dashboard(request):
    user_group = request.session["user_group"][0]
    project = request.session["user_group"][1]
    email = request.session["user_group"][3]
    if "admin" not in user_group:
        query_set = ProjectPlannerData.objects.filter(project_name=project[0], financial_approval=True, procurement_approval=True)
        return render(request, 'capacity_app/dashboard.html', {"user_group": user_group, "email": email, "query_data": query_set})
    else:
        return render(request, 'capacity_app/dashboard.html',
                      {"user_group": user_group, "email": email, "query_data": "admin"})


def storage_space_verification(project, column_name, value):
    sum_value = 0

    project_planner_data = (ProjectPlannerData.objects.filter(project_name=project).values(column_name))
    project_capacity_value = project_planner_data[0][column_name]

    capacity_data = CapacityData.objects.filter(project_name=project).aggregate(capacity_sum=Coalesce(Sum(column_name), 0))
    user_used_capacity = (capacity_data["capacity_sum"])

    completed_capacity_data = HistoryData.objects.filter(project_name=project).aggregate(completed_capacity_sum=Coalesce(Sum(column_name), 0))
    complete_sum = completed_capacity_data["completed_capacity_sum"]

    sum_value = sum_value + (user_used_capacity + complete_sum) + value

    if sum_value > project_capacity_value:
        print(sum_value, project_capacity_value, column_name, "=========================")
        return False
    else:
        print(sum_value, project_capacity_value, column_name, "-------------------------------------")
        return True

@csrf_exempt
@login_required
def create_request(request):
    tkt_status = "ACTIVE"
    user_group = request.session["user_group"][0]
    projects = request.session["user_group"][1]
    email = request.session["user_group"][3]
    mile_stone_data = MilestoneData.objects.filter(project_name=projects[0])

    ''' getting data from user form'''
    if request.method == "POST":
        data_center = request.POST['dc']
        project = request.POST['project']
        user_id = request.POST['user_id']
        move_group_name = request.POST['move_group_name']
        std_stable1 = request.POST['std_stable1']
        std_stable2 = request.POST['std_stable2']
        std_arbor = request.POST['std_arbor']
        stable1 = request.POST['stable1']
        stable2 = request.POST['stable2']
        arbor = request.POST['arbor']
        gravit = request.POST['gravit']
        remarks = request.POST['remarks']

        data_list = [("std_stable1", std_stable1), ("std_stable2", std_stable2),
                     ("std_arbor", std_arbor), ("stable1", stable1), ("stable2", stable2),
                     ("arbor", arbor), ("gravit", gravit)]

        for name, value in data_list:
            if int(value) != 0:
                check_value = storage_space_verification(project, name, int(value))
                if check_value is False:
                    message = f"Please Select values based on quota availability"
                    return render(request, 'capacity_app/create_request.html',
                                  {"user_group": user_group, "projects": projects,
                                   "email": email, "milestone": mile_stone_data, "messages": message})

        request_id = project[0:3] + "_" + str(int(time.time() * 1000))
        now = datetime.now()
        date_time = str(now.strftime("%Y-%m-%d %H:%M:%S"))

        ''' storing data into database '''
        request_data_create = CapacityData.objects.create(
            request_id=request_id,
            updated_time=date_time,
            data_center=data_center,
            project_name=project,
            user_id=user_id,
            std_stable1=std_stable1,
            std_stable2=std_stable2,
            std_arbor=std_arbor,
            stable1=stable1,
            stable2=stable2,
            arbor=arbor,
            gravit=gravit,
            move_group_name=move_group_name,
            remarks=remarks,
            tkt_status=tkt_status,
        )
        request_data_create.save()
        return HttpResponseRedirect(reverse("view_request"))
    else:
        mile_stone_data = MilestoneData.objects.filter(project_name=projects[0])
        return render(request, 'capacity_app/create_request.html', {"user_group": user_group, "projects": projects,
                                                                    "email": email,"milestone": mile_stone_data})


@csrf_exempt
@login_required
def view_request(request):
    """render all request to the front end"""
    user_group = request.session["user_group"][0]
    user_name = request.session["user_group"][2]
    email = request.session["user_group"][3]

    data = CapacityData.objects.filter(user_id=str(user_name))

    return render(request, 'capacity_app/view_request.html', {'data': data,
                                                                  "user_group": user_group, "email": email})


@csrf_exempt
@login_required
def update_project_planner_request(request, pk):
    project = request.session["user_group"][1]
    user_group = request.session["user_group"][0]
    email = request.session["user_group"][3]
    mile_stone_data = MilestoneData.objects.filter(project_name=project[0])
    if request.method == "POST":
        std_stable1 = request.POST.get('std_stable1', None)
        std_stable2 = request.POST.get('std_stable2', None)
        std_arbor = request.POST.get('std_arbor', None)
        stable1 = request.POST.get('stable1', None)
        stable2 = request.POST.get('stable2', None)
        arbor = request.POST.get('arbor', None)
        gravit = request.POST.get('gravit', None)
        remarks = request.POST.get('remarks', None)

        data = ProjectPlannerData.objects.get(request_id=pk)

        if (int(std_stable1) >= data.std_stable1) and (int(std_stable2) >= data.std_stable2) and (int(std_arbor) >= data.std_arbor) and (int(stable1) >= data.stable1) and (int(stable2) >= data.stable2) and (int(arbor) >= data.arbor) and (int(gravit) >= data.gravit):
            ''' create updated ticket data in history table'''
            history_data_create = ProjectPlannerHistoryData.objects.create(
                data_center=data.data_center,
                project_name=data.project_name,
                user_name=data.user_name,
                milestone_name=data.milestone_name,
                date=data.date,
                std_stable1=data.std_stable1,
                std_stable2=data.std_stable2,
                std_arbor=data.std_arbor,
                stable1=data.stable1,
                stable2=data.stable2,
                arbor=data.arbor,
                gravit=data.gravit,
                remarks=data.remarks,
                financial_approval=data.financial_approval,
                procurement_approval=data.procurement_approval,
                created_at=data.created_at
            )
            history_data_create.save()  # saving the record in the table

            updated_at = datetime.now()
            ''' updating the new vales in table '''
            ProjectPlannerData.objects.filter(request_id=pk).update(std_stable1=std_stable1,
                                                            std_stable2=std_stable2,
                                                            std_arbor=std_arbor,
                                                            stable1=stable1,
                                                            stable2=stable2,
                                                            arbor=arbor,
                                                            gravit=gravit,
                                                            remarks=remarks,
                                                            created_at=updated_at,
                                                            financial_approval=False,
                                                            procurement_approval=False)
            return HttpResponseRedirect(reverse("project_view_request"))

        else:
            messages="Please provide greater values!!!!!"
            return render(request, 'capacity_app/update_request.html', {"data": data, "user_group": user_group,
                                                                    "email": email, "mile_stone": mile_stone_data,
                                                                    "messages":messages})
    else:
        data = ProjectPlannerData.objects.get(request_id=pk)
        return render(request, 'capacity_app/update_request.html', {"data": data, "user_group": user_group,
                                                                    "email": email, "mile_stone": mile_stone_data})


@csrf_exempt
@login_required
def completed_request(request, pk):
    """ fetch the record the table based on pk"""
    user_group = request.session["user_group"][0]
    data = CapacityData.objects.get(pk=pk)

    closed_date = datetime.now()
    ''' create updated ticket data in history table'''
    history_data_create = HistoryData.objects.create(
        request_id=data.request_id,
        updated_time=closed_date,
        data_center=data.data_center,
        project_name=data.project_name,
        user_id=data.user_id,
        std_stable1=data.std_stable1,
        std_stable2=data.std_stable2,
        std_arbor=data.std_arbor,
        stable1=data.stable1,
        stable2=data.stable2,
        arbor=data.arbor,
        gravit=data.gravit,
        move_group_name=data.move_group_name,
        remarks=data.remarks,
        tkt_status="Completed",
    )
    history_data_create.save()  # saving the record in the table
    time.sleep(1)
    '''after updating into history table deleting record from capacity table'''
    data.delete()
    if "admin" in user_group:
        return HttpResponseRedirect(reverse("admin_view_request"))
    else:
        return HttpResponseRedirect(reverse("view_request"))


@csrf_exempt
@login_required
def reject_request(request, pk):
    """ fetch the record the table based on pk"""
    user_group = request.session["user_group"][0]
    data = CapacityData.objects.get(pk=pk)

    closed_date = datetime.now()
    ''' create updated ticket data in history table'''
    history_data_create = HistoryData.objects.create(
        request_id=data.request_id,
        updated_time=closed_date,
        data_center=data.data_center,
        project_name=data.project_name,
        user_id=data.user_id,
        std_stable1=data.std_stable1,
        std_stable2=data.std_stable2,
        std_arbor=data.std_arbor,
        stable1=data.stable1,
        stable2=data.stable2,
        arbor=data.arbor,
        gravit=data.gravit,
        move_group_name=data.move_group_name,
        remarks=data.remarks,
        tkt_status="Rejected",
    )
    history_data_create.save()  # saving the record in the table
    time.sleep(1)
    '''after updating into history table deleting record from capacity table'''
    data.delete()

    if "admin" in user_group:
        return HttpResponseRedirect(reverse("admin_view_request"))
    else:
        return HttpResponseRedirect(reverse("view_request"))


@login_required
def history_request(request):
    user_group = request.session["user_group"][0]
    project = request.session["user_group"][1]
    email = request.session["user_group"][3]
    data = ProjectPlannerHistoryData.objects.filter(project_name=project[0])
    return render(request, 'capacity_app/history_request.html', {"data": data, "user_group": user_group,
                                                                 "email": email})


@login_required
def completeticketdata(request):
    user_group = request.session["user_group"][0]
    user_name = request.session["user_group"][2]
    email = request.session["user_group"][3]

    data = HistoryData.objects.filter(user_id=user_name)
    return render(request, 'capacity_app/completed_request.html', {"data": data, "user_group": user_group,
                                                                       "email": email})


@csrf_exempt
@login_required
def project_create_request(request):

    if request.method == "POST":
        data_center = request.POST['dc']
        project_name = request.POST['project']
        user_id = request.POST['user_id']
        milestone_name = request.POST.getlist('mytext[]')
        milestone_date = request.POST.getlist('mytext2[]')
        std_stable1 = request.POST['std_stable1']
        std_stable2 = request.POST['std_stable2']
        std_arbor = request.POST['std_arbor']
        stable1 = request.POST['stable1']
        stable2 = request.POST['stable2']
        arbor = request.POST['arbor']
        gravit = request.POST['gravit']
        remarks = request.POST['remarks']

        request_id = project_name[0:3] + "_" + str(int(time.time() * 1000))

        # creating the project plans
        query_data = ProjectPlannerData.objects.create(
            data_center=data_center,
            project_name=project_name,
            user_name=user_id,
            milestone_name=str(milestone_name),
            date=milestone_date,
            std_stable1=int(std_stable1),
            std_stable2=int(std_stable2),
            std_arbor=int(std_arbor),
            stable1=int(stable1),
            stable2=int(stable2),
            arbor=int(arbor),
            gravit=gravit,
            remarks=remarks,
            financial_approval=False,
            procurement_approval=False,
            request_id=request_id
        )
        query_data.save()

        # # storing milestone data
        for i in range(len(milestone_name)):
            milestone_data = MilestoneData.objects.create(
                name=milestone_name[i],
                date=milestone_date[i],
                project_name=project_name
            )
            milestone_data.save()

        return HttpResponseRedirect(reverse("project_view_request"))

    else:
        user_group = request.session["user_group"][0]
        projects = request.session["user_group"][1]
        email = request.session["user_group"][3]
        query_set = ProjectPlannerData.objects.filter(project_name=projects[0])

        if len(query_set) > 0:
            return HttpResponseRedirect(reverse("project_view_request"))
        else:
            if "admin" not in user_group:
                query_set = ProjectPlannerData.objects.filter(project_name=projects[0], financial_approval=True, procurement_approval=True)
                return render(request, 'capacity_app/project_create_request.html',
                            {"projects": projects, "user_group": user_group, "email": email, "query_set": query_set})
            else:
                pass


@csrf_exempt
@login_required
def project_view_request(request):
    user_group = request.session["user_group"][0]
    email = request.session["user_group"][3]
    project = request.session["user_group"][1]

    if "admin" not in user_group:
        query_set = ProjectPlannerData.objects.filter(project_name=project[0])
        query_set1 = ProjectPlannerData.objects.filter(project_name=project[0], financial_approval=True,
                                                       procurement_approval=True)

        mile_stone_data = MilestoneData.objects.filter(project_name=project[0])
        return render(request, 'capacity_app/project_view_request.html',
                    {"user_group": user_group, "email": email, "data": query_set, "query_data": query_set1,
                     "mile_stone": mile_stone_data})


@login_required
def financial_approval(request):
    email = request.session["user_group"][3]
    query_set = ProjectPlannerData.objects.filter(financial_approval=False)
    mile_stone_data = MilestoneData.objects.all()
    return render(request, 'capacity_app/financial_approval.html', {"email": email, "mile_stone": mile_stone_data,
                                                                    "data": query_set})


@login_required
def completed_financial_approval(request, pk):

    print(pk)
    """ storing approved record in table"""
    data = ProjectPlannerData.objects.get(request_id=pk)

    create_record = FinanceProcurementApprovalData.objects.create(
        data_center=data.data_center,
        project_name=data.project_name,
        group="finance",
        milestone_name=data.milestone_name,
        date=data.date,
        std_stable1=data.std_stable1,
        std_stable2=data.std_stable2,
        std_arbor=data.std_arbor,
        stable1=data.stable1,
        stable2=data.stable2,
        arbor=data.arbor,
        gravit=data.gravit,
        remarks=data.remarks,
        user_name=data.user_name,
        request_id=data.request_id
    )
    create_record.save()

    """ updating the new vales in table """
    ProjectPlannerData.objects.filter(request_id=pk).update(financial_approval=True)

    return HttpResponseRedirect(reverse("financial_completed_request"))


@login_required
def financial_completed_request(request):
    email = request.session["user_group"][3]
    query_set = FinanceProcurementApprovalData.objects.filter(group="finance")
    mile_stone_data = MilestoneData.objects.all()
    return render(request, 'capacity_app/finance_completed.html', {"email": email, "mile_stone": mile_stone_data, "data": query_set})


@login_required
def procurement_approval(request):
    email = request.session["user_group"][3]
    query_set = ProjectPlannerData.objects.filter(financial_approval=True, procurement_approval=False)
    mile_stone_data = MilestoneData.objects.all()
    return render(request, 'capacity_app/procurement_approval.html', {"email": email, "data": query_set, "mile_stone": mile_stone_data})


@login_required
def completed_procurement_approval(request, pk):
    data = ProjectPlannerData.objects.get(request_id=str(pk))

    """ storing approved record in table"""

    create_record = FinanceProcurementApprovalData.objects.create(
        data_center=data.data_center,
        project_name=data.project_name,
        group="procurement",
        milestone_name=data.milestone_name,
        date=data.date,
        std_stable1=data.std_stable1,
        std_stable2=data.std_stable2,
        std_arbor=data.std_arbor,
        stable1=data.stable1,
        stable2=data.stable2,
        arbor=data.arbor,
        gravit=data.gravit,
        remarks=data.remarks,
        user_name=data.user_name,
        request_id=data.request_id
    )
    create_record.save()

    """ updating the new vales in table """
    ProjectPlannerData.objects.filter(request_id=str(pk)).update(procurement_approval=True)

    return HttpResponseRedirect(reverse("procurement_completed_request"))


@login_required
def procurement_completed_request(request):
    email = request.session["user_group"][3]
    query_set = FinanceProcurementApprovalData.objects.filter(group="procurement")
    mile_stone_data = MilestoneData.objects.all()
    return render(request, 'capacity_app/procurement_completed_request.html', {"email": email,"data": query_set,
                                                                               "mile_stone": mile_stone_data})


@login_required
def admin_view_request(request):
    email = request.session["user_group"][3]
    data = CapacityData.objects.all()
    return render(request, 'capacity_app/admin_view_request.html', {"email": email, "data": data})


@login_required
def admin_completed_request(request):
    email = request.session["user_group"][3]
    data = HistoryData.objects.all()
    return render(request, 'capacity_app/admin_completed_request.html', {"email": email, "data": data})