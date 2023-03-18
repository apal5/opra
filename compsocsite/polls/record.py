import datetime
import os
import csv

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest, JsonResponse
from django.urls import reverse
from django.views import generic
from django.core.files import File
from .models import *
from django.core.exceptions import ObjectDoesNotExist

from django.utils import timezone
from django.template import RequestContext
from django.shortcuts import render
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.core import mail
from groups.models import *
from django.conf import settings
import random
import string
import json

def writeUserAction(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if request.method == 'POST':
        #session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        #str = "/log/" + request.user.username + "_" + session_key + ".txt"
        #f = open(str, 'w+')
        type = 0
        data = request.POST['data']
        order1 = request.POST['order1']
        device = request.POST['device']
        final = request.POST['final']
        commentTime = request.POST['commentTime']
        swit = request.POST['swit']
        init = order1
        UI = request.POST['ui']
        submit_time = request.POST['submit_time']
        #print(slider_record)
        if request.user.username == "":
            anonymous_name = ""
            new_name = "(Anonymous)" + anonymous_name
            r = UserVoteRecord(timestamp=timezone.now(),user=new_name,col=data,question=question,initial_order=init,final_order=final,device=device,initial_type=type,comment_time=commentTime,swit=swit,submit_time=submit_time,ui=UI)
            r.save()
        else:
            r = UserVoteRecord(timestamp=timezone.now(),user=request.user.username,col=data,question=question,initial_order=init,final_order=final,device=device,initial_type=type,comment_time=commentTime,swit=swit,submit_time=submit_time,ui=UI)
            r.save()
        #f.close()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    
# download all data from database, only initial and final rankings
# allow self-sign-up to groups


def interpretRecordForDownload(record):
    order = record.initial_order
    r = record.record
    title_arr = []
    record_arr = []
    if r != "":
        action_arr = r.split(";;;")
        title_arr.append(record.user)
        title_arr.append(str(record.question.id))
        title_arr.append(str(record.timestamp))
        if record.initial_order == "":
            title_arr.append("Last user's vote order")
        else:
            title_arr.append(order)
        title_arr.append(record.device)
        for str1 in action_arr:
            each_record = []
            if str1.find(";;") != -1:
                pair = str1.split(";;")
                if len(pair) == 2:
                    t1 = pair[0].split("::")
                    t2 = pair[1].split("::")
                    t1[2] = t1[2][4:]
                    t2[2] = t2[2][4:]
                    if t1[1] == "start":
                        each_record.append("Drag")
                        str2 = ""
                        item_arr = t2[3].split("||")
                        each_record.append(t1[0])
                        each_record.append(t1[3])
                        each_record.append(t2[0])
                        each_record.append(item_arr[0])
                        for index in range(1,len(item_arr)):
                            if(item_arr[index] != ""):
                                str2 += item_arr[index][4:] + ", "
                        each_record.append(str2)
                    else:
                        each_record.append("Click")
                        each_record.append(t1[0])
                        each_record.append(t1[3])
                        each_record.append(t2[0])
                        each_record.append(t2[3])
            else:
                if len(str1) != 0:
                    if str1[0] == "S":
                        each_record.append("Submit")
                        each_record.append(str1[1:])
                    elif str1.find("||") == -1:
                        each_record.append("Move All")
                        each_record.append(str1)
                    else:
                        str2 = ""
                        clear_arr = str1.split("||")
                        each_record.append("Clear All")
                        each_record.append(clear_arr[0])
                        each_record.append("")
                        each_record.append("")
                        each_record.append("")
                        for i in range(1,len(clear_arr)):
                            str2 += clear_arr[i][4:] + "; "
                        each_record.append(str2)
            record_arr.append(each_record)
    return (title_arr,record_arr)
    
def interpretRecord(record):
    order = record.initial_order
    r = record.record
    record_arr = []
    if r != "":
        action_arr = r.split(";;;")
        temp = ""
        temp += record.user + " voted at " + str(record.timestamp) + "\n"
        if order != "":
            temp += "\nInitial order: " + order
        if record.initial_type == 0:
            temp += "  (recommended order)"
        else:
            temp += "  (User's last vote order)"
        record_arr.append(temp)
        record_arr.append(record.device)
        for str1 in action_arr:
            if str1.find(";;") != -1:
                pair = str1.split(";;")
                if len(pair) == 2:
                    t1 = pair[0].split("::")
                    t2 = pair[1].split("::")
                    t1[2] = t1[2][4:]
                    t2[2] = t2[2][4:]
                    if t1[1] == "start":
                        str2 = ""
                        item_arr = t2[3].split("||")
                        str2 += "Moved item " + t1[2] + " from tier " + t1[3] + " to tier " + item_arr[0] + " at time " + t1[0] + ", tier " + item_arr[0] + " has items: "
                        for index in range(1,len(item_arr)):
                            if(item_arr[index] != ""):
                                str2 += item_arr[index][4:] + ", "
                        record_arr.append(str2)
                    else:
                        str2 = ""
                        str2 += "Clicked item " + t1[2] + " on the right at tier " +t1[3] + " and moved it to tier " + t2[3] + " on the left at time " + t1[0] + "."
                        record_arr.append(str2)
            else:
                if len(str1) != 0:
                    if str1[0] == "S":
                        str2 = "Clicked submit at time " + str1[1:] + "."
                        record_arr.append(str2)
                    elif str1.find("||") == -1:
                        str2 = "Clicked move all at time " + str1 + "."
                        record_arr.append(str2)
                    else:
                        clear_arr = str1.split("||")
                        str2 = "Clicked clear at time " + clear_arr[0] + ", order on the right is: "
                        for i in range(1,len(clear_arr)):
                            str2 += clear_arr[i][4:] + "; "
                        record_arr.append(str2)
    else:
        temp = ""
        temp += record.user + " voted at " + str(record.timestamp) + "\n"
        if order != "":
            temp += "\nInitial order: " + order
        if record.initial_type == 0:
            temp += "  (recommended order)"
        else:
            temp += "  (User's last vote order)"
        record_arr.append(temp)
        record_arr.append(record.device)
        record_arr.append(record.col)
    if record.slider != "":
        record_arr.append(record.one_col)
        record_arr.append(record.slider)
        record_arr.append(record.star)
        record_arr.append(record.swit)
    return record_arr
    
def interpretRecord1(record):
    init = record.initial_order
    if len(init) > 0 and init[len(init)-1] == "":
        init = init[0:len(init)-1]
    final = record.final_order
    t = ""
    if record.record != "":
        action_arr = record.record.split(";;;")
        t = action_arr[len(action_arr)-1][1:]
    else:
        r = json.loads(record.col)
        t = r["submit"]["time"]
    type = str(record.initial_type)
    result = []
    result.append(str(record.question.id))
    result.append(record.user)
    result.append(t)
    result.append(init)
    result.append(type)
    result.append(final)
    result.append(record.comment_time)
    return result
    
def interpretSliderStar(record):
    slider = json.dumps(record.slider)
    star = json.dumps(record.star)
    return (slider)
    
def downloadRecord(request, question_id):
    response = HttpResponse(content_type='text/csv')
    question = get_object_or_404(Question,pk=question_id)
    records = question.uservoterecord_set.all()
    response['Content-Disposition'] = 'attachment; filename="record.csv"'
    writer = csv.writer(response)
    for r in records:
        (data,time) = interpretRecordForLearning(r)
        writer.writerow(data)
    return response

def downloadAllRecord(request, user_id):
    user = get_object_or_404(User,pk=user_id)
    response = HttpResponse(content_type='text/csv')
    records = []
    response['Content-Disposition'] = 'attachment; filename="all_record.csv"'
    writer = csv.writer(response)
    for question in user.question_set.order_by('id'):
        for record in question.uservoterecord_set.all():
            writer.writerow(interpretRecord1(record))
        writer.writerow([])
    return response
    
def downloadAllRecord1(request, user_id):
    user = get_object_or_404(User,pk=user_id)
    response = HttpResponse(content_type='text/csv')
    records = []
    response['Content-Disposition'] = 'attachment; filename="record.csv"'
    writer = csv.writer(response)
    writer.writerow(["Username","Question id","Timestamp","Initial order"])
    for question in user.question_set.order_by('id'):
        for record in question.uservoterecord_set.all():
            (title_arr,record_arr) = interpretRecordForDownload(record)
            writer.writerow(title_arr)
            writer.writerow(["Action type","Start time","Start tier","Stop time","Stop tier","Final order"])
            for r in record_arr:
                writer.writerow(r)
            writer.writerow([])
    return response
            
    
    
class RecordView(generic.DetailView):
    model = Question
    template_name = 'polls/record.html'
    
    def get_context_data(self, **kwargs):
        ctx = super(RecordView, self).get_context_data(**kwargs)
        records = self.object.response_set.all()
        interpreted_records = []
        for r in records:
            interpreted_records.append(r.behavior_data)
        ctx['user_records'] = interpreted_records
        return ctx

def interpretRecordForLearning(record):
    record_time = record.timestamp
    record_user = record.user
    record_device = record.device
    col_dict = json.loads(record.col)
    one_col_dict = json.loads(record.one_col)
    slider_dict = json.loads(record.slider)
    star_dict = json.loads(record.star)
    submit_time = "0"
    for item in col_dict["two_column"]:
        if item["action"] == "submit":
            submit_time = item["time"]
    for item in one_col_dict["one_column"]:
        if item["action"] == "submit":
            submit_time = item["time"]
    switch_list = []
    if record.swit != "":
        temp_switch_list = record.swit.split(";;")
        for item in temp_switch_list:
            if item != "":
                each_list = item.split(";")
                temp_dict = {}
                temp_dict["action"] = "switch"
                if len(each_list) > 2:
                    temp_dict["time"] = each_list[0]
                    temp_dict["from"] = each_list[1]
                    temp_dict["to"] = each_list[2]
                else:
                    temp_dict["time"] = each_list[0]
                    temp_dict["to"] = each_list[1]
                switch_list.append(temp_dict)
    total_order = []
    total_order.extend(col_dict["two_column"])
    total_order.extend(one_col_dict["one_column"])
    total_order.extend(slider_dict["slider"])
    total_order.extend(star_dict["star"])
    total_order.extend(switch_list)
    sorted_order = sorted(total_order, key=lambda k: k["time"])
    final_list = []
    final_list.append(record_user)
    final_list.append(record_device)
    final_list.append(record_time)
    final_list.append(submit_time)
    final_list.extend(total_order)
    return (final_list, submit_time)
    
def downloadParticipants(request):
    all_par = User.objects.filter(userprofile__mturk=1)
    result = []
    for par in all_par:
        dic = {}
        dic["user_id"] = par.id
        dic["username"] = par.username
        dic["time_creation"] = par.userprofile.time_creation
        dic["age"] = par.userprofile.age
        dic["survey_code"]=par.userprofile.code
        dic["poll_seq"]=par.userprofile.sequence
        dic["current_poll"] = par.userprofile.cur_poll
        result.append(dic)
    return JsonResponse(result, safe=False)
    
def downloadPolls(request):
    all_poll = User.objects.get(username="opraexp").question_set.all()
    result = []
    for poll in all_poll:
        dic = {}
        dic["id"] = poll.id
        dic["title"] = poll.question_text
        dic["time_creation"] = str(poll.pub_date)
        dic["UI"] = getUIs(poll)
        dic["description"] = poll.question_desc
        dic["alternatives"] = list(poll.item_set.all().values_list("item_text",flat=True))
        result.append(dic)
    return JsonResponse(result, safe=False)
    
def downloadRecords(request):
    all_record = UserVoteRecord.objects.all()
    result = []
    for record in all_record:
        dic = {}
        dic["vote_id"] = record.id
        dic["poll_id"] = record.question.id
        dic["user_id"] = 0
        try:
            user = User.objects.get(username=record.user)
            dic["user_id"] = user.id
        except ObjectDoesNotExist:
            pass
        dic["data"] = json.loads(record.col)
        dic["platform"] = record.device
        dic["UI"] = getUIs(record.question)
        try:
            dic["initial_ranking"] = json.loads(record.initial_order)
        except ValueError:
            dic["initial_ranking"] = []
        try:
            dic["submitted_ranking"] = json.loads(record.final_order)
        except ValueError:
            dic["submitted_ranking"] = []
        dic["timestamp_submission"] = str(record.timestamp)
        dic["time_submission"] = record.submit_time
        result.append(dic)
    return JsonResponse(result, safe=False)

def downloadSpecificRecords(request):
    all_responses = []
    result = []
    polls = getMturkPollID()
    for poll in polls:
        all_responses += list(get_object_or_404(Question,pk=poll).response_set.filter(active=1,timestamp__gt=datetime.datetime(2018,5,17,23,30)))
    for resp in all_responses:
        dic = {}
        try:
            dic = json.loads(resp.behavior_data)
        except ValueError:
            dic = {}
        dic["UI"] = getUIs(resp.question)
        dic["vote_id"] = resp.id
        dic["poll_id"] = resp.question.id
        dic["timestamp_submission"] = str(resp.timestamp)
        if hasattr(resp, 'user'):
            dic["user_id"] = resp.user.id
        else:
            dic["user_id"] = 0
        result.append(dic)
    return JsonResponse(result, safe=False)
        


def getMturkPollID():
    polls = list(range(180,190))
    return polls

def getUIs(poll):
    result = []
    if poll.twocol_enabled:
        result.append("two_column")
    if poll.onecol_enabled:
        result.append("one_column")
    if poll.slider_enabled:
        result.append("slider")
    if poll.star_enabled:
        result.append("star")
    if poll.yesno_enabled:
        result.append("yesno")
    if poll.yesno2_enabled:
        result.append("yesno_grid")
    return result
    