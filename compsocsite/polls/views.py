from .models import *
from appauth.models import *
from groups.models import *
import datetime
import os
import time
import collections

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.urls import reverse
from django import views
from django.db.models import Q

from django.utils import timezone
from django.template import RequestContext
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core import mail
from prefpy.mechanism import *
from prefpy.allocation_mechanism import *
from prefpy.gmm_mixpl import *
from prefpy.egmm_mixpl import *
from .email import EmailThread, setupEmail
from django.conf import settings
from multipolls.models import *

from . import opra_crypto
import json
import threading
import itertools
import numpy as np
import random
import csv

class IndexView(views.generic.ListView):
    """
    Define homepage view, inheriting ListView class, which specifies a context variable.
    
    Note that login is required to view the items on the page.
    """
    
    template_name = 'polls/index2.html'
    context_object_name = 'question_list'
    def get_queryset(self):
        """Override function in parent class and return all questions."""
        
        return Question.objects.all().order_by('-pub_date')


class RegularPollsView(views.generic.ListView):
    """
    Define regular polls view, inheriting ListView class, which specifies a context variable.
    
    The variables used in regular polls page are extracted from database and defined below.
    """
    
    template_name = 'polls/regular_polls.html'
    context_object_name = 'question_list'
    def get_queryset(self):
        """Override function in parent class and return all questions."""
        
        return Question.objects.all().order_by('-pub_date')
        
    
    def get_context_data(self, **kwargs):
        """Override function in parent class and define additional context variables to be used in the page."""
        
        
        ctx = super(RegularPollsView, self).get_context_data(**kwargs)
        # get folders
        ctx['folders'] = Folder.objects.filter(user=self.request.user).all()
        unshown = []
        for folder in ctx['folders']:
            unshown += folder.questions.all()
        
        # sort the lists by date (most recent should be at the top)
        ctx['polls_created'] = list(Question.objects.filter(question_owner=self.request.user,
                                                       m_poll=False).order_by('-pub_date'))
        # get all polls current user participates in and filter out those she is the owner of
        polls = self.request.user.poll_participated.filter(m_poll=False)
        polls = polls.exclude(question_owner=self.request.user).order_by('-pub_date')
        ctx['polls_participated'] = list(polls)
        
        # for polls in folders, do not show them in the main page
        for poll in unshown:
            if poll in ctx['polls_created']:
                ctx['polls_created'].remove(poll)
            elif poll in ctx['polls_participated']:
                ctx['polls_participated'].remove(poll)
        return ctx

class RegularPollsFolderView(views.generic.DetailView):
    """Define folder view, inheriting DetailView class, which specifies a specific object."""
    
    template_name = 'polls/regular_polls_folder.html'
    model = Folder
    
    def get_context_data(self, **kwargs):
        """Override function in parent class and define additional context variables to be used in the page."""
        
        ctx = super(RegularPollsFolderView, self).get_context_data(**kwargs)
        ctx['polls_folder'] = self.object.questions.all()
        return ctx


def reverseListOrder(query):
    """Reverse the order in a list."""
    
    list_query = list(query)
    list_query.reverse()
    return list_query

class MultiPollsView(views.generic.ListView):
    """Define multi-poll view, inheriting ListView class, which specifies a context variable. """
    template_name = 'polls/m_polls.html'
    context_object_name = 'question_list'
    def get_queryset(self):
        """Override function in parent class and return all questions."""
        
        return Question.objects.all()
    
    def get_context_data(self, **kwargs):
        """Override function in parent class and define additional context variables to be used in the page."""
        
        ctx = super(MultiPollsView, self).get_context_data(**kwargs)
        # sort the list by date
        m_polls = MultiPoll.objects.filter(owner=self.request.user)
        m_polls_part = self.request.user.multipoll_participated.exclude(owner=self.request.user)
        ctx['multipolls_created'] = reverseListOrder(m_polls)
        ctx['multipolls_participated'] = reverseListOrder(m_polls_part)
        return ctx


class MainView(views.generic.ListView):
    """Define homepage for users that have not logged in."""
    
    template_name = 'polls/index.html'
    context_object_name = 'question_list'
    
    def get_queryset(self):
        """Override function in parent class and return all questions."""
        
        return Question.objects.all().order_by('-pub_date')

    def get_context_data(self, **kwargs):
        """Override function in parent class and define additional context variables to be used in the page."""
        
        ctx = super(MainView, self).get_context_data(**kwargs)
        # sort the list by date
        ctx['preference'] = 1
        ctx['poll_algorithms'] = getListPollAlgorithms()
        ctx['alloc_methods'] = getAllocMethods()
        ctx['view_preferences'] = getViewPreferences()

        return ctx


class DemoView(views.generic.DetailView):
    """Define demo poll, which is not used. Need more work on this."""
    
    model = Question
    template_name = 'polls/demo.html'

    def get_order(self, ctx):
        other_user_responses = self.object.response_set.reverse()
        default_order = ctx['object'].item_set.all()
        #random.shuffle(default_order)
        return default_order
        #return getRecommendedOrder(other_user_responses, self.request, default_order)

    def get_context_data(self, **kwargs):
        ctx = super(DemoView, self).get_context_data(**kwargs)
        ctx['items'] = self.get_order(ctx)
        return ctx
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class GMView(views.generic.ListView):
    """Define poll main page for GM week 2017."""
    
    template_name = 'events/GM2017/GM2017.html'
    context_object_name = 'question_list'
    def get_queryset(self):
        return Question.objects.all()
    def get_context_data(self, **kwargs):
        ctx = super(GMView, self).get_context_data(**kwargs)
        ctx['winners'] = getWinnersFromIDList(getGMPollIDLIst())
        return ctx

        
class GMResultsView(views.generic.ListView):
    """Define result page for GM week 2017."""

    template_name = 'events/GM2017/GM2017results.html'
    context_object_name = 'question_list'
    def get_queryset(self):
        return Question.objects.all()
    def get_context_data(self, **kwargs):
        ctx = super(GMResultsView, self).get_context_data(**kwargs)
        ctx['winners'] = getWinnersFromIDList(getGMPollIDLIst())
        return ctx


class CSPosterView(views.generic.ListView):
    """Define CS Poster page."""
    
    template_name = 'events/CSposter/CSposter.html'
    context_object_name = 'question_list'
    def get_queryset(self):
        return Question.objects.all()
    def get_context_data(self, **kwargs):
        ctx = super(CSPosterView, self).get_context_data(**kwargs)
        return ctx


def AddStep1View(request):
    """
    Define the first step in creating poll.
    
    Obtain title, description, type, allowing tie, and image from POST of HTTP request.
    Redirects to add step 1 page if request does not contain POST, go to add step 2 otherwise.
    """
    context = RequestContext(request)
    if request.method == 'POST':
        questionString = request.POST['questionTitle']
        questionDesc = request.POST['desc']
        questionType = request.POST['questiontype']
        imageURL = request.POST['imageURL']
        tie=False
        t = request.POST.getlist('allowties')
        if "1" in t:
            tie = True
        if "2" in t:
            tie = False

        # create a new question using information from the form and inherit
        # settings from the user's preferences
        question = Question(question_text=questionString, question_desc=questionDesc,
                            pub_date=timezone.now(), question_owner=request.user,
                            display_pref=request.user.userprofile.displayPref,
                            emailInvite=request.user.userprofile.emailInvite,
                            emailDelete=request.user.userprofile.emailDelete,
                            emailStart=request.user.userprofile.emailStart,
                            emailStop=request.user.userprofile.emailStop, creator_pref=1,allowties = tie)
        if request.FILES.get('docfile') != None:
            question.image = request.FILES.get('docfile')
        elif imageURL != '':
            question.imageURL = imageURL
        question.question_type = questionType
        
        question.save()
        setupEmail(question)
        return HttpResponseRedirect(reverse('polls:AddStep2', args=(question.id,)))
    return render(request,'polls/add_step1.html', {})


class AddStep2View(views.generic.DetailView):
    """Define step 2 in creating poll: adding choices."""
    
    model = Question
    template_name = 'polls/add_step2.html'
    def get_context_data(self, **kwargs):
        ctx = super(AddStep2View, self).get_context_data(**kwargs)
        ctx['items'] = self.object.item_set.all()
        return ctx
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())


class AddStep3View(views.generic.DetailView):
    """Defind step 3 in creating poll: inviting voters."""

    model = Question
    template_name = 'polls/add_step3.html'
    def get_context_data(self, **kwargs):
        ctx = super(AddStep3View, self).get_context_data(**kwargs)
        ctx['users'] = User.objects.all()
        ctx['groups'] = Group.objects.all()
        return ctx
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())


class AddStep4View(views.generic.DetailView):
    """Define step 4 in creating poll: privacy setting, voting mechanisms, voting UIs, etc."""
    
    model = Question
    template_name = 'polls/add_step4.html'
    def get_context_data(self, **kwargs):
        ctx = super(AddStep4View, self).get_context_data(**kwargs)
        ctx['preference'] = self.request.user.userprofile.displayPref
        ctx['poll_algorithms'] = getListPollAlgorithms()
        ctx['alloc_methods'] = getAllocMethods()
        ctx['view_preferences'] = getViewPreferences()
        return ctx
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


def addChoice(request, question_id):
    """
    Called when the "+" for adding choice is pressed.
    
    Submitted data must satisfy:
        - cannot be empty
        - cannot contain exactly same text as choices already added
    Image is optional.
    """

    question = get_object_or_404(Question, pk=question_id)
    item_text = request.POST['choice']
    imageURL = request.POST['imageURL']

    # check for empty strings
    if item_text == "":
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # check for duplicates
    allChoices = question.item_set.all()
    for choice in allChoices:
        if item_text == choice.item_text:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    # for cases of adding new alternative when poll is paused
    recentlyAdded = False
    if question.status == 4:
        recentlyAdded = True
    # create the choice
    item = Item(question=question, item_text=item_text, timestamp=timezone.now(),
                recently_added=recentlyAdded)

    # if the user uploaded an image or set a URL, add it to the item
    if request.FILES.get('docfile') != None:
        item.image = request.FILES.get('docfile')
    elif imageURL != '':
        item.imageURL = imageURL
    
    # save the choice
    item.save()
    request.session['setting'] = 0
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def editChoice(request, question_id):
    """Called when choice title or description is edited in poll info page."""
    
    question = get_object_or_404(Question, pk=question_id)
    for item in question.item_set.all():
        # get data from POST request
        new_text = request.POST["item"+str(item.id)]
        item_desc = request.POST["itemdescription"+str(item.id)]
        imageURL = request.POST["imageURL"+str(item.id)]
        # update choice info accordingly
        if item_desc != "":
            item.item_description = item_desc
        if request.FILES.get("docfile"+str(item.id)) != None:
            item.image = request.FILES.get("docfile"+str(item.id))
        elif imageURL != "":
            item.imageURL = imageURL
        item.item_text = new_text
        item.save()
    request.session['setting'] = 0
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def editBasicInfo(request, question_id):
    """
    Called in basic info tab in poll info page when saving changes.
    
    Updates title, description, available voting UIs, and whether ties are allowed.
    """
    
    question = get_object_or_404(Question, pk=question_id)
    # update title and description
    new_title = question.question_text
    if "title" in request.POST:
        new_title = request.POST["title"]
    new_desc = question.question_desc
    if "desc" in request.POST:
        new_desc = request.POST["desc"]
    question.question_text = new_title
    question.question_desc = new_desc
    
    # update UIs
    twocol = False
    onecol = False
    slider = False
    star = False
    yesno = False
    yesno2 = False
    uilist = request.POST.getlist('ui')
    if "twocol" in uilist:
        twocol = True
    if "onecol" in uilist:
        onecol = True
    if "slider" in uilist:
        slider = True
    if "star" in uilist:
        star = True
    if "yesno" in uilist:
        yesno = True
    if "yesno2" in uilist:
        yesno2 = True
    question.twocol_enabled = twocol
    question.onecol_enabled = onecol
    question.slider_enabled = slider
    question.star_enabled = star
    question.yesno_enabled = yesno
    question.yesno2_enabled = yesno2
    question.ui_number = twocol+onecol+slider+star+yesno+yesno2
    
    # update whether ties are allowed
    tie=question.allowties
    t = request.POST.getlist('allowties')
    if "1" in t:
        tie = True
    if "2" in t:
        tie = False

    question.allowties = tie
    
    # save the changes
    question.save()
    request.session['setting'] = 8
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def deleteChoice(request, choice_id):
    """Delete a choice; can only be done before a poll starts."""
    
    item = get_object_or_404(Item, pk=choice_id)
    item.delete()
    request.session['setting'] = 0
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def deletePoll(request, question_id):
    """Delete a poll. Only poll owner can do this."""
    
    question = get_object_or_404(Question, pk=question_id)

    # check to make sure the current user is the owner
    if request.user != question.question_owner:
        return HttpResponseRedirect(reverse('polls:index'))

    question.delete()
    return HttpResponseRedirect(reverse('polls:index'))


def quitPoll(request, question_id):
    """Voter opts out of a poll."""
    
    question = get_object_or_404(Question, pk=question_id)

    # notify the user if this option is checked
    if request.user.userprofile.emailDelete:
        email_class = EmailThread(request, question_id, 'remove')
        email_class.start()

    # remove from the voter list
    question.question_voters.remove(request.user)
    question.save()

    return HttpResponseRedirect(reverse('polls:regular_polls'))


def startPoll(request, question_id):
    """
    Called when poll owner starts a poll.
    
    After a poll starts, voters can vote at any time.
    However, poll owner cannot remove choices any more.
    """
    
    question = get_object_or_404(Question, pk=question_id)

    # check to make sure the owner started the poll
    if request.user != question.question_owner:
        return HttpResponseRedirect(reverse('polls:index'))

    # set the poll to start
    question.status = 2
    question.save()

    # send notification email
    if question.emailStart:
        email_class = EmailThread(request, question_id, 'start')
        email_class.start()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def pausePoll(request, question_id):
    """
    Called when a poll is paused. 
    
    Owner can then add choices. Voters can no longer vote until poll resumes.
    """
    
    question = get_object_or_404(Question, pk=question_id)

    # check to make sure the owner paused the poll
    if request.user != question.question_owner:
        return HttpResponseRedirect(reverse('polls:index'))

    # set the status to pause
    question.status = 4
    # get winner or allocation, and save it
    if question.question_type == 1 and question.response_set.filter(active=1).count() >= 1: #poll
        (question.winner, question.mixtures_pl1, question.mixtures_pl2,
         question.mixtures_pl3) = getPollWinner(question)
    question.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def resumePoll(request, question_id):
    """Resume a poll from paused state."""
    
    question = get_object_or_404(Question, pk=question_id)

    # check to make sure the owner resumed the poll
    if request.user != question.question_owner:
        return HttpResponseRedirect(reverse('polls:index'))
    
    allItems = question.item_set.all()
    for item in allItems:
        if item.recently_added:
            item.recently_added = False
            item.save()
    # set the poll to start
    question.status = 2
    question.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def stopPoll(request, question_id):
    """
    Stop a poll.
    
    After the poll stops, voters cannot vote. Final results will be available.
    """
    
    question = get_object_or_404(Question, pk=question_id)

    # check to make sure the owner stopped the poll
    if request.user != question.question_owner:
        return HttpResponseRedirect(reverse('polls:index'))

    # set the status to stop
    question.status = 3
    # get winner or allocation, and save it
    if question.question_type == 1: #poll
        (question.winner, question.mixtures_pl1, question.mixtures_pl2,
         question.mixtures_pl3) = getPollWinner(question)
    elif question.question_type == 2: #allocation
        getFinalAllocation(question)
    question.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# find the winner(s) using the polling algorithm selected earlier
# Question question
# return String winnerStr
def getPollWinner(question):
    """
    Calculate winner of poll. 
    
    Parameter: Question object.
    Returns: string containing winner(s), mixture for k = 1, 2, 3.
    """
    
    all_responses = question.response_set.filter(active=1).order_by('-timestamp')
    (latest_responses, previous_responses) = categorizeResponses(all_responses)
    # Calculate results
    cand_map = getCandidateMapFromList(list(question.item_set.all()))
    (vote_results, mixtures_pl1, mixtures_pl2,
     mixtures_pl3) = getVoteResults(latest_responses, cand_map)
    index_vote_results = question.poll_algorithm - 1
    current_result = vote_results[index_vote_results]

    winnerStr = ""
    
    # Transform result data into JSON strings and save in database

    #item_set = getCandidateMap(latest_responses[0])
    for index, score in current_result.items():
        # index 5 uses Simplified Bucklin, where score is rank.
        #   A low score means it has a high rank (e.g. rank 1 > rank 2),
        #   so the best score is the minimum.
        # All other indices rank score from highest to lowest, so the best score would be
        #   the maximum.
        if ((score == min(current_result.values()) and index_vote_results == 5)
                or (score == max(current_result.values()) and index_vote_results != 5)):
            #add a comma to separate the winners
            if winnerStr != "":
                winnerStr += ", "
            #add the winner
            winnerStr += cand_map[index].item_text

    if hasattr(question, 'finalresult'):
        question.finalresult.delete()
    result = FinalResult(question=question, timestamp=timezone.now(),
                         result_string="", mov_string="", cand_num=question.item_set.all().count(),
                         node_string="", edge_string="", shade_string="")
    
    resultlist = []
    mov = getMarginOfVictory(latest_responses, cand_map)
    movlist = [str(i) for i in mov]
    for x in range(0, len(vote_results)):
        for key, value in vote_results[x].items():
            resultlist.append(str(value))
            # resultstr += str(value)
            # resultstr += ","
    # for x in range(0, len(mov)):
    #     movstr += str(mov[x])
    #     movstr += ","
    # resultstr = resultstr[:-1]
    # movstr = movstr[:-1]
    (nodes, edges) = parseWmg(latest_responses, cand_map)
    # for node in nodes:
    #     for k, v in node.items():
    #         nodestr += k + "," + str(v) + ";"
    #     nodestr += "|"
    # nodestr = nodestr[:-2]
    # for edge in edges:
    #     for k, v in edge.items():
    #         edgestr += k + "," + str(v) + ";"
    #     edgestr += "|"
    # edgestr = edgestr[:-2]
    shadevalues = getShadeValues(vote_results)
    # for x in shadevalues:
    #     for y in x:
    #         shadestr += y + ";"
    #     shadestr += "|"
    # shadestr = shadestr[:-2]
    result.result_string = json.dumps(resultlist)
    result.mov_string = json.dumps(movlist)
    result.node_string = json.dumps(nodes)
    result.edge_string = json.dumps(edges)
    result.shade_string = json.dumps(shadevalues)
    result.save()
    
    # Resets new vote flag so that result is not computed again
    if question.new_vote:
        question.new_vote = False
    question.winner = winnerStr
    question.mixtures_pl1 = json.dumps(mixtures_pl1)
    question.mixtures_pl2 = json.dumps(mixtures_pl2)
    question.mixtures_pl3 = json.dumps(mixtures_pl3)
    question.save()

    return winnerStr, json.dumps(mixtures_pl1), json.dumps(mixtures_pl2), json.dumps(mixtures_pl3)



def interpretResult(finalresult):
    """
    Interpret result into strings that can be shown on the result page.
    
    Parameter: FinalResult object
    Returns: list of list of String containing data used on result page.
    """
    
    candnum = finalresult.cand_num
    # resultstr = finalresult.result_string
    # movstr = finalresult.mov_string
    # shadestr = finalresult.shade_string
    # nodestr = finalresult.node_string
    # edgestr = finalresult.edge_string
    # resultlist = resultstr.split(",")
    # movlist = movstr.split(",")
    # tempResults = []
    # algonum = len(getListPollAlgorithms())
    # if len(resultlist) < candnum*algonum:
    #     algonum = 7
    # if len(resultlist) > 0:
    #     for x in range(0, algonum):
    #         tempList = []
    #         for y in range(x*candnum, (x+1)*candnum):
    #             tempList.append(resultlist[y])
    #         tempResults.append(tempList)
    # tempMargin = []
    # for margin in movlist:
    #     tempMargin.append(margin)
    # tempShades = []
    # shadelist = shadestr.split(";|")
    # for item in shadelist:
    #     tempShades.append(item.split(";"))
    # temp_nodes = []
    # nodelist = nodestr.split(";|")
    # for node in nodelist:
    #     data = {}
    #     l = node.split(";")
    #     for item in l:
    #         tup = item.split(",")
    #         data[tup[0]] = tup[1]
    #     temp_nodes.append(data)
    # tempEdges = []
    # edgelist = edgestr.split(";|")
    # if edgestr != "":
    #     for edge in edgelist:
    #         data = {}
    #         l = edge.split(";")
    #         for item in l:
    #             tup = item.split(",")
    #             data[tup[0]] = tup[1]
    #         tempEdges.append(data)
    resultlist = json.loads(finalresult.result_string)
    tempResults = []
    algonum = len(getListPollAlgorithms())
    if len(resultlist) < candnum*algonum:
        algonum = 7
    if len(resultlist) > 0:
        for x in range(0, algonum):
            tempList = []
            for y in range(x*candnum, (x+1)*candnum):
                tempList.append(resultlist[y])
            tempResults.append(tempList)
    tempMargin = json.loads(finalresult.mov_string)
    tempShades = json.loads(finalresult.shade_string)
    temp_nodes = json.loads(finalresult.node_string)
    tempEdges = json.loads(finalresult.edge_string)
    return [tempResults, tempMargin, tempShades, temp_nodes, tempEdges]


def recalculateResult(request, question_id):
    """Called when poll owner wants to recalculate result manually."""
    
    question = get_object_or_404(Question, pk=question_id)
    getPollWinner(question)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))



def isPrefReset(request):
    """Reset order in two-column UI. No longer used."""
    # reset link would have '?order=null' at the end
    orderStr = request.GET.get('order', '')
    if orderStr == "null":
        return True
    return False


def getCurrentSelection(mostRecentResponse):
    """
    Given a response, return current ranking data that can be loaded on voting UIs.
    
    Parameter: Response object.
    Returns: List<List<Item>>
    """
    responseDict = {}
    # if mostRecentResponse.dictionary_set.all().count() > 0:
        # responseDict = mostRecentResponse.dictionary_set.all()[0]
    # else:
    responseDict = buildResponseDict(mostRecentResponse, mostRecentResponse.question,
                                     getPrefOrder(mostRecentResponse.resp_str,
                                                  mostRecentResponse.question))
    rd = responseDict
    array = []
    for itr in range(mostRecentResponse.question.item_set.all().count()):
        array.append([])
    for itr in rd:
        if rd[itr] != 1000:
            array[rd[itr] - 1].append(itr)
    return array

def getUnrankedCandidates(resp):
    """Simiar to getCurrentSelection; gets unranked alternatives."""
    
    rd = buildResponseDict(resp, resp.question, getPrefOrder(resp.resp_str, resp.question))
    array = []
    for itr in rd:
        if rd[itr] == 1000:
            array.append(itr)
    if len(array) == 0:
        return None
    return array


class DetailView(views.generic.DetailView):
    """Define poll voting page view."""
    
    model = Question
    template_name = 'polls/detail.html'

    def get_order(self, ctx):
        """Define the initial order to be displayed on the page."""
        
        other_user_responses = self.object.response_set.reverse()
        default_order = list(ctx['object'].item_set.all())
        random.shuffle(default_order)
        return default_order
        #commented out to improve performance
        #return getRecommendedOrder(other_user_responses, self.request, default_order)

    def get_context_data(self, **kwargs):
        ctx = super(DetailView, self).get_context_data(**kwargs)
        ctx['lastcomment'] = ""

        #Case for anonymous user
        if self.request.user.get_username() == "":
            if isPrefReset(self.request):
                ctx['items'] = self.object.item_set.all()
                return ctx
            # check the anonymous voter
            if 'anonymousvoter' in self.request.session and 'anonymousid' in self.request.session:
                # sort the responses from latest to earliest
                anon_id = self.request.session['anonymousid']
                curr_anon_resps = self.object.response_set.filter(anonymous_id=anon_id).reverse()
                if len(curr_anon_resps) > 0:
                    # get the voter's most recent selection
                    mostRecentAnonymousResponse = curr_anon_resps[0]
                    if mostRecentAnonymousResponse.comment:
                        ctx['lastcomment'] = mostRecentAnonymousResponse.comment
                    ctx['currentSelection'] = getCurrentSelection(curr_anon_resps[0])
                    ctx['unrankedCandidates'] = getUnrankedCandidates(curr_anon_resps[0])
                    ctx['itr'] = itertools.count(1, 1)
                    items_ano = []
                    for item in ctx['currentSelection']:
                        for i in item:
                            items_ano.append(i)
                    if not ctx['unrankedCandidates'] == None:
                        for item in ctx['unrankedCandidates']:
                            items_ano.append(item)
                    ctx['items'] = items_ano
            else:
                # load choices in the default order
                ctx['items'] = self.object.item_set.all()
            return ctx

        # Get the responses for the current logged-in user from latest to earliest
        currentUserResponses = self.object.response_set.filter(user=self.request.user).reverse()

        if len(currentUserResponses) > 0:
            if currentUserResponses[0].comment:
                ctx['lastcomment'] = currentUserResponses[0].comment

        # reset button
        if isPrefReset(self.request):
            ctx['items'] = self.get_order(ctx)
            return ctx

        # check if the user submitted a vote earlier and display that for modification
        if len(currentUserResponses) > 0 and self.request.user.get_username() != "":
            ctx['currentSelection'] = getCurrentSelection(currentUserResponses[0])
            ctx['itr'] = itertools.count(1, 1)
            ctx['unrankedCandidates'] = getUnrankedCandidates(currentUserResponses[0])
            items = []
            for item in ctx['currentSelection']:
                for i in item:
                    items.append(i)
            if not ctx['unrankedCandidates'] == None:
                for item in ctx['unrankedCandidates']:
                    items.append(item)
            ctx['items'] = items
        else:
            # no history so display the list of choices
            ctx['items'] = self.get_order(ctx)
        return ctx
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

# view for settings detail
class PollInfoView(views.generic.DetailView):
    model = Question
    template_name = 'polls/pollinfo.html'
    def get_context_data(self, **kwargs):
        ctx = super(PollInfoView, self).get_context_data(**kwargs)
        emailInvite = Email.objects.filter(question=self.object, type=1)
        if len(emailInvite) == 1:
            setupEmail(self.object)
        if Email.objects.filter(question=self.object).count() > 0:
            ctx['emailInvite'] = Email.objects.filter(question=self.object, type=1)[0]
            ctx['emailDelete'] = Email.objects.filter(question=self.object, type=2)[0]
            ctx['emailStart'] = Email.objects.filter(question=self.object, type=3)[0]
            ctx['emailStop'] = Email.objects.filter(question=self.object, type=4)[0]
        ctx['users'] = User.objects.all()
        ctx['items'] = self.object.item_set.all()
        ctx['groups'] = Group.objects.all()
        ctx['poll_algorithms'] = getListPollAlgorithms()
        ctx['alloc_methods'] = getAllocMethods()
        twos = []
        for i in range(0, len(ctx['poll_algorithms'])):
            twos.append(2 ** i)
        ctx['twos'] = twos
        ctx['bools'] = self.object.vote_rule

        # display this user's history
        currentUserResponses = self.object.response_set.filter(user=self.request.user,
                                                               active=1).order_by('-timestamp')
        if len(currentUserResponses) > 0:
            ctx['user_latest_responses'] = getSelectionList([currentUserResponses[0]])
        ctx['user_previous_responses'] = getSelectionList(currentUserResponses[1:])

        # get history of all users
        all_responses = self.object.response_set.filter(active=1).order_by('-timestamp')
        (latest_responses, previous_responses) = categorizeResponses(all_responses)
        ctx['latest_responses'] = getSelectionList(latest_responses)
        ctx['previous_responses'] = getSelectionList(previous_responses)

        # get deleted votes
        deleted_resps = self.object.response_set.filter(active=0).order_by('-timestamp')
        (latest_deleted_resps,previous_deleted_resps) = categorizeResponses(deleted_resps)
        ctx['latest_deleted_resps'] = getSelectionList(latest_deleted_resps)
        ctx['previous_deleted_resps'] = getSelectionList(previous_deleted_resps)

        if self.object.question_voters.all().count() > 0:
            progressPercentage = len(latest_responses) / self.object.question_voters.all().count()
            progressPercentage = progressPercentage * 100
            ctx['progressPercentage'] = progressPercentage
        ctx['request_list'] = self.object.signuprequest_set.filter(status=1)
        return ctx
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

# view for results detail
class AllocateResultsView(views.generic.DetailView):
    model = Question
    template_name = 'polls/allocate_results.html'

# view for submission confirmation
class ConfirmationView(views.generic.DetailView):
    model = Question
    template_name = 'polls/confirmation.html'

# view that displays vote results using various algorithms
class VoteResultsView(views.generic.DetailView):
    model = Question
    template_name = 'polls/vote_rule.html'
    def get_context_data(self, **kwargs):
        ctx = super(VoteResultsView, self).get_context_data(**kwargs)
        #print("page accessed")
        cand_map = getCandidateMapFromList(list(self.object.item_set.all()))
        ctx['cand_map'] = cand_map# if (len(latest_responses) > 0) else None
        if len(list(self.object.response_set.all())) == 0:
            return ctx
        if self.object.status != 4 and self.object.new_vote == True:
            getPollWinner(self.object)
        final_result = self.object.finalresult
        if self.object.mixtures_pl1 == "":
            getPollWinner(self.object)
        if self.object.mixtures_pl1 != "":
            mixtures_pl1 = json.loads(self.object.mixtures_pl1)
            mixtures_pl2 = json.loads(self.object.mixtures_pl2)
            mixtures_pl3 = json.loads(self.object.mixtures_pl3)
        else:
            mixtures_pl1 = [[]]
            mixtures_pl2 = []
            mixtures_pl3 = []

        l = interpretResult(final_result)
        # print(l[0])
        poll_algorithms = []
        algorithm_links = []
        vote_results = []
        margin_victory = []
        shade_values = []

        start_poll_algorithms = getListPollAlgorithms()
        start_algorithm_links = getListAlgorithmLinks()
        to_show = self.object.vote_rule
        itr = 0
        poll_alg_num = self.object.poll_algorithm
        while to_show > 0:
            if to_show % 2 == 1:
                poll_algorithms.append(start_poll_algorithms[itr])
                algorithm_links.append(start_algorithm_links[itr])
                vote_results.append(l[0][itr])
                shade_values.append(l[2][itr])
                if itr < len(l[1]):
                    margin_victory.append(l[1][itr])
                to_show = to_show - 1
            elif itr < self.object.poll_algorithm - 1:
                poll_alg_num -= 1
            to_show = int(to_show / 2)
            itr += 1
        ctx['poll_algorithms'] = poll_algorithms
        ctx['poll_alg_num'] = poll_alg_num
        ctx['algorithm_links'] = algorithm_links
        ctx['vote_results'] = vote_results
        ctx['margin_victory'] = margin_victory
        ctx['shade_values'] = shade_values
        ctx['wmg_nodes'] = l[3]
        ctx['wmg_edges'] = l[4]
        ctx['time'] = final_result.timestamp
        ctx['margin_len'] = len(margin_victory)
        #else:
            #all_responses = self.object.response_set.filter(active=1).order_by('-timestamp')
            #(latest_responses, previous_responses) = categorizeResponses(all_responses)
            #voteResults, mixtures = getVoteResults(latest_responses, cand_map)
            #resultlist = []
            #for r in voteResults:
            #    resultlist.append(r.values())
            #ctx['vote_results'] = resultlist
            #ctx['shade_values'] = getShadeValues(voteResults)
            #(nodes, edges) = parseWmg(latest_responses, cand_map)
            #ctx['wmg_nodes'] = nodes
            #ctx['wmg_edges'] = edges

            #ctx['margin_victory'] = getMarginOfVictory(latest_responses, cand_map)
            #ctx['mixtures_pl'] = mixtures[0]
        m = len(mixtures_pl1) - 1
        print("pl2", mixtures_pl2)
        print()
        ctx['mixtures_pl1'] = mixtures_pl1
        ctx['mixtures_pl2'] = mixtures_pl2
        ctx['mixtures_pl3'] = mixtures_pl3
        print(mixtures_pl1)
        previous_results = self.object.voteresult_set.all()
        ctx['previous_winners'] = []
        for pw in previous_results:
            obj = {}
            obj['title'] = str(pw.timestamp.time())
            candnum = pw.cand_num
            resultstr = pw.result_string
            movstr = pw.mov_string
            if resultstr == "" and movstr == "":
                continue
            resultlist = resultstr.split(",")
            movlist = movstr.split(",")
            tempResults = []
            algonum = len(getListPollAlgorithms())
            if len(resultlist) < candnum*algonum:
                algonum = 7
            if len(resultlist) > 0:
                for x in range(0, algonum):
                    tempList = []
                    for y in range(x*candnum, (x+1)*candnum):
                        tempList.append(resultlist[y])
                    tempResults.append(tempList)
            obj['vote_results'] = tempResults
            tempMargin = []
            for margin in movlist:
                tempMargin.append(margin)
            obj['margin_victory'] = tempMargin
            ctx['previous_winners'].append(obj)
        return ctx

# get a list of algorithms supported by the system
# return List<String>
def getListPollAlgorithms():
    return ["Plurality", "Borda", "Veto", "K-approval (k = 3)", "Simplified Bucklin",
            "Copeland", "Maximin", "STV", "Baldwin", "Coombs", "Black", "Ranked Pairs",
            "Plurality With Runoff", "Borda Mean", "Simulated Approval"]

def getListAlgorithmLinks():
    return ["https://en.wikipedia.org/wiki/Plurality_voting_method",
            "https://en.wikipedia.org/wiki/Borda_count", "", "",
            "https://en.wikipedia.org/wiki/Bucklin_voting",
            "https://en.wikipedia.org/wiki/Copeland%27s_method",
            "https://en.wikipedia.org/wiki/Minimax_Condorcet",
            "https://en.wikipedia.org/wiki/Single_transferable_vote",
            "https://en.wikipedia.org/wiki/Nanson%27s_method#Baldwin_method",
            "https://en.wikipedia.org/wiki/Coombs%27_method","","","","",""]

# get a list of allocation methods
# return List<String>
def getAllocMethods():
    return ["Serial dictatorship: early voters first",
            "Serial dictatorship: late voter first", "Manually allocate"]

# get a list of visibility settings
# return List<String>
def getViewPreferences():
    return ["Everyone can see all votes at all times",
            "Everyone can see all votes", "Only show the names of voters",
            "Only show number of voters", "Everyone can only see his/her own vote",
            "All votes will be shown, but usernames will be hidden"]


def getWinnersFromIDList(idList):
    winners = {}
    for i in idList:
        try:
            q = Question.objects.get(pk=i)
            winners[i] = q.winner
        except Question.DoesNotExist:
            pass
    return winners

def getGMPollIDLIst():
    return [239, 219, 220, 223, 227, 229, 241, 242, 243, 230, 240, 224, 228, 238,
            232, 233, 234, 235, 236, 222, 226, 244, 245]

# build a graph of nodes and edges from a 2d dictionary
# List<Response> latest_responses
# return (List<Dict> nodes, List<Dict> edges)
def parseWmg(latest_responses, cand_map):
    pollProfile = getPollProfile(latest_responses, cand_map)
    if pollProfile == None:
        return ([], [])

    #make sure no incomplete results are in the votes
    if pollProfile.getElecType() != "soc" and pollProfile.getElecType() != "toc":
        return ([], [])

    # make sure there's at least one response
    if len(latest_responses) == 0:
        return ([], [])

    # get nodes (the options)
    nodes = []
    for rowIndex in cand_map:
        data = {}
        data['id'] = rowIndex
        data['value'] = 1
        data['label'] = cand_map[rowIndex].item_text
        nodes.append(data)

    # get edges from the weighted majority graph
    wmg = pollProfile.getWmg()
    edges = []
    for rowIndex in wmg:
        row = wmg[rowIndex]
        for colIndex in row:
            value = row[colIndex]
            if value > 0:
                data = {}
                data['from'] = rowIndex
                data['to'] = colIndex
                data['value'] = value
                data['title'] = str(value)
                edges.append(data)

    return (nodes, edges)

# format a list of votes to account for ties
def getSelectionList(responseList):
    selectList = []
    for response in responseList:
        selectList.append((response, getCurrentSelection(response)))
    return selectList

#separate the user votes into two categories: (1)most recent (2)previous history
# List<Response> all_responses
# return (List<Response> latest_responses, List<Response> previous_responses)
def categorizeResponses(all_responses):
    latest_responses = []
    previous_responses = []

    if len(all_responses) > 0:
        #the first response must be the most recent
        latest_responses.append(all_responses[0])

    others = all_responses[1:]

    #the outer loop goes through all the responses
    for response1 in others:
        #for anonymous users, check anonymous name instead of username
        if response1.user == None:
            add = True
            for response2 in latest_responses:
                if response1.anonymous_voter and response2.anonymous_voter:
                    if response1.anonymous_id == response2.anonymous_id:
                        add = False
                        previous_responses.append(response1)
                        break
            if add:
                latest_responses.append(response1)

        else:
            add = True
            #check if the user has voted multiple times
            for response2 in latest_responses:
                if not response2.user == None:
                    if response1.user.username == response2.user.username:
                        add = False
                        previous_responses.append(response1)
                        break

            #this is the most recent vote
            if add:
                latest_responses.append(response1)

    return (latest_responses, previous_responses)

# get a list of options for this poll
# Response response
# return Dict<int, Item> cand_map
def getCandidateMap(response):
    d = {}
    if response.dictionary_set.all().count() > 0:
        d = Dictionary.objects.get(response=response)
    else:
        d = buildResponseDict(response, response.question,
                              getPrefOrder(response.resp_str, response.question))
    d = interpretResponseDict(d)
    cand_map = {}

    counter = 0
    for item in d.items():
        cand_map[counter] = item[0]
        counter += 1
    return cand_map

def getCandidateMapFromList(candlist):
    cand_map = {}
    counter = 0
    for item in candlist:
        cand_map[counter] = item
        counter += 1
    return cand_map

#convert a user's preference into a 2d map
# Response response
# return Dict<int, Dict<int, int>> pref_graph
def getPreferenceGraph(response, cand_map):
    pref_graph = {}
    dictionary = {}
    if response.dictionary_set.all().count() > 0:
        dictionary = Dictionary.objects.get(response=response)
    else:
        dictionary = buildResponseDict(response, response.question,
                                       getPrefOrder(response.resp_str, response.question))
    dictionary = interpretResponseDict(dictionary)
    for cand1Index in cand_map:
        tempDict = {}
        for cand2Index in cand_map:
            if cand1Index == cand2Index:
                continue

            cand1 = cand_map[cand1Index]
            cand2 = cand_map[cand2Index]
            cand1Rank = dictionary.get(cand1)
            cand2Rank = dictionary.get(cand2)
            #lower number is better (i.e. rank 1 is better than rank 2)
            if cand1Rank < cand2Rank:
                tempDict[cand2Index] = 1
            elif cand2Rank < cand1Rank:
                tempDict[cand2Index] = -1
            else:
                tempDict[cand2Index] = 0
        pref_graph[cand1Index] = tempDict

    return pref_graph

# initialize a profile object using all the preferences
# List<Response> latest_responses
# return Profile object
def getPollProfile(latest_responses, cand_map):
    if len(latest_responses) == 0:
        return None

    pref_list = []
    for response in latest_responses:
        pref_graph = getPreferenceGraph(response, cand_map)
        userPref = Preference(pref_graph)
        pref_list.append(userPref)
    return Profile(cand_map, pref_list)
    
def translateSingleWinner(winner, cand_map):
    result = {}
    if isinstance(winner, collections.Iterable):
        return translateWinnerList(winner,cand_map)
    for cand in cand_map.keys():
        if cand == winner:
            result[cand] = 1
        else:
            result[cand] = 0
    return result

def translateWinnerList(winners, cand_map):
    result = {}
    for cand in cand_map.keys():
        if cand in winners:
            result[cand] = 1
        else:
            result[cand] = 0
    return result
    
def translateBinaryWinnerList(winners, cand_map):
    result = {}
    if len(cand_map.keys()) != len(winners):
        return result
    for cand in cand_map.keys():
        if winners[cand] == 1:
            result[cand] = 1
        else:
            result[cand] = 0
    return result

#calculate the results of the vote using different algorithms
# List<Response> latest_responses
# return a List<Dictionary<Double>>
def getVoteResults(latest_responses, cand_map):
    pollProfile = getPollProfile(latest_responses, cand_map)
    if pollProfile == None:
        return []

    #make sure no incomplete results are in the votes
    if pollProfile.getElecType() != "soc" and pollProfile.getElecType() != "toc":
        return []

    scoreVectorList = []
    scoreVectorList.append(MechanismPlurality().getCandScoresMap(pollProfile))
    scoreVectorList.append(MechanismBorda().getCandScoresMap(pollProfile))
    scoreVectorList.append(MechanismVeto().getCandScoresMap(pollProfile))
    scoreVectorList.append(MechanismKApproval(3).getCandScoresMap(pollProfile))
    scoreVectorList.append(MechanismSimplifiedBucklin().getCandScoresMap(pollProfile))
    scoreVectorList.append(MechanismCopeland(1).getCandScoresMap(pollProfile))
    scoreVectorList.append(MechanismMaximin().getCandScoresMap(pollProfile))

    #STV, Baldwin, Coombs give list of integers as output
    stv = MechanismSTV().STVwinners(pollProfile)
    baldwin = MechanismBaldwin().baldwin_winners(pollProfile)
    coombs = MechanismCoombs().coombs_winners(pollProfile)
    #print("test8")
    black = MechanismBlack().black_winner(pollProfile)
    #print("test7")
    ranked = MechanismRankedPairs().ranked_pairs_cowinners(pollProfile)
    pwro = MechanismPluralityRunOff().PluRunOff_cowinners(pollProfile)
    bordamean = MechanismBordaMean().Borda_mean_winners(pollProfile)
    simapp, sim_scores = MechanismBordaMean().simulated_approval(pollProfile)
    print("pwro=", pwro)
    #print("test6")
    scoreVectorList.append(translateWinnerList(stv, cand_map))
    scoreVectorList.append(translateWinnerList(baldwin, cand_map))
    scoreVectorList.append(translateWinnerList(coombs, cand_map))
    scoreVectorList.append(translateWinnerList(black, cand_map))
    scoreVectorList.append(translateWinnerList(ranked, cand_map))
    scoreVectorList.append(translateWinnerList(pwro, cand_map))
    scoreVectorList.append(translateBinaryWinnerList(bordamean, cand_map))
    scoreVectorList.append(translateBinaryWinnerList(simapp, cand_map))

    #for Mixtures
    #print("test1")
    rankings = pollProfile.getOrderVectorsEGMM()
    m = len(rankings[0])
    #print("test2")
    mixtures_pl1 = egmm_mixpl(rankings, m, k=1, itr=10)[0].tolist()
    #print("test3")
    mixtures_pl2 = egmm_mixpl(rankings, m, k=2, itr=10).tolist()
    #print("test4")
    mixtures_pl3 = egmm_mixpl(rankings, m, k=3, itr=10).tolist()
    #print("test5")
    #gmm = GMMMixPLAggregator(list(pollProfile.cand_map.values()), use_matlab=False)

    return scoreVectorList, mixtures_pl1, mixtures_pl2, mixtures_pl3

def calculatePreviousResults(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    question.voteresult_set.clear()
    cand_map = getCandidateMapFromList(list(question.item_set.all()))
    previous_winners = question.oldwinner_set.all()
    for pw in previous_winners:

        result = VoteResult(question=question, timestamp=pw.response.timestamp,
                            result_string="", mov_string="",
                            cand_num=question.item_set.all().count())
        result.save()
        resultstr = ""
        movstr = ""
        responses = question.response_set.reverse()
        responses = responses.filter(timestamp__range=[datetime.date(1899, 12, 30),
                                                       pw.response.timestamp], active=1)
        (lr, pr) = categorizeResponses(responses)
        scorelist, mixtures_pl1, mixtures_pl2, mixtures_pl3 = getVoteResults(lr, cand_map)
        mov = getMarginOfVictory(lr, cand_map)
        for x in range(0, len(scorelist)):
            for key, value in scorelist[x].items():
                resultstr += str(value)
                resultstr += ","
        for x in range(0, len(mov)):
            movstr += str(mov[x])
            movstr += ","
        resultstr = resultstr[:-1]
        movstr = movstr[:-1]
        result.result_string = resultstr
        result.mov_string = movstr
        result.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# return lighter (+lum) or darker (-lum) color as a hex string
# pass original hex string and luminosity factor, e.g. -0.1 = 10% darker
# String hexVal
# double lum
def colorLuminance(hexVal, lum):
    #convert to decimal and change luminosity
    rgb = "#"
    for i in range(0, 3):
        c = int(hexVal[i * 2 : i * 2 + 2], 16)
        c = round(min(max(0, c + (c * float(lum))), 255))
        c = hex(int(c))
        rgb += ("00" + str(c))[len(str(c)):]
    return rgb

# get a range of colors from green to red
# List<int> scoreVectorList
# return a List<List<String>> shadeValues
def getShadeValues(scoreVectorList):
    shadeValues = []

    for row in scoreVectorList:
        sortedRow = sorted(set(list(row.values())))
        highestRank = len(sortedRow) - 1

        newRow = []
        greenColor = "6cbf6c"
        whiteColor = "ffffff"
        for index in row:
            rank = sortedRow.index(row[index])

            if highestRank == 0:
                # must be the winner
                newRow.append("#" + greenColor)
                continue

            # make the colors closer to the left lighter (higher value) and toward the right
            #   darker (lower value)

            # the 5th row is Simplified Bucklin (lower score is better so reverse the colorings
            #   for this row)
            counter = len(shadeValues)
            if counter != 4:
                luminance = 1 - rank / float(highestRank)
            else:
                luminance = rank / float(highestRank)

            # set lowest rank to white
            if luminance == 1:
                newRow.append("#" + whiteColor)
                continue
            if luminance <= 0.5:
                luminance /= 2.0

            newRow.append(colorLuminance(greenColor, luminance))

        shadeValues.append(newRow)
    return shadeValues

# find the minimum number of votes needed to change the poll results
# List<Response> latest_responses
# return List<int> marginList
def getMarginOfVictory(latest_responses, cand_map):
    pollProfile = getPollProfile(latest_responses, cand_map)
    if pollProfile == None:
        return []

    #make sure no incomplete results are in the votes
    if pollProfile.getElecType() != "soc" and pollProfile.getElecType() != "toc":
        return []
    marginList = []
    for x in range(0,len(getListPollAlgorithms())):
        marginList.append(-1)
    marginList[0] = MechanismPlurality().getMov(pollProfile)
    marginList[1] = MechanismBorda().getMov(pollProfile)
    marginList[2] = MechanismVeto().getMov(pollProfile)
    marginList[3] = MechanismKApproval(3).getMov(pollProfile)
    marginList[4] = MechanismSimplifiedBucklin().getMov(pollProfile)
    #marginList[12] = MechanismPluralityRunOff().getMov(pollProfile)

    return marginList

# used to help find the recommended order
# User user
# User otherUser
# return double kendall_tau
def getKTScore(user, otherUser):
    kendall_tau = 0
    num = 0
    questions = Question.objects.all().filter(question_voters=otherUser).filter(question_voters=user)
    for q in questions:
        userResponse = q.response_set.filter(user=user).reverse()
        other_user_response = q.response_set.filter(user=otherUser).reverse()
        if len(userResponse) > 0 and len(other_user_response) > 0:
            num = num + 1
            userResponse = get_object_or_404(Dictionary, response=userResponse[0])
            other_user_response = get_object_or_404(Dictionary, response=other_user_response[0])
            kendall_tau += getKendallTauScore(userResponse, other_user_response)

    if num != 0:
        kendall_tau /= num
    if kendall_tau == 0:
        kendall_tau = .25
    else:
        kendall_tau = 1/(1 + kendall_tau)
    return kendall_tau

# use other responses to recommend a response order for you
# responses are sorted from latest to earliest
# List<Response> response
# request request
# List<Item> default_order
# return List<Item> final_list
def getRecommendedOrder(other_user_responses, request, default_order):
    # no responses
    if len(other_user_responses) == 0:
        return default_order

    # if the poll owner added more choices during the poll, then reset using the default order
    itemsLastResponse = len(getCandidateMap(other_user_responses[0]))
    itemsCurrent = default_order.count()
    if itemsLastResponse != itemsCurrent:
        return default_order

    # iterate through all the responses
    preferences = []
    for resp in other_user_responses:
        user = request.user
        otherUser = resp.user

        # get current user and other user preferences
        KT = getKTScore(user, otherUser)
        pref_graph = getPreferenceGraph(resp, cand_map)
        preferences.append(Preference(pref_graph, KT))

    cand_map = getCandidateMap(other_user_responses[0])
    pollProfile = Profile(cand_map, preferences)

    # incomplete answers
    if pollProfile.getElecType() != "soc" and pollProfile.getElecType() != "toc":
        return default_order

    # return the order based off of ranking
    pref = MechanismBorda().getCandScoresMap(pollProfile)
    l = list(sorted(pref.items(), key=lambda kv: (kv[1], kv[0])))
    final_list = []
    for p in reversed(l):
        final_list.append(cand_map[p[0]])
    return final_list

# function to add voter to voter list (invite only)
# can invite new voters at any time
def addVoter(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    creator_obj = User.objects.get(id=question.question_owner_id)

    newVoters = request.GET.get('voters')
    # send an invitation email
    email = request.GET.get('email') == 'email'
    question.emailInvite = email
    question.save()
    if email:
        email_class = EmailThread(request, question_id, 'invite')
        email_class.start()
    # add each voter to the question by username
    voterObj = User.objects.get(username=newVoters)
    question.question_voters.add(voterObj.id)
    request.session['setting'] = 1

    data = "{}"
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)

# remove voters from a poll.
# should only be done before a poll starts
def removeVoter(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    newVoters = request.POST.getlist('voters')
    email = request.POST.get('email') == 'email'
    question.emailDelete = email
    question.save()
    if email:
        email_class = EmailThread(request, question_id, 'remove')
        email_class.start()
    for voter in newVoters:
        voterObj = User.objects.get(username=voter)
        question.question_voters.remove(voterObj.id)
    request.session['setting'] = 1
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# called when creating the poll
def setInitialSettings(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    question.poll_algorithm = request.POST['pollpreferences']
    question.display_pref = request.POST['viewpreferences']
    question.creator_pref = request.POST['creatorpreferences']
    openstring = request.POST['openpoll']
    signup_string = request.POST['selfsignup']
    twocol = False
    onecol = False
    slider = False
    star = False
    yesno = False
    yesno2 = False
    uilist = request.POST.getlist('ui')
    if "twocol" in uilist:
        twocol = True
    if "onecol" in uilist:
        onecol = True
    if "slider" in uilist:
        slider = True
    if "star" in uilist:
        star = True
    if "yesno" in uilist:
        yesno = True
    if "yesno2" in uilist:
        yesno2 = True
    vr = (2 ** (int(request.POST['pollpreferences']) - 1))
    for rule in request.POST.getlist('vr'):
        if int(rule) != (2 ** (int(request.POST['pollpreferences']) - 1)):
            vr += int(rule)
    question.twocol_enabled = twocol
    question.onecol_enabled = onecol
    question.slider_enabled = slider
    question.star_enabled = star
    question.yesno_enabled = yesno
    question.yesno2_enabled = yesno2
    question.ui_number = twocol+onecol+slider+star+yesno+yesno2
    question.vote_rule = vr
    if openstring == "anon":
        question.open = 1
    elif openstring == "invite":
        question.open = 0
    else:
        question.open = 2
    if signup_string == "allow":
        question.allow_self_sign_up = 1
    else:
        question.allow_self_sign_up = 0

    question.save()
    return HttpResponseRedirect(reverse('polls:regular_polls'))

# set algorithms and visibility
def setPollingSettings(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    # set the poll algorithm or allocation method using an integer
    poll_alg = question.poll_algorithm
    if 'pollpreferences' in request.POST:
        poll_alg = int(request.POST['pollpreferences'])
        question.poll_algorithm = poll_alg

    # set the visibility settings, how much information should be shown to the user
    # options range from showing everything (most visibility) to showing only the user's vote
    #   (least visibility)
    displayChoice = request.POST['viewpreferences']
    if displayChoice == "always":
        question.display_pref = 0
    elif displayChoice == "allpermit":
        question.display_pref = 1
    elif displayChoice == "voternames":
        question.display_pref = 2
    elif displayChoice == "justnumber":
        question.display_pref = 3
    elif displayChoice == "nothing":
        question.display_pref = 4
    else:
        question.display_pref = 5
    creatorChoice = str(question.creator_pref)
    if 'creatorpreferences' in request.POST:
        creatorChoice = request.POST['creatorpreferences']
    if creatorChoice == "1":
        question.creator_pref = 1
    else:
        question.creator_pref = 2
    vr = (2 ** (poll_alg - 1))
    for rule in request.POST.getlist('vr'):
        if int(rule) != (2 ** (poll_alg - 1)):
            vr += int(rule)
    question.vote_rule = vr
    question.save()
    request.session['setting'] = 2
    messages.success(request, 'Your changes have been saved.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# poll is open to anonymous voters
def changeType(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    openstring = request.POST['openpoll']
    if openstring == "anon":
        question.open = 1
    elif openstring == "invite":
        question.open = 0
    else:
        question.open = 2
    question.save()
    request.session['setting'] = 4
    messages.success(request, 'Your changes have been saved.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# poll is closed to anonymous voters
def closePoll(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    question.open = 0
    question.save()
    request.session['setting'] = 4
    messages.success(request, 'Your changes have been saved.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# poll is closed to anonymous voters, open to people logged in
def uninvitedPoll(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    question.open = 2
    question.save()
    request.session['setting'] = 4
    messages.success(request, 'Your changes have been saved.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def duplicatePoll(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    title = question.question_text
    desc = question.question_desc
    voters = question.question_voters.all()
    user = request.user
    items = question.item_set.all()
    new_question = Question(question_text=title, question_desc=desc,
                            pub_date=timezone.now(), question_owner=user,
                            display_pref=question.display_pref,
                            emailInvite=question.emailInvite,
                            emailDelete=question.emailDelete,
                            emailStart=question.emailStart,
                            emailStop=question.emailStop, creator_pref=question.creator_pref,
                            poll_algorithm=question.poll_algorithm,
                            question_type=question.question_type,
                            open=question.open,twocol_enabled=question.twocol_enabled,
                            onecol_enabled=question.onecol_enabled,
                            slider_enabled=question.slider_enabled,
                            star_enabled=question.star_enabled,
                            yesno_enabled=question.yesno_enabled,
                            allowties=question.allowties,
                            vote_rule=question.vote_rule)
    new_question.save()
    new_question.question_voters.add(*voters)
    new_items = []
    for item in items:
        new_item = Item(question=new_question, item_text=item.item_text,
                        item_description=item.item_description, timestamp=timezone.now(),
                        image=item.image, imageURL=item.imageURL)
        new_item.save()
        new_items.append(new_item)
    new_question.item_set.add(*new_items)
    setupEmail(new_question)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    #return HttpResponseRedirect(reverse('polls:regular_polls'))

def deleteUserVotes(request, response_id):
    response = get_object_or_404(Response, pk=response_id)
    user = response.user
    question = response.question
    if user: 
        question.response_set.filter(user=user).update(active=0)
    else:
        question.response_set.filter(anonymous_id=response.anonymous_id).update(active=0)
    request.session['setting'] = 6
    if not question.new_vote:
    	question.new_vote = True
    	question.save()
    messages.success(request, 'Your changes have been saved.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def restoreUserVotes(request, response_id):
    response = get_object_or_404(Response, pk=response_id)
    user = response.user
    question = response.question
    if user: 
        question.response_set.filter(user=user, active=0).update(active=1)
    else:
        question.response_set.filter(anonymous_id=response.anonymous_id, active=0).update(active=1)
    request.session['setting'] = 7
    if not question.new_vote:
    	question.new_vote = True
    	question.save()
    messages.success(request, 'Your changes have been saved.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# view for ordering voters for allocation
class AllocationOrder(views.generic.DetailView):
    model = Question
    template_name = 'polls/allocation_order.html'
    def get_context_data(self, **kwargs):
        ctx = super(AllocationOrder, self).get_context_data(**kwargs)
        currentAllocationOrder = self.object.allocationvoter_set.all()
        tempOrderStr = self.request.GET.get('order', '')
        if tempOrderStr == "null":
            ctx['question_voters'] = self.object.question_voters.all()
            return ctx

        # check if the user submitted a vote earlier and display that for modification
        if len(currentAllocationOrder) > 0:
            ctx['currentSelection'] = currentAllocationOrder

        ctx['question_voters'] = self.object.question_voters.all()
        return ctx
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

# manually set the allocation order of voters
def setAllocationOrder(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    # get the voter order
    orderStr = request.POST["pref_order"]
    prefOrder = getPrefOrder(orderStr, question)
    if orderStr == "":
        # the user must rank all voters
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    prefOrder = orderStr.split(",")
    if len(prefOrder) != len(question.question_voters.all()):
        # the user must rank all voters
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    #reset allocation order
    for voter in question.allocationvoter_set.all():
        voter.delete()

    # find ranking student gave for each item under the question
    item_num = 1
    for item in question.question_voters.all():
        arrayIndex = prefOrder.index("item" + str(item_num))
        if arrayIndex != -1:
            user = question.question_voters.all()[arrayIndex]
            # add pref to list
            voter, created = AllocationVoter.objects.get_or_create(question=question,
                                                                   user=user, response=None)
            voter.save()

        item_num += 1

    return HttpResponseRedirect(reverse('polls:viewAllocationOrder', args=(question.id,)))

# if the allocation mechanism is early-first or late-first serial dictatorship,
#   assign the order based off of latest response time
# Question question
# List<Response> latest_responses
def getInitialAllocationOrder(question, latest_responses):
    if len(latest_responses) == 0:
        return

    # assign the default allocation order from earliest to latest
    counter = len(question.item_set.all())
    for user_response in list(reversed(latest_responses)):
        # no more items left to allocate
        if counter == 0:
            return

        counter -= 1
        # create the object
        voter, created = AllocationVoter.objects.get_or_create(question=user_response.question,
                                                               user=user_response.user)
        # save the most recent response
        voter.response = user_response
        voter.save()
    return

# get the current allocation order for this poll
# if this poll is part of a multi-poll, then it must consider the order of the previous subpolls
# Question question
# List<Response> latest_responses
# return Query<AllocationVoter> allocation_order
def getCurrentAllocationOrder(question, latest_responses):
    # get the allocation order from the first multipoll
    allocation_order = []
    if question.m_poll == True:
        multipoll = question.multipoll_set.all()[0]
        firstSubpoll = multipoll.questions.all()[0]
        allocation_order = firstSubpoll.allocationvoter_set.all()

        # fix the allocation order from the first subpoll
        if len(allocation_order) == 0:
            # get allocation order
            getInitialAllocationOrder(question, latest_responses)
        else:
            # copy a new allocation order based off of the first subpoll
            for alloc_item in allocation_order:
                voter, created = AllocationVoter.objects.get_or_create(question=question,
                                                                       user=alloc_item.user)
                voter.response = question.response_set.reverse().filter(user=alloc_item.user)[0]
                voter.save()
        allocation_order = question.allocationvoter_set.all()
    else:
        # get the allocation order
        allocation_order = question.allocationvoter_set.all()

        # calculate initial order if there is none or if new voters are added during the poll
        if len(allocation_order) == 0 or len(allocation_order) != len(latest_responses):
            getInitialAllocationOrder(question, latest_responses)
            allocation_order = question.allocationvoter_set.all()

    return allocation_order

# order user responses similar to the allocation order
# Query<AllocationVoter> allocation_order
# return List<Response>
def getResponseOrder(allocation_order):
    response_set = []
    for order_item in allocation_order:
        question = order_item.question
        user = order_item.user

        # skip if no vote
        if question.response_set.reverse().filter(user=user).count() == 0:
            continue

        # save response
        response = question.response_set.reverse().filter(user=user)[0]
        order_item.response = response
        order_item.save()

        # add to the list
        response_set.append(response)
    return response_set

# update the database with the new allocation results
# Question question
# Dict<String, String> allocationResults
def assignAllocation(question, allocationResults):
    for username, item in allocationResults.items():
        currentUser = User.objects.filter(username=username)
        allocatedItem = question.item_set.get(item_text=item)
        mostRecentResponse = question.response_set.reverse().filter(user=currentUser)[0]
        mostRecentResponse.allocation = allocatedItem
        mostRecentResponse.save()
    return

# organize the data into items and responses (most recent) and then apply allocation algorithms
# to get the final result
# Question question
def getFinalAllocation(question):
    # the latest and previous responses are from latest to earliest
    response_set = question.response_set.filter(active=1).order_by('-timestamp')
    (latest_responses, previous_responses) = categorizeResponses(response_set)

    # no responses, so stop here
    if len(latest_responses) == 0:
        return

    allocation_order = getCurrentAllocationOrder(question, latest_responses)
    response_set = getResponseOrder(allocation_order) # get list of responses in specified order

    # make items and responses views.generic
    item_set = latest_responses[0].question.item_set.all()
    itemList = []
    for item in item_set:
        itemList.append(item.item_text)
    responseList = []
    for response in response_set:
        tempDict = {}
        dictionary = {}
        if response.dictionary_set.all().count() > 0:
            dictionary = Dictionary.objects.get(response=response)
        else:
            dictionary = buildResponseDict(response, response.question,
                                           getPrefOrder(response.resp_str,
                                                        response.question))
        dictionary = interpretResponseDict(dictionary)
        for item, rank in dictionary.items():
            tempDict[item.item_text] = rank
        responseList.append((response.user.username, tempDict))

    allocationResults = allocation(question.poll_algorithm, itemList, responseList)
    assignAllocation(question, allocationResults)


# function to get preference order from a string
# String orderStr
# Question question
# return List<List<String>> prefOrder
def getPrefOrder(orderStr, question):
    # empty string
    if orderStr == "":
        return None
    if ";;|;;" in orderStr:
        current_array = orderStr.split(";;|;;")
        final_order = []
        length = 0
        for item in current_array:
            if item != "":
                curr = item.split(";;")
                final_order.append(curr)
                length += len(curr)
    else:
        final_order = json.loads(orderStr)
    
    # the user hasn't ranked all the preferences yet
    #if length != len(question.item_set.all()):
     #   return None

    return final_order

# function to process student submission
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    prevResponseCount = question.response_set.filter(user=request.user).count()
    # get the preference order

    orderStr = request.POST["pref_order"]
    prefOrder = getPrefOrder(orderStr, question)
    behavior_string = request.POST["record_data"]
    #print(behavior_string)
    if prefOrder == None:
        # the user must rank all preferences
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # make Response object to store data
    comment = request.POST['comment']
    response = Response(question=question, user=request.user, timestamp=timezone.now(),
                        resp_str=orderStr, behavior_data=behavior_string)
    if comment != "":
        response.comment = comment
    response.save()

    if question.related_class != None and request.user not in question.related_class.students.all():
        question.related_class.students.add(request.user)

    if question.related_class != None and request.user == question.related_class.teacher:
        formatted_order = sorted([i[4:] for i in prefOrder[0]])
        question.correct_answer = json.dumps(formatted_order)
        question.save()


    #enqueue
    #enqueue(getCurrentResult(question))

    #get current winner
    old_winner = OldWinner(question=question, response=response)
    old_winner.save()
    # notify the user that the vote has been saved/updated
    if prevResponseCount == 0:
        messages.success(request, 'Saved!')
    else:
        messages.success(request, 'Updated!')

    if question.open == 2 and request.user not in question.question_voters.all():
        question.question_voters.add(request.user.id)

    if not question.new_vote:
        question.new_vote = True
        question.save()

    return HttpResponseRedirect(reverse('polls:detail', args=(question.id,)))

# create a new dictionary that stores the preferences and rankings
# Response response
# Question question
# List<List<String>> prefOrder
def buildResponseDict(response, question, prefOrder):
    d = {}

    # find ranking user gave for each item under the question
    item_num = 1
    for item in question.item_set.all():
        rank = 1
        #Flag for examining the case when new choices are added to poll after poll starts
        flag = True
        for l in prefOrder:
            string = "item" + str(item)
            if string in l:
                d[item] = rank
                #If the item is found in preforder, the set flag to false
                flag = False
                break
            rank += 1
        if flag:
            d[item] = 1000
        # if arrayIndex == -1:
        #     # set value to lowest possible rank
        #     d[item] = question.item_set.all().count()
        # else:
        #     # add 1 to array index, since rank starts at 1
        #     rank = (prefOrder.index("item" + str(item))) + 1
        #     # add pref to response dict
        #     d[item] = rank
    return d

def interpretResponseDict(dict):
    d = dict
    max = -1
    for k, v in d.items():
        if v > max and v != 1000:
            max = v
    for k, v in d.items():
        if v == 1000:
            d[k] = max + 1

    return d


# join a poll without logging in
def anonymousJoin(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    name = request.POST['name']
    request.session['anonymousvoter'] = name
    return HttpResponseRedirect(reverse('polls:detail', args=(question.id,)))

# submit a vote without logging in
def anonymousVote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    voter = "Anonymous"
    id = 0
    # check if the anonymous voter has voted before
    if 'anonymousname' in request.POST:
        voter = request.POST['anonymousname']
    if 'anonymousid' not in request.session:
        request.session['anonymousvoter'] = voter
        id = question.response_set.all().count() + 1
        request.session['anonymousid'] = id
    else:
        voter = request.session['anonymousvoter']
        id = request.session['anonymousid']
    # get the preference order
    #print(orderStr)
    orderStr = request.POST["pref_order"]
    prefOrder = getPrefOrder(orderStr, question)
    if prefOrder == None:
        # the user must rank all preferences
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # make Response object to store data
    comment = request.POST['comment']
    response = Response(question=question, timestamp=timezone.now(),
                        anonymous_voter=voter, anonymous_id=id, resp_str=orderStr)
    if comment != "":
        response.comment = comment
    response.save()

    

    # find ranking student gave for each item under the question

    #get current winner
    old_winner = OldWinner(question=question, response=response)
    old_winner.save()
    if not question.new_vote:
        question.new_vote = True
        question.save()
    # notify the user that the vote has been updated
    messages.success(request, 'Saved!')
    return HttpResponseRedirect(reverse('polls:detail', args=(question.id,)))

def sendMessage(request):
    if request.method == 'POST':
        message = request.POST["message"]
        name = request.POST["name"]
        email = request.POST["email"]
        if request.user.username != "":
            m1 = Message(text=message, timestamp=timezone.now(), user=request.user,
                         name=name, email=email)
            m1.save()
        else:
            m2 = Message(text=message, timestamp=timezone.now(), name=name, email=email)
            m2.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# Mixture API
def mixtureAPI(request):
    context = RequestContext(request)
    if request.method == 'POST':
        votes = json.loads(request.GET['data'])
        m = len(votes[0])
        mixtures_pl1 = egmm_mixpl(votes, m, k=1, itr=10).tolist()
        mixtures_pl2 = egmm_mixpl(votes, m, k=2, itr=10).tolist()
        mixtures_pl3 = egmm_mixpl(votes, m, k=3, itr=10).tolist()
        return HttpResponse(
            json.dumps(mixtures_pl2),
            content_type="application/json"
        )

# Mixture API
def mixtureAPI_test(request):
    context = RequestContext(request)
    return render('polls/api_test.html')

#Poll search API
def get_polls(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        polls = list(Question.objects.filter(question_owner=request.user,
                                                       m_poll=False,
                                                       question_text__icontains = q).order_by('-pub_date'))
        polls += list(request.user.poll_participated.filter(m_poll=False,
            question_text__icontains = q ).exclude(question_owner=request.user).order_by('-pub_date'))
        polls = polls[:20]
        results = []
        for poll in polls:
            poll_json = {}
            poll_json['id'] = poll.id
            poll_json['label'] = poll.question_text
            poll_json['value'] = poll.question_text
            if poll.question_desc:
                poll_json['desc'] = poll.question_text
            else:
                poll_json['desc'] = "None"
            poll_json['status'] = poll.status
            poll_json['curr_win'] = (poll.question_type == 1 and
                                    poll.status != 1 and poll.status != 3 and
                                    len(poll.response_set.all()) > 0)
            poll_json['type'] = poll.question_type
            if poll.question_type == 1 and poll.status == 3:
                poll_json['winner'] = poll.winner
            elif poll.question_type == 2 and poll.status == 3:
                poll_json['winner'] = ""
            poll_json['created'] = request.user == poll.question_owner
            poll_json['voter'] = request.user in poll.question_voters.all()
            results.append(poll_json)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)

# Add function
def addFolder(request):
    if request.method == 'POST':
        title = request.POST['title']
        fold = Folder(user=request.user, title=title, edit_date=timezone.now())
        fold.save()
        for poll in request.POST.getlist('polls'):
            try:
                q = Question.objects.filter(id=int(poll)).all()[0]
                fold.questions.add(q)
            except:
                print("Error: poll not working")
        fold.save()
        print(fold.questions)
        return HttpResponseRedirect(reverse('polls:regular_polls'))
    else:
        print("Error: not post in addFolder function line 1993")

def getMturkPollList(request):
    # get all IRB polls from database
    list1 = [1,2,3,4,5,6,7,8,9,10,11]
    list2 = [12,13,14,15,16,17,18,19,20]
    ramdom.shuffle(list2)
    polls = list1 + list2
    # polls= random.sample(polls,k=10)
    #329-342
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# submit a vote without logging in from Mturk
def MturkVote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    # get the preference order
    orderStr = request.POST["pref_order"]
    prefOrder = getPrefOrder(orderStr, question)
    behavior_string = request.POST["record_data"]
    if prefOrder == None:
        # the user must rank all preferences
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # make Response object to store data
    response = Response(question=question, user=request.user, timestamp=timezone.now(),
                        resp_str=orderStr, behavior_data=behavior_string)
    response.save()

    # find ranking student gave for each item under the question

    #get current winner
    old_winner = OldWinner(question=question, response=response)
    old_winner.save()
    if not question.new_vote:
        question.new_vote = True
        question.save()
    # notify the user that the vote has been updated
    #messages.success(request, 'Saved!')
    polls = json.loads(request.user.userprofile.sequence)
    current = request.user.userprofile.cur_poll
    try:
        idx = polls.index(current)
        if idx == len(polls)-1:
            request.user.userprofile.finished = True
            request.user.userprofile.save()
            return HttpResponseRedirect(reverse('polls:SurveyCode'))
        else:
            request.user.userprofile.cur_poll = polls[idx + 1]
            request.user.userprofile.save()
            return HttpResponseRedirect(reverse('polls:IRBdetail', args=(polls[idx+1],)))

    except ValueError:
        return HttpResponseRedirect(reverse('polls:SurveyCode'))



class MturkView(views.generic.ListView):
    template_name = 'events/Mturk/Mturk.html'
    context_object_name = 'question_list'
    model = Question
    
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())
    
    
    def get_context_data(self,**kwargs):
        ctx = super(MturkView, self).get_context_data(**kwargs)
        #exp = get_object_or_404(User, username="opraexp")
        #polls= list(Question.objects.filter(question_owner = exp))
        #ctx['IRB_polls'] = polls
        return ctx

class SurveyFinalView(views.generic.ListView):
    template_name = 'events/Mturk/SurveyCode.html'
    model = Question
    
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())
    
    def get_context_data(self,**kwargs):
        ctx = super(SurveyFinalView, self).get_context_data(**kwargs)
        #get surveycode
        code= self.request.user.userprofile.code
        ctx['code']= code
        return ctx

class SurveyEndView(views.generic.ListView):
    template_name = 'events/Mturk/End.html'
    model = Question
    
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())
    
    def get_context_data(self,**kwargs):
        ctx = super(SurveyEndView, self).get_context_data(**kwargs)
        return ctx

# view for question detail
class IRBDetailView(views.generic.DetailView):
    model = Question
    template_name = 'events/Mturk/IRBPollDetail.html'
    
    def get_order(self, ctx):
        other_user_responses = self.object.response_set.reverse()
        default_order = list(ctx['object'].item_set.all())
        random.shuffle(default_order)
        return default_order
    #commented out to improve performance
    #return getRecommendedOrder(other_user_responses, self.request, default_order)
    
    def get_context_data(self, **kwargs):
        ctx = super(IRBDetailView, self).get_context_data(**kwargs)
        #exp = get_object_or_404(User, username="opraexp")
            
        polls = json.loads(self.request.user.userprofile.sequence)
        current = self.request.user.userprofile.cur_poll
        idx = 0
        try:
            idx = polls.index(current)
            ctx['poll_index'] = idx + 1
        except ValueError:
            pass
        #ctx['index']= idx
        #ctx['title_index']=idx-5
        #ctx['title_type']=idx<12
        #ctx['tutorials'] = [2,3]
        ctx['seq']=range(1,len(polls)+1)
        #ctx['outof']=idx>5
        ctx['next'] = self.object.next
        
        #get surveycode
        #code= self.request.user.userprofile.code
        #ctx['code']= code
        
        # Get the responses for the current logged-in user from latest to earliest
        currentUserResponses = self.object.response_set.filter(user=self.request.user).reverse()

    
        # reset button
        #if isPrefReset(self.request):
        #    ctx['items'] = self.get_order(ctx)
        #    return ctx

        # check if the user submitted a vote earlier and display that for modification
        #if len(currentUserResponses) > 0 and self.request.user.get_username() != "":
        #    ctx['currentSelection'] = getCurrentSelection(currentUserResponses[0])
        #    ctx['itr'] = itertools.count(1, 1)
        #    ctx['unrankedCandidates'] = getUnrankedCandidates(currentUserResponses[0])
        #    items = []
         #   for item in ctx['currentSelection']:
        #        for i in item:
        #            items.append(i)
        #    if not ctx['unrankedCandidates'] == None:
        #        for item in ctx['unrankedCandidates']:
        #            items.append(item)
        #    ctx['items'] = items
        #else:
            # no history so display the list of choices
        random_order = self.get_order(ctx)

        use_recommend = False
        if use_recommend and idx > 0:
            recommended_order = recommend_ranking(idx)
            try:
                current_order = [int(i.item_text) for i in random_order]
                new_order = [random_order[current_order.index(i)] for i in recommended_order]
                random_order = new_order
            except:
                pass
        ctx['items'] = random_order
        try:
            random_utilities = []
            sigma = 20
            for i in random_order:
                base = float(i.item_text)
                utility = round(np.random.normal(0.0,sigma)+ base)
                while utility in random_utilities:
                    utility = round(np.random.normal(0.0,sigma)+ base)
                random_utilities.append(utility)
        except:
            random_utilities = random_order
        ctx['random_utilities'] = random_utilities
        return ctx
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())

# function to process student submission
def ExpAddComment(request):
    if request.method == "POST":
    # make Response object to store data
        comment = request.POST['comment']
        request.user.userprofile.comments = comment
        request.user.userprofile.save()
    return HttpResponseRedirect(reverse('polls:SurveyEnd'))

def test_server(request):
    m = Message(timestamp=timezone.now(),text="test")
    m.save()
    return HttpResponse("success")

def delete_messages(request):
    Message.objects.all().delete()
    return HttpResponse("success")
    
def get_num_responses(request):
    result = ""
    resps = Response.objects.filter(user__id__range=(237,647))
    result += str(len(resps)) + "\n"
    return HttpResponse(result)


class RGView(views.generic.ListView):
    template_name = 'events/ResearchGroup.html'
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())
    def get_context_data(self, **kwargs):
        ctx = super(RGView, self).get_context_data(**kwargs)
        return ctx

class RGENView(views.generic.ListView):
    template_name = 'events/ResearchGroupEN.html'
    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())
    def get_context_data(self, **kwargs):
        ctx = super(RGENView, self).get_context_data(**kwargs)
        return ctx

def get_voters(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        users = list(User.objects.filter(username__icontains=q))
        poll_id = request.GET.get('poll_id', '-1')
        if poll_id != '-1':
            exists = Question.objects.filter(pk=poll_id)[0].question_voters.all()
        else:
            exists = []
        ##Add get possible users from API
        results = []
        count = 0
        for user in users:
            if count == 20:
                break
            if user in exists:
                continue
            user_json = {}
            user_json['id'] = user.id
            user_json['label'] = user.username
            user_json['value'] = user.username
            results.append(user_json)
            count += 1
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)

def recommend_ranking(k):
    try:
        dataset = json.loads(RandomUtilityPool.objects.get(id=3).data)
        rankings = random.sample(dataset,k)
        candidates = [i[1] for i in rankings[0]]
        borda_scores = dict()
        for c in candidates:
            borda_scores[c] = 0
        for r in rankings:
            for i in range(len(r)):
                borda_scores[r[i][1]] += len(r)-i-1
        k = list(borda_scores.keys())
        v = list(borda_scores.values())
        v_with_index = [(v[i],i) for i in range(len(v))]
        v_with_index.sort(reverse=True)
        sorted_k = [k[i[1]] for i in v_with_index]
        return sorted_k
    except:
        return None


class SelfRegisterView(views.generic.DetailView):
    model = Question
    template_name = "polls/self_register.html"
    def get_context_data(self, **kwargs):
        ctx = super(SelfRegisterView, self).get_context_data(**kwargs)
        if check_duplicate_sign_up(self.request.user,self.object):
            ctx["submitted"] = True
        return ctx

def change_self_sign_up(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    signup_string = request.POST["selfsignup"]
    if signup_string == "allow":
        question.allow_self_sign_up = 1
    else:
        question.allow_self_sign_up = 0
    question.save()
    request.session['setting'] = 9

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def self_sign_up(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if request.method == "POST" and request.user != question.question_owner:
        if check_duplicate_sign_up(request.user,question):
            return HttpResponse("You can only register once!")
        item_name = request.POST['item_name']
        new_request = SignUpRequest(question=question,user=request.user,item_name=item_name,timestamp=timezone.now())
        new_request.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def check_duplicate_sign_up(user, question):
    current_list = list(question.item_set.all())
    request_list = list(question.signuprequest_set.filter(status=1))
    for i in current_list:
        if str(user.id) == i.self_sign_up_user_id:
            return True
    for r in request_list:
        if user == r.user:
            return True
    return False

def approve_request(request, request_id):
    sign_up_request = get_object_or_404(SignUpRequest,pk=request_id)
    question = sign_up_request.question
    if question.status != 1 and question.status != 4:
        return HttpResponse("Please pause the poll first.")
    sign_up_request.status = 2
    sign_up_request.save()
    item_text = sign_up_request.item_name
    allChoices = question.item_set.all()
    for choice in allChoices:
        if item_text == choice.item_text:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    recentlyAdded = False
    if question.status == 4:
        recentlyAdded = True
    new_choice = Item(question=question, item_text=item_text, timestamp=timezone.now(), recently_added=recentlyAdded, self_sign_up_user_id=str(sign_up_request.user.id))
    new_choice.save()
    request.session['setting'] = 9

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

#############################################################
# CLASSES                                                   #
#############################################################
def newClass(request):
    if request.method == "POST":
        date = request.POST['startDate'].split('/')
        date = date[2] + "-" + date[0] + "-" + date[1]
        new_class = Classes(title=request.POST['classTitle'], startDate=date, teacher=request.user)
        new_class.save()
        new_class.students.add(request.user.id)
        return HttpResponseRedirect(reverse('polls:classes'))
    else:
        context = RequestContext(request)
        return render(request, 'classes/new_class.html', {})

def newQuiz(request, pk):
    if request.method == "POST":
        cur_class = get_object_or_404(Classes, pk=pk)
        options = json.loads(request.POST["choice"])
        quiz = Question(question_text=request.POST["quizTitle"],
                                question_desc=request.POST["quizDesc"],
                                pub_date=timezone.now(),
                                question_owner=request.user,
                                display_pref=4,
                                emailInvite=False,
                                emailDelete=False,
                                emailStart=False,
                                emailStop=False,
                                question_type=3,
                                twocol_enabled=False,
                                onecol_enabled=False,
                                slider_enabled=False,
                                star_enabled=False,
                                yesno_enabled=True,
                                single_enabled=False,
                                ui_number=True+True+True+True+True,
                                vote_rule=1,
                                creator_pref=1,
                                open=2,
                                related_class=cur_class)
        quiz.save()
        for option in options:
            item = Item(question=quiz,
                item_text=option,
                timestamp=timezone.now())
            item.save()
        for student in cur_class.students.all():
            quiz.question_voters.add(student.id)
    return HttpResponseRedirect(reverse('polls:classes'))

def takeAttendance(request, pk):
    cur_class = get_object_or_404(Classes, pk=pk)
    if cur_class.teacher == request.user and cur_class.attendance == -1:
        quiz = Question(question_text=cur_class.title + " attendance " + str(timezone.now())[:19],
                                question_desc="",
                                pub_date=timezone.now(),
                                question_owner=request.user,
                                display_pref=4,
                                emailInvite=False,
                                emailDelete=False,
                                emailStart=False,
                                emailStop=False,
                                question_type=4,
                                twocol_enabled=False,
                                onecol_enabled=False,
                                slider_enabled=False,
                                star_enabled=False,
                                yesno_enabled=False,
                                single_enabled=True,
                                ui_number=True+True+True+True+True,
                                vote_rule=1,
                                creator_pref=1,
                                open=2,
                                status=2,
                                related_class=cur_class)
        quiz.save()
        item = Item(question=quiz,
            item_text="I'm here",
            timestamp=timezone.now())
        item.save()
        cur_class.attendance = quiz.id
        cur_class.save()
        print(cur_class.attendance)
        for student in cur_class.students.all():
            quiz.question_voters.add(student.id)
    return HttpResponseRedirect(reverse('polls:classes'))

def stopAttendance(request, pk):
    cur_class = get_object_or_404(Classes, pk=pk)
    if cur_class.teacher == request.user and cur_class.attendance != -1:
        quiz = get_object_or_404(Question, pk=cur_class.attendance)
        quiz.status = 3
        quiz.save()
        cur_class.attendance = -1
        cur_class.save()
    return HttpResponseRedirect(reverse('polls:classes'))

@login_required
def attendanceSignIn(request, question_id):
    cur_poll = get_object_or_404(Question, pk=question_id)
    if request.user not in cur_poll.related_class.students.all():
        cur_poll.related_class.students.add(request.user.id)
    resp = Response(question=cur_poll, user=request.user, timestamp=timezone.now(),resp_str="[\"itemI'm here\"]")
    resp.save()
    return render(request, "classes/success_join.html", {"poll_name":cur_poll.question_text})

def classSignIn(request, pk):
    cur_class = get_object_or_404(Classes, pk=pk)
    if cur_class.teacher == request.user and cur_class.attendance != -1:
        quiz = get_object_or_404(Question, pk=cur_class.attendance)
        orderStr = "itemI'm here;;|;;"
        response = Response(question=quiz, user=request.user,
            timestamp=timezone.now(), resp_str=orderStr)
        response.save()
    return HttpResponseRedirect(reverse('polls:classes'))

class ClassesView(views.generic.ListView):
    template_name = 'classes/classes.html'
    context_object_name = 'question_list'
    def get_queryset(self):
        return Question.objects.all()
    def get_context_data(self, **kwargs):
        ctx = super(ClassesView, self).get_context_data(**kwargs)
        # sort the list by date
        classes = Classes.objects.filter(teacher=self.request.user).order_by('-startDate')
        quizzes = []
        quizzes_part_curr = []
        quizzes_part_prev = []
        quizzes_part_prev_answer = []
        attendance_prev = []
        attendance_curr = []
        attendance_prev_states = []
        taking_attendance = []
        classes_part = self.request.user.students.exclude(teacher=None).order_by('-startDate')#self.request.user)
        ctx['classes_created'] = classes
        ctx['classes_participated'] = classes_part
        for class_inst in classes:
            quizzes.append(Question.objects.filter(related_class=class_inst).filter(question_type=3))
        for class_inst in classes_part:
            if class_inst.attendance > 0:
                question = Question.objects.filter(id=class_inst.attendance)[0]
                prevResponseCount = question.response_set.filter(user=self.request.user).count()
                taking_attendance.append(prevResponseCount == 0)
            else:
                taking_attendance.append(False)
            previous_quiz = list(Question.objects.filter(related_class=class_inst).filter(question_type=3).filter(Q(status=3) | Q(status=4)))
            previous_att = list(Question.objects.filter(related_class=class_inst).filter(question_type=4).filter(Q(status=3) | Q(status=4)))
            quizzes_part_curr.append(Question.objects.filter(related_class=class_inst).filter(question_type=3).filter(status=2))
            quizzes_part_prev.append(previous_quiz)
            attendance_curr.append(Question.objects.filter(related_class=class_inst).filter(question_type=4).filter(status=2))
            attendance_prev.append(previous_att)
            for quiz in previous_quiz:
                user_response = list(Response.objects.filter(question=quiz,user=self.request.user,active=1).order_by('timestamp'))
                #print(user_response)
                if len(user_response) > 0:
                    try:
                        resp_str = json.loads(user_response[0].resp_str)
                        formatted_response = sorted([i[4:] for i in resp_str[0]])
                        quizzes_part_prev_answer.append(json.dumps(formatted_response))
                    except:
                        quizzes_part_prev_answer.append("")
                else:
                    quizzes_part_prev_answer.append("Missed")
            for att in previous_att:
                user_response = list(Response.objects.filter(question=att,user=self.request.user,active=1).order_by('timestamp'))
                if len(user_response) > 0:
                    attendance_prev_states.append("Attended")
                else:
                    attendance_prev_states.append("Missed")
        taking_attendance.reverse()
        ctx['quizzes_created'] = quizzes
        ctx['quizzes_part_prev'] = quizzes_part_prev
        ctx['quizzes_part_curr'] = quizzes_part_curr
        ctx['attendance_prev'] = attendance_prev
        ctx['attendance_curr'] = attendance_curr
        ctx['taking_attendance'] = taking_attendance
        ctx['quizzes_part_prev_answer'] = quizzes_part_prev_answer
        ctx['attendance_prev_states'] = attendance_prev_states
        #print(taking_attendance)
        return ctx

class GradesView(views.generic.ListView):
    model = Classes
    template_name = 'classes/classes.html'
    def get_queryset(self):
        return Question.objects.all()
    def get_context_data(self, **kwargs):
        ctx = super(GradesView, self).get_context_data(**kwargs)
        # sort the list by date
        classes = Classes.objects.filter(teacher=self.request.user).order_by('-startDate')
        quizzes = []
        quizzes_part_curr = []
        quizzes_part_prev = []
        taking_attendance = []
        classes_part = self.request.user.students.exclude(teacher=None).order_by('-startDate')#self.request.user)
        ctx['classes_created'] = classes
        ctx['classes_participated'] = classes_part
        for class_inst in classes:
            quizzes.append(Question.objects.filter(related_class=class_inst).filter(question_type=3))
        for class_inst in classes_part:
            if class_inst.attendance > 0:
                question = Question.objects.filter(id=class_inst.attendance)[0]
                prevResponseCount = question.response_set.filter(user=self.request.user).count()
                taking_attendance.append(prevResponseCount == 0)
            else:
                taking_attendance.append(False)
            quizzes_part_curr.append(Question.objects.filter(related_class=class_inst).filter(question_type=3).filter(status=2))
            quizzes_part_prev.append(Question.objects.filter(related_class=class_inst).filter(question_type=3).filter(status=4))
        taking_attendance.reverse()
        ctx['quizzes_created'] = quizzes
        ctx['quizzes_part_prev'] = quizzes_part_prev
        ctx['quizzes_part_curr'] = quizzes_part_curr
        ctx['taking_attendance'] = taking_attendance
        print(taking_attendance)
        return ctx

def GradesDownload(request, pk):
    cur_class = get_object_or_404(Classes, pk=pk)

    quizzes = Question.objects.filter(related_class=cur_class).all()
    student_dict = {}
    for quiz in quizzes:
        responses = Response.objects.filter(question=quiz).all()
        students_in_quiz = set()
        for response in responses:
            user = response.user
            if user != None and user.username not in students_in_quiz:
                students_in_quiz.add(user.username)
                if user.username in student_dict.keys():
                    student_dict[user.username] += 1
                else:
                    student_dict[user.username] = 1

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="grades.csv"'

    writer = csv.writer(response)
    writer.writerow(["Username", "Classes attended", "Total", "Percentage attended"])
    for k in student_dict.keys():
        writer.writerow([k, student_dict[k], len(quizzes), student_dict[k] * 100. / len(quizzes)])

    return response